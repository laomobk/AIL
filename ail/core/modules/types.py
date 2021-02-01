# builtin type struct wrappers
from functools import wraps

from ail.core.aobjects import (
    convert_to_ail_object, ObjectCreater,
    AILObjectType
)
from ail.objects import integer, struct


_SPECIAL_METHODS = [
    '__add__',
    '__div__',
    '__muit__',
    '__sub__',
    '__eq__',
    '__mod__',
    '__pow__',
    '__lshift__',
    '__rshift__',
    '__and__',
    '__or__',
    '__xor__',
    '__inc__',
    '__dec__',
]


def _get_special_methods(_type: AILObjectType, wrapper=None, convert=True):
    methods = dict()

    for m in _SPECIAL_METHODS:
        if m in _type.required:
            _req = _type.required[m]
            if wrapper is not None:
                _req = wrapper(_req)
            if convert:
                _req = convert_to_ail_object(_req)
            methods[m] = _req

    return methods


# integer type


def _integer_wrapper(func):
    @wraps(func)
    def integer_method_wrapper(self, *args):
        val = self.members['__value']
        return func(val, *args)
    return integer_method_wrapper


def _integer_init(self, value):
    real_int = ObjectCreater.new_object(integer.INTEGER_TYPE, value)
    self.members['__value'] = real_int


_INTEGER_STRUCT_MEMBER = ['__value']
_INTEGER_STRUCT_METHOD = {n: convert_to_ail_object(_integer_wrapper(m))
                          for n, m in integer.INTEGER_TYPE.methods.items()}
_INTEGER_STRUCT_METHOD.update(_get_special_methods(integer.INTEGER_TYPE, _integer_wrapper))
_INTEGER_STRUCT_METHOD['__init__'] = convert_to_ail_object(_integer_init)


def get_integer_struct():
    i = struct.new_struct(
        'Integer', _INTEGER_STRUCT_MEMBER, _INTEGER_STRUCT_MEMBER, _INTEGER_STRUCT_METHOD)
    return i


_IS_AIL_MODULE_ = True
_AIL_NAMESPACE_ = {
    'Integer': get_integer_struct(),
    'str_t': convert_to_ail_object(0x0),
    'int_t': convert_to_ail_object(0x1),
    'float_t': convert_to_ail_object(0x2),
    'bool_t': convert_to_ail_object(0x3),
    'wrapper_t': convert_to_ail_object(0x4),
    'func_t': convert_to_ail_object(0x5),
    'pyfunc_t': convert_to_ail_object(0x6),
    'type_t': convert_to_ail_object(0x7),
    'null_t': convert_to_ail_object(0x8),
    'array_t': convert_to_ail_object(0x9),
    'struct_t': convert_to_ail_object(0xa),
    'struct_obj_t': convert_to_ail_object(0xb),
}

