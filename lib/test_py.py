
import requests


def get(url):
    return requests.get(url)

_AIL_NAMESPACE_ = {'get' : get}
