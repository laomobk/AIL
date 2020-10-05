import sys
import os.path

from . import debugger


ERR_NOT_EXIT = False
THROW_ERROR_TO_PYTHON = False


def get_line_from_line_no(lno: int, fp: str, replace_return=True):
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
    
    try:
        f = open(fp, encoding='UTF-8')

        for ln in f:
            if tlno == lno:
                return ln.replace('\n', '' if replace_return else '\n')
            tlno += 1

        return ''
    except (OSError, UnicodeDecodeError):
        return ''


# @debugger.debug_python_runtime
def error_msg(line: int, msg: str, filename: str, errcode=1):
    """
    line : 行号
    msg : 信息
    filename : 文件名
    errcode : 错误码 / 程序返回值
    """
    source_line = get_line_from_line_no(line, filename)

    if source_line != '':
        err_msg = 'File: \'{0}\', line {2}:\n   {3}\nError: {1}'.format(
            filename, msg, line, source_line)
    else:
        err_msg = 'File: \'{0}\', line {2}\n{1}'.format(
            filename, msg, line)

    if THROW_ERROR_TO_PYTHON:
        raise _AILRuntimeError(err_msg)
    else:
        sys.stderr.write(err_msg)
        sys.stderr.flush()

    if not ERR_NOT_EXIT:
        sys.exit(errcode)


def print_stack_trace():
    from .astate import MAIN_INTERPRETER_STATE as state

    for f in state.frame_stack[1:][::-1]:
        cp = f.lineno
        n = f.code.name
        filename = f.code.filename

        print('File \'%s \', line %s, in %s' % (filename, cp, n))


class AILRuntimeError:
    def __init__(self, msg: str = None, err_type: str = None, 
                 frame=None, stack_trace=None):
        self.msg: str = msg
        self.err_type: str = err_type
        self.frame = frame

    def __str__(self):
        return '<AIL_RT_ERROR %s : %s>' % (self.err_type, self.msg)


def print_global_error(err: AILRuntimeError, filename: str, 
                       lineno: int):
    if THROW_ERROR_TO_PYTHON:
        raise_error_as_python(err, where)

    source_line = get_line_from_line_no(lineno, filename)

    msg = err.msg
    t = err.err_type
    where = err.frame.code.namee

    info = '  File \'%s\', line %s, in %s' % (filename, lineno, where)

    sys.stderr.write(info)

    if source_line != '':
        sys.stderr.write('    %s\n' % source_line)

    sys.stderr.write('%s: %s' % (t, msg))
    sys.stderr.flush()

    if not ERR_NOT_EXIT:
        sys.exit(1)


def format_error(error: AILRuntimeError):
    msg = error.err_type
    f = error.frame
    t = error.err_type
    lno = f.lineno

    source_line = get_line_from_line_no(lno, f.code.name)
    line_detail = ''

    if source_line != '':
        line_detail = '    %s\n' % source_line

    return 'File: \'%s\', line %s :\n%s%s : %s' % \
           (f.code.name, p, line_detail, t, msg)


def raise_error_as_python(err: AILRuntimeError, where: str = ''):
    msg = err.msg
    t = err.err_type

    w = ''

    if where:
        w = 'in \'%s\' :\n\t' % where

    raise _AILRuntimeError('%s%s : %s' % (w, t, msg))


class _AILRuntimeError(Exception):
    pass
