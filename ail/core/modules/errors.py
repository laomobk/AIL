from ail.core.err_types import *
from ail.api.object import object_convert_to_ail_object as convert_to_ail_object


_IS_AIL_MODULE_ = True

_AIL_NAMESPACE_ = {
    ATTRIBUTE_ERROR: convert_to_ail_object(ATTRIBUTE_ERROR),
    PYTHON_ERROR: convert_to_ail_object(PYTHON_ERROR),
    TYPE_ERROR: convert_to_ail_object(TYPE_ERROR),
    UNHASHABLE_ERROR: convert_to_ail_object(UNHASHABLE_ERROR),
    INDEX_ERROR: convert_to_ail_object(INDEX_ERROR),
    OBJECT_ERROR: convert_to_ail_object(OBJECT_ERROR),
    OS_ERROR: convert_to_ail_object(OS_ERROR),
    LOAD_ERROR: convert_to_ail_object(LOAD_ERROR),
    IMPORT_ERROR: convert_to_ail_object(IMPORT_ERROR),
    RECURSION_ERROR: convert_to_ail_object(RECURSION_ERROR),
    VM_ERROR: convert_to_ail_object(VM_ERROR),
    NAME_ERROR: convert_to_ail_object(NAME_ERROR),
    ZERO_DIVISION_ERROR: convert_to_ail_object(ZERO_DIVISION_ERROR),
    KEY_ERROR: convert_to_ail_object(KEY_ERROR)
}

