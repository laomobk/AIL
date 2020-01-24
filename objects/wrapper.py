# Object wrapper

import aobjects as obj


def wrapper_func_init(self, pyobj :object):
    self['__pyobject__'] = pyobj


WRAPPER_TYPE = obj.AILObjectType('<Python object wrapper>', __init__=wrapper_func_init)
