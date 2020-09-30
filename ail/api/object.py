"""
AIL Python API -- object

The collection of AIL Objs API.
You can almost do anything through these API.
But please use them normatively.

AIL is fragile.
"""

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
    convert_to_pyobj as _convert_to_pyobj,
)

from ..objects.type import TYPE_TYPE
from ..objects.wrapper import WRAPPER_TYPE

from ..core.aobjects import (
    convert_to_ail_object as _convert_to_ail_object,
    unpack_ailobj,
    AILObject,
    AILObjectType
)

__all__ = [
    'ARRAY_TYPE', 'BOOL_TYPE', 'FLOAT_TYPE', 'FUNCTION_TYPE',
    'INTEGER_TYPE', 'STRING_TYPE', 'STRUCT_TYPE', 'WRAPPER_TYPE',
    'null', 'convert_to_ail_object', 'unpack_ailobj', 'get_type'
    'AILObject', 'AILObjectType',
]


def convert_to_ail_object(pyobj: object) -> AILObject:
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


    >>> from ail.api.object import convert_to_ail_object
    >>>
    >>> aint = convert_to_ail_object(726)
    >>> aint
    < 726 >
    >>>
    >>> aint['__class__']
    <AIL Type '<AIL integer type>'>

    >>> aarray = convert_to_ail_object(['Nezha', 'Aobing'])
    >>>
    >>> aarray
    {'Nezha', 'Aobing'}
    >>> aarray['__class__']
    <AIL Type '<AIL array type>'>

    :param pyobj: python object.
    :return: AIL object
    """
    return _convert_to_ail_object(pyobj)


def get_type(ailobj: AILObject) -> AILObjectType:
    """
    Get the AILObjectType object from an AIL object

    >>> from ail.api.object import get_type, convert_to_ail_object
    >>>
    >>> get_type(convert_to_ail_object(726))
    <AIL Type '<AIL integer type>'>

    :param ailobj: an AIL object WHICH HAS TYPE
    :return: the AILObjectType object of that  AIL object
    """
    return ailobj['__class__'] if isinstance(ailobj, AILObject) else None
