"""
AIL Python API -- object

The collection of AIL Objs API.
You can almost do anything through these API.
But please use them normatively.

AIL is fragile.
"""
from typing import Dict, List

from ._exceptions import NoGlobalInterpreterException

from ..objects.array import (
    ARRAY_TYPE,
    convert_to_array as _convert_to_array
)

from ..objects.bool import BOOL_TYPE
from ..objects.float import FLOAT_TYPE

from ..objects.function import (
    FUNCTION_TYPE,
    convert_to_func_wrapper as _convert_to_func_wrapper
)

from ..objects.integer import (
    INTEGER_TYPE,
    convert_to_integer as _convert_to_integer
)

from ..objects.null import null
from ..objects.string import STRING_TYPE

from ..objects.struct import (
    STRUCT_TYPE,
    new_struct_object as _new_struct_object,
    new_struct as _new_struct,
    struct_object_setattr as _struct_object_setattr,
    struct_object_getattr as _struct_object_getattr,
)

from ..objects.wrapper import WRAPPER_TYPE

from ..core.aobjects import (
    convert_to_ail_object as _convert_to_ail_object,
    unpack_ailobj as object_unpack_ailobj,
    AILObject,
    AILObjectType
)

from ..core.astate import (
    MAIN_INTERPRETER_STATE as _MAIN_INTERPRETER_STATE
)

__all__ = [
    'ARRAY_TYPE', 'BOOL_TYPE', 'FLOAT_TYPE', 'FUNCTION_TYPE',
    'INTEGER_TYPE', 'STRING_TYPE', 'STRUCT_TYPE', 'WRAPPER_TYPE',
    'null', 'object_convert_to_ail_object', 'object_unpack_ailobj', 'object_get_type',
    'AILObject', 'AILObjectType',
    'object_call_object',
    'integer_convert_to_interger',
    'struct_new_struct_object', 'struct_object_setattr', 'struct_object_getattr'
]


def object_convert_to_ail_object(pyobj: object) -> AILObject:
    """
    Convert a python object to an AIL object.

    normally, only 'constant' type can be converted to target type AIL object.
    if AIL cannot convert this object, will return `Python Object Wrapper`

    * supporting types:
        int
        float
        str
        bool
        list
        python function  (only python function, not method or built-in function, etc.)


    >>> from ail.api.object import object_convert_to_ail_object
    >>>
    >>> aint = object_convert_to_ail_object(726)
    >>> aint
    < 726 >
    >>>
    >>> aint['__class__']
    <AIL Type '<AIL integer type>'>

    >>> aarray = object_convert_to_ail_object(['Nezha', 'Aobing'])
    >>>
    >>> aarray
    {'Nezha', 'Aobing'}
    >>> aarray['__class__']
    <AIL Type '<AIL array type>'>

    :param pyobj: python object.
    :return: AIL object
    """
    return _convert_to_ail_object(pyobj)


def object_get_type(ailobj: AILObject) -> AILObjectType:
    """
    Get the AILObjectType object from an AIL object

    >>> from ail.api.object import object_get_type, object_convert_to_ail_object
    >>>
    >>> object_get_type(object_convert_to_ail_object(726))
    <AIL Type '<AIL integer type>'>

    :param ailobj: an AIL object WHICH HAS TYPE
    :return: the AILObjectType object of that  AIL object
    """
    return ailobj['__class__'] if isinstance(ailobj, AILObject) else None


def object_call_object(callable_object: AILObject, *args):
    interpreter = _MAIN_INTERPRETER_STATE.global_interpreter

    if interpreter is None:
        raise NoGlobalInterpreterException()

    if not isinstance(callable_object, AILObject):
        raise TypeError('%s in AIL is not callable.' % type(callable_object))

    interpreter.call_function(callable_object, len(args), args)


def integer_convert_to_interger(py_int: int) -> AILObject:
    return _convert_to_integer(py_int)


def struct_new_struct_object(name: str, struct_type: AILObject,
                             members: Dict[str, AILObject],
                             protected_members: List[str]) -> AILObject:
    if struct_type is None:
        struct_type = null

    return _new_struct_object(name, struct_type, members, protected_members)


def struct_new_struct(name: str,
                      members: List[str], protected_members: List[str]) -> AILObject:
    return _new_struct(name, members, protected_members)


def struct_object_setattr(struct_object: AILObject, name: str, value: AILObject):
    if not isinstance(name, str):
        raise TypeError('attribute name must be a string')

    _struct_object_setattr(struct_object, name, value)


def struct_object_getattr(struct_object: AILObject, name: str) -> AILObject:
    if not isinstance(name, str):
        raise TypeError('attribute name must be a string')

    return _struct_object_getattr(struct_object, name)

