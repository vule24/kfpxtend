import copy
import requests
import kfp
import kfp.components._components as comp
from kfp.components._structures import ComponentReference
from pathlib import Path
from typing import Callable, Iterable


def load_component_from_gcs(uri):
    from google.cloud import storage
    uri = uri[len('gs://'):].split('/')
    client = storage.Client()
    blob = client.bucket(uri[0]).blob('/'.join(uri[1:]))
    return blob.download_as_string()


class CloudComponentStore(kfp.components.ComponentStore):
    def __init__(self, url_search_prefixes:list=None):
        super().__init__(url_search_prefixes=url_search_prefixes)
    
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

        #Trying local search paths
        for local_search_path in self.local_search_paths:
            component_path = Path(local_search_path, path_suffix)
            tried_locations.append(str(component_path))
            if component_path.is_file():
                # TODO: Verify that the content matches the digest (if specified).
                component_ref._local_path = str(component_path)
                component_ref.spec = comp._load_component_spec_from_file(str(component_path))
                return component_ref

        #Trying URL prefixes
        for url_search_prefix in self.url_search_prefixes:
            url = url_search_prefix + path_suffix
            tried_locations.append(url)
            if url.startswith('gs://'):
                component_content = _load_component_from_gcs(url)
                component_ref.url = url
                component_ref.spec = comp._load_component_spec_from_yaml_or_zip_bytes(component_content)
                return component_ref
            try:
                response = requests.get(url, auth=self._auth) #Does not throw exceptions on bad status, but throws on dead domains and malformed URLs. Should we log those cases?
                response.raise_for_status()
            except:
                continue
            if response.content:
                # TODO: Verify that the content matches the digest (if specified).
                component_ref.url = url
                component_ref.spec = comp._load_component_spec_from_yaml_or_zip_bytes(response.content)
                return component_ref

        raise RuntimeError('Component {} was not found. Tried the following locations:\n{}'.format(name, '\n'.join(tried_locations)))
        
    def list(self):
        from google.cloud import storage
        client = storage.Client()
        for url_search_prefix in self.url_search_prefixes:
            uri = url_search_prefix[len('gs://'):].split('/')
            bucket = client.bucket(uri[0])
            store_blob = '/'.join(uri[1:])
            blobs = client.list_blobs(bucket_or_name=uri[0], prefix = '/'.join(uri[1:]), delimiter = None)

            for blob in blobs:
                if store_blob in blob.name and blob.name.endswith('component.yaml'):
                    yield 'gs://' + '/'.join([uri[0], blob.name]), blob.name[len(store_blob):-len('/component.yaml')]
    
    def search(self, name:str):
        for blob, component_name in self.list():
            if name.casefold() in blob.casefold():
                print(f"name: {component_name}  uri: {blob}")


