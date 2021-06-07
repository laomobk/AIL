# map module
# 2020 / 7 / 7

from ail.core.aobjects import convert_to_ail_object, unpack_ailobj
from ail.objects.struct import convert_to_pyobj, new_struct_object
from ail.objects.null import null
from ail.core.error import AILRuntimeError


_KEY_NOT_EXISTS = object()


def _map_put(this, k, v):
    this = convert_to_pyobj(this)

    m = this.__this___base_map

    k_val = unpack_ailobj(k)

    try:
        m[k_val] = v
    except TypeError:
        return AILRuntimeError(str(k['__class__']), 'UnhashableError')


def _map_get(this, k, default=None):
    this = convert_to_pyobj(this)

    k_val = unpack_ailobj(k)
    try:
        v = this.__this___base_map.get(k_val, default)
    except TypeError:
        return AILRuntimeError(str(k['__class__']), 'UnhashableError')

    return v


def _new_map():
    new_dict = map_obj_dict.copy()
    new_dict['__base_map'] = dict()

    return new_struct_object(
            'hash_map', null, new_dict, map_obj_dict.keys())


map_obj_dict = {
        '__base_map': None,
        'get': convert_to_ail_object(_map_get),
        'put': convert_to_ail_object(_map_put),
}


_IS_AIL_MODULE_ = True

_AIL_NAMESPACE_ = {
        'map': _new_map
}
