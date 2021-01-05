import requests
import subprocess as sub

class CloudBearerAuth(requests.auth.AuthBase):
    def __init__(self):
        process = sub.Popen(['gcloud', 'auth', 'print-identity-token'], stdout=sub.PIPE)
        token = process.communicate()[0].decode(encoding='utf-8')
        self.token = token.strip()
    
    def __call__(self, r):
        r.headers["authorization"] = "Bearer " + self.token
        return r
