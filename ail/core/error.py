import sys
import os.path
from . import debugger


ERR_NOT_EXIT = False
THROW_ERROR_TO_PYTHON = False


def get_line_from_line_no(lno :int, fp :str):
    '''
    ln : 行号
    fp : 文件路径
    根据行号得到在源码的行
    '''
    if lno <= 0:
        return '<Illegal line number>'
    
    tlno = 1

    if not os.path.exists(fp):
        return '<NULL>'

    f = open(fp, encoding='UTF-8')

    for ln in f:
        if tlno == lno:
            return ln
        tlno += 1
    
    return '<NULL>'


# @debugger.debug_python_runtime
def error_msg(line :int, msg :str, filename :str, errcode=1):
    '''
    line : 行号
    msg : 信息
    filename : 文件名
    errcode : 错误码 / 程序返回值
    '''
    emsg = '\tLine {2}: {3}\nFile: {0} :{2}, error: {1}\n'.format(
        filename, msg, line, get_line_from_line_no(line, filename))

    if THROW_ERROR_TO_PYTHON:
        raise _AILRuntimeError('\n' + emsg)
    else:
        sys.stderr.write(emsg)
        sys.stderr.flush()

    if not ERR_NOT_EXIT:
        sys.exit(errcode)


def print_stack_trace():
    from .astate import MAIN_INTERPRETER_STATE as state

    for f in state.frame_stack[1:][::-1]:
        cp = f._latest_call_opcounter
        n = f.code.name

        print('in \'%s \' +%s' % (n, cp))


class AILRuntimeError:
    def __init__(self, msg :str=None, err_type :str=None, frame=None, stack_trace=None):
        self.msg :str = msg
        self.err_type :str = err_type
        self.frame = frame

    def __str__(self):
        return '<AIL_RT_ERROR %s : %s>' % (self.err_type, self.msg)


def print_global_error(err :AILRuntimeError, where :str=''):
    if THROW_ERROR_TO_PYTHON:
        raise_error_as_python(err, where)

    if isinstance(where, list):
        for w in where[:-1]:
            sys.stderr.write('in \'%s\' :\n' % w)
            sys.stderr.flush()

        where = where[-1]

    msg = err.msg
    t = err.err_type

    if where:
        sys.stderr.write('in \'%s\' :\n' % where)

    sys.stderr.write(('\t' if where else '') + '%s : %s \n' % (t, msg))
    sys.stderr.flush()

    if not ERR_NOT_EXIT:
        sys.exit(1)


def format_error(error :AILRuntimeError):
    msg = error.err_type
    f = error.frame
    t = error.err_type
    p = f._marked_opcounter

    return 'in \'%s\' +%s :\n\t%s : %s' % \
           (f.code.name, p, t, msg)


def raise_error_as_python(err :AILRuntimeError, where :str=''):
    msg = err.msg
    t = err.err_type

    w = ''

    if where:
        w = 'in \'%s\' :\n\t' % where

    raise _AILRuntimeError('%s%s : %s' % (w, t, msg))


class _AILRuntimeError(Exception):
    pass
