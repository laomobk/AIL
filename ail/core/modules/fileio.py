
import os

from ail.core.aobjects import convert_to_ail_object, unpack_ailobj
from ail.core.error import AILRuntimeError

from ail.objects.class_object import (
    new_class, new_object,
    object_getattr_with_default,
    object_setattr,
)


def _get_and_check_fd(fobj) -> int:
    fd = object_getattr_with_default(fobj, 'fileno')
    if not isinstance(fd, int):
        return None
    return fd


def _file___init__(self, file_path, fileno, encoding):
    object_setattr(self, 'path', file_path)
    object_setattr(self, 'fileno', fileno)
    object_setattr(self, 'encoding', encoding)


def _file_read(self, n=1):
    fd = _get_and_check_fd(self)
    if fd is None:
        return AILRuntimeError('bad file descriptor', 'OSError')
    
    n = unpack_ailobj(n)
    
    if not isinstance(n, int) or n < 0:
        return AILRuntimeError
    os.read(fd, n)

