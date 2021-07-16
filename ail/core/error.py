import sys
import os.path

from .shared import GLOBAL_SHARED_DATA
from . import debugger


ERR_NOT_EXIT = False
THROW_ERROR_TO_PYTHON = False


def get_line_from_file(lno: int, fp: str, strip=True):
    """
    ln : 行号
    fp : 文件路径
    根据行号得到在源码的行
    """
    if lno <= 0:
        return ''

    tlno = 1

    if not os.path.exists(fp):
        return ''

    last_line = ''
    
    try:
        f = open(fp, encoding='UTF-8')

        for ln in f:
            if tlno == lno:
                if strip:
                    return ln.strip()
                return ln
            tlno += 1
            if ln:
                last_line = ln

        if strip:
            return last_line.strip()
        return last_line
    except (OSError, UnicodeDecodeError):
        return ''


def get_line_from_source(lno: int, source: str, strip=True):
    """
    ln : 行号
    fp : 文件路径
    根据行号得到在源码的行
    """
    if lno <= 0:
        return ''

    tlno = 1
    last_line = ''

    try:
        for ln in source.split('\n'):
            if ln:
                last_line = ln
            if tlno == lno:
                if strip:
                    return last_line.strip()
                return last_line
            tlno += 1
        
        if strip:
            return last_line.strip()
        return last_line
    except (OSError, UnicodeDecodeError):
        return ''


# @debugger.debug_python_runtime
def error_msg(line: int, msg: str, filename: str, errcode=1, source: str = None):
    """
    line : 行号
    msg : 信息
    filename : 文件名
    errcode : 错误码 / 程序返回值
    """
    if source is None:
        source_line = get_line_from_file(line, filename)
    else:
        source_line = get_line_from_source(line, source)

    if source_line != '':
        err_msg = '  File \'{0}\', line {2}:\n   {3}\n{1}\n'.format(
            filename, msg, line, source_line)
    else:
        err_msg = '  File \'{0}\', line {2}\n{1}\n'.format(
            filename, msg, line)

    if THROW_ERROR_TO_PYTHON:
        raise BuiltinAILRuntimeError(err_msg)
    else:
        sys.stderr.write(err_msg)
        sys.stderr.flush()

    if not ERR_NOT_EXIT:
        sys.exit(errcode)


def print_stack_trace(stack_trace, print_last=False):
    stack = stack_trace.frame_stack[:-1]

    if print_last:
        stack = stack_trace.frame_stack

    boot_dir = GLOBAL_SHARED_DATA.boot_dir

    for f in stack:
        lineno = f.lineno
        n = f.code.name
        filename = f.code.filename

        line_info = ''
        source_line = get_line_from_file(
                lineno, os.path.join(boot_dir, filename))

        if source_line != '':
            line_info = '\n    %s' % source_line

        print('  File \'%s\', line %s, in %s%s' % (filename, lineno, n, line_info))


class AILRuntimeError:
    def __init__(self, msg: str, err_type: str,
                 frame=None, stack_trace=None):
        self.msg: str = msg
        self.err_type: str = err_type
        self.frame = frame
        self.stack_trace = stack_trace

    def __str__(self):
        return '<AIL_RT_ERROR %s : %s>' % (self.err_type, self.msg)


def print_global_error(err: AILRuntimeError, filename: str, 
                       lineno: int):
    if THROW_ERROR_TO_PYTHON:
        raise_error_as_python(err)

    source_line = get_line_from_file(lineno, filename)

    msg = err.msg
    t = err.err_type
    where = err.frame.code.namee

    info = '  File \'%s\', line %s, in %s' % (filename, lineno, where)

    sys.stderr.write(info)

    if source_line != '':
        sys.stderr.write('    %s' % source_line)

    sys.stderr.write('%s: %s' % (t, msg))
    sys.stderr.flush()

    if not ERR_NOT_EXIT:
        sys.exit(1)


def print_exception_for_vm(handling_err_stack: list, err_struct):
    from ail.modules._error import _err_to_string
    for err in handling_err_stack:
        sys.stderr.write('Traceback (most recent call last):\n')
        print_stack_trace(err.error_object.stack_trace)
        sys.stderr.write(_err_to_string(err) + '\n')
        sys.stderr.write('\n%s\n' %
                         ('During handling of the above exception, ' +
                          'another exception occurred:\n'))

    sys.stderr.write('Traceback (most recent call last):\n')
    print_stack_trace(err_struct.error_object.stack_trace)
    sys.stderr.write(_err_to_string(err_struct) + '\n')


def raise_error_as_python(err: AILRuntimeError, where: str = ''):
    msg = err.msg
    t = err.err_type

    w = ''

    if where:
        w = 'in \'%s\' :\n\t' % where

    raise BuiltinAILRuntimeError('%s%s : %s' % (w, t, msg))


class BuiltinAILRuntimeError(Exception):
    pass


class AILVersionError(Exception):
    pass

