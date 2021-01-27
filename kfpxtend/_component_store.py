import copy
import kfp
import kfp.components._components as comp
from kfp.components._structures import ComponentReference

def load_component_from_gcs(uri):
    from google.cloud import storage
    uri = uri[len('gs://'):].split('/')
    client = storage.Client()
    blob = client.bucket(uri[0]).blob('/'.join(uri[1:]))
    return blob.download_as_string()


class GSComponentStore(kfp.components.ComponentStore):
    def __init__(self, local_search_paths=None, url_search_prefixes=None, gs_search_prefixes=None):
        self.gs_search_prefixes = gs_search_prefixes
        super().__init__(local_search_paths=local_search_paths, url_search_prefixes=url_search_prefixes)
    
    def _load_component_spec_in_component_ref(
        self,
        component_ref: ComponentReference,
    ) -> ComponentReference:
        """Takes component_ref, finds the component spec and returns component_ref with .spec set to the component spec.
        See ComponentStore.load_component for the details of the search logic.
        """
        if component_ref.spec:
            return component_ref

        component_ref = copy.copy(component_ref)
        if component_ref.url:
            component_ref.spec = comp._load_component_spec_from_url(url=component_ref.url, auth=self._auth)
            return component_ref

        name = component_ref.name
        if not name:
            raise TypeError("name is required")
        if name.startswith('/') or name.endswith('/'):
            raise ValueError('Component name should not start or end with slash: "{}"'.format(name))

        digest = component_ref.digest
        tag = component_ref.tag

        tried_locations = []

        if digest is not None and tag is not None:
            raise ValueError('Cannot specify both tag and digest')

        if digest is not None:
            path_suffix = name + '/' + self._digests_subpath + '/' + digest
        elif tag is not None:
            path_suffix = name + '/' + self._tags_subpath + '/' + tag
            #TODO: Handle symlinks in GIT URLs
        else:
            path_suffix = name + '/' + self._component_file_name

        #Trying URL prefixes
        for gs_search_prefix in self.gs_search_prefixes:
            uri = gs_search_prefix.rstrip('/') + '/' + path_suffix
            tried_locations.append(uri)
            if uri.startswith('gs://'):
                component_content = load_component_from_gcs(uri)
                component_ref.spec = comp._load_component_spec_from_yaml_or_zip_bytes(component_content)
                return component_ref

        return super()._load_component_spec_in_component_ref(component_ref)
        
    def list(self):
        super().search('')
        from google.cloud import storage
        client = storage.Client()
        gcs_list = []
        for gs_search_prefix in self.gs_search_prefixes:
            uri = gs_search_prefix[len('gs://'):].split('/')
            store_blob = '/'.join(uri[1:])
            blobs = client.list_blobs(bucket_or_name=uri[0], prefix=store_blob, delimiter=None)

            for blob in blobs:
                if store_blob in blob.name and blob.name.endswith('component.yaml'):
                    gcs_list.append(['gs://' + '/'.join([uri[0], blob.name]), blob.name[len(store_blob):-len('/component.yaml')]])
        return gcs_list
    
    def search(self, name:str):
        super().search(name)
        for blob, component_name in self.list():
            if name.casefold() in blob.casefold():
                print(f"name: {component_name}  uri: {blob}")


