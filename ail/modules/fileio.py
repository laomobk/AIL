
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
            if plus:
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

    object_setattr(self, 'readable', convert_to_ail_object(self._file_readable))
    object_setattr(self, 'writeable', convert_to_ail_object(self._file_writeable))
    object_setattr(self, 'created', convert_to_ail_object(self._file_created))
    object_setattr(self, 'appending', convert_to_ail_object(self._file_appending))
    object_setattr(self, 'closed', convert_to_ail_object(False))


def _fileio_readall(self, block_size=1024):
    """
    readAll([blockSize=1024]) -> bytes

    read a readable file from current cursor to EOF.
    """
    fd = self._file_object_fd
    if fd < 0:
        return _ERROR_CLOSED

    if not self._file_readable:
        return AILRuntimeError('file is not readable', 'OSError')

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
    """
    read(n: integer) -> bytes

    read n bytes from a readable file, if reach the EOF or reach EOF while 
    reading, the length of the bytes which it returns will less than n or 
    equals 0.
    """
    fd = self._file_object_fd
    if fd < 0:
        return _ERROR_CLOSED

    if not self._file_readable:
        return AILRuntimeError('file is not readable', 'OSError')
    
    n = unpack_ailobj(n)
    
    if not isinstance(n, int):
        return AILRuntimeError('Invalid arguments', 'OSError')

    if n < 0:
        return _fileio_readall(self)

    b = os.read(fd, n)

    return b


def _fileio_write(self, b):
    """
    write(data: bytes) -> integer

    write data to a writeable file.
    @returns the size of wrote data.
    """
    fd = self._file_object_fd
    if fd < 0:
        return _ERROR_CLOSED

    if not self._file_writeable:
        return AILRuntimeError('file is not writeable', 'OSError')

    b = unpack_ailobj(b)
    if not isinstance(b, bytes):
        return AILRuntimeError('can only write bytes', 'TypeError')

    return os.write(fd, b)


def _fileio_seek(self, pos, whence=os.SEEK_SET):
    """
    seek(pos [, whence=SEEK_SET]) -> integer

    move the cursor of a file.
    
    @param whence:
        SEEK_SET: cursor directly set to pos.
        SEEK_CUR: cursor will go forward 'pos' step from current position.
        SEEK_END: cursor will go forward 'posl' step from EOF, in this case, 
                  the 'pos' can less than 0.
        
    @returns the offset of cursor to the cursor after seek().
    """
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
        return AILRuntimeError(
                'not support negative offset in this whence', 'TypeError')

    return os.lseek(fd, pos, whence)


def _fileio_close(self):
    """
    close()

    close a file.
    """
    fd = self._file_object_fd
    if fd < 0:
        return _ERROR_CLOSED 

    os.close(fd)
    self._file_object_fd = -1
    object_setattr(self, 'closed', convert_to_ail_object(True))


CLASS_FILEIO = new_class(
    '_FileIO', [],
    {
        '__init__': convert_to_ail_object(_fileio___init__),
        'readAll': convert_to_ail_object(_fileio_readall),
        'read': convert_to_ail_object(_fileio_read),
        'write': convert_to_ail_object(_fileio_write),
        'seek': convert_to_ail_object(_fileio_seek),
        'close': convert_to_ail_object(_fileio_close),
    }
)


_IS_AIL_MODULE_ = True
_AIL_NAMESPACE_ = {
    'FileIO': CLASS_FILEIO,
    'SEEK_SET': convert_to_ail_object(os.SEEK_SET),
    'SEEK_CUR': convert_to_ail_object(os.SEEK_CUR),
    'SEEK_END': convert_to_ail_object(os.SEEK_END),
}
