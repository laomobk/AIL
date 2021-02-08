
import os

from ail.core.aobjects import convert_to_ail_object, unpack_ailobj
from ail.core.error import AILRuntimeError

from ail.objects.class_object import (
    new_class, new_object,
    object_getattr_with_default,
    object_setattr,
)


_ERROR_CLOSED = AILRuntimeError('file closed', 'OSError')
_ERROR_MODE_AGAIN = AILRuntimeError('Must have exactly one of create/read/write/append'
                                    'mode and at most one plus', 'ValueError')


def _mode_to_flag(self, mode_str: str) -> int:
    flags = 0

    rwa = False
    plus = False

    for s in mode_str:
        if s == 'x':
            if rwa:
                return _ERROR_MODE_AGAIN
            rwa = True
            self._file_created = True
            self._file_writeable = True
            flags |= os.O_EXCL | os.O_CREAT
        elif s == 'r':
            if rwa:
                return _ERROR_MODE_AGAIN
            rwa = True
            self._file_readable = True
        elif s == 'w':
            if rwa:
                return _ERROR_MODE_AGAIN
            rwa = True
            self._file_writeable = True
            flags |= os.O_TRUNC | os.O_CREAT
        elif s == 'a':
            if rwa:
                return _ERROR_MODE_AGAIN
            rwa = True
            self._file_readable = True
            self._file_appending = True
            flags |= os.O_CREAT | os.O_APPEND
        elif s == '+':
            if rwa:
                return _ERROR_MODE_AGAIN
            rwa = True
            self._file_readable = True
            self._file_writeable = True
            plus = 1
        elif s == 'b':
            pass
        else:
            return AILRuntimeError('invaild mode %s' % mode_str, 'ValueError')

    if not rwa:
        return _ERROR_MODE_AGAIN

    if self._file_readable and self._file_writeable:
        flags |= os.O_RDWR
    elif self._file_readable:
        flags |= os.O_RDONLY
    else:
        flags |= os.O_WRONLY

    return flags


def _fileio___init__(self, file_path, mode, buf_size=1024):
    path = unpack_ailobj(file_path)
    if not isinstance(path, str):
        return AILRuntimeError('\'path\' must be string', 'TypeError')

    if not os.access(path, 0):
        return AILRuntimeError(
            'No such file or directory: \'%s\'' % path, 'FileNotFoundError')

    mode_str = unpack_ailobj(mode)
    if not isinstance(mode_str, str):
        return AILRuntimeError('\'mode\' must be string', 'TypeError')

    bufsize = unpack_ailobj(buf_size)
    if not isinstance(buf_size, int):
        return AILRuntimeError('\'bufferSize\' must be integer', 'TypeError')

    object_setattr(self, 'path', file_path)
    object_setattr(self, 'mode', mode)
    object_setattr(self, 'bufferSize', buf_size)

    self._file_writeable = False
    self._file_created = False
    self._file_appending = False
    self._file_readable = False

    flags = _mode_to_flag(self, mode_str)
    if not isinstance(flags, int):
        assert isinstance(flags, AILRuntimeError)
        return flags

    self._file_flags = flags

    fd = os.open(path, flags, bufsize)
    self._file_object_fd = fd


def _fileio_readall(self, block_size=1024):
    fd = self._file_object_fd
    if fd < 0:
        return _ERROR_CLOSED
    block_size = unpack_ailobj(block_size)
    if not isinstance(block_size, int):
        return AILRuntimeError(
            '\'blockSize\' must be integer', 'TypeError')
    b = os.read(fd, block_size)
    total_b = b
    while b:
        b = os.read(fd, block_size)
        total_b += b

    return total_b


def _fileio_read(self, n):
    fd = self._file_object_fd
    if fd < 0:
        return _ERROR_CLOSED
    
    n = unpack_ailobj(n)
    
    if not isinstance(n, int):
        return AILRuntimeError('Invalid arguments', 'OSError')

    if n < 0:
        return _fileio_readall(self)

    b = os.read(fd, n)

    return b


def _fileio_write(self, b):
    fd = self._file_object_fd
    if fd < 0:
        return _ERROR_CLOSED

    b = unpack_ailobj(b)
    if not isinstance(b, bytes):
        return AILRuntimeError('can only write bytes', 'TypeError')

    return os.write(fd, b)


def _fileio_seek(self, pos, whence=os.SEEK_SET):
    fd = self._file_object_fd
    if fd < 0:
        return _ERROR_CLOSED

    pos = unpack_ailobj(pos)
    if not isinstance(pos, int):
        return AILRuntimeError('\'pos\' must be integer', 'TypeError')

    whence = unpack_ailobj(whence)
    if not isinstance(whence, int):
        return AILRuntimeError('\'whence\' must be integer', 'TypeError')

    if whence > 2 or whence < 0:
        return AILRuntimeError('invalid \'whence\' argument', 'TypeError')

    if pos < 0 and whence != os.SEEK_END:
        return AILRuntimeError('not support negative offset in this whence', 'TypeError')

    return os.lseek(fd, pos, whence)


CLASS_FILEIO = new_class(
    '_FileIO', [],
    {
        '__init__': convert_to_ail_object(_fileio___init__),
        'readAll': convert_to_ail_object(_fileio_readall),
        'read': convert_to_ail_object(_fileio_read),
        'write': convert_to_ail_object(_fileio_write),
        'seek': convert_to_ail_object(_fileio_seek),
    }
)


_IS_AIL_MODULE_ = True
_AIL_NAMESPACE_ = {
    'FileIO': CLASS_FILEIO,
    'SEEK_SET': convert_to_ail_object(os.SEEK_SET),
    'SEEK_CUR': convert_to_ail_object(os.SEEK_CUR),
    'SEEK_END': convert_to_ail_object(os.SEEK_END),
}
