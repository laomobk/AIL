import sys
import os.path


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


def error_msg(line :int, msg :str, filename :str, errcode=1):
    '''
    line : 行号
    msg : 信息
    filename : 文件名
    errcode : 错误码 / 程序返回值
    '''
    sys.stderr.write('\tLine {2}: {3}\nFile: {0} :{2}, error: {1}\n'.format(
        filename, msg, line, get_line_from_line_no(line, filename)))

    sys.exit(errcode)


class AILRuntimeError:
    def __init__(self, msg :str=None, err_type :str=None):
        self.msg :str = msg
        self.err_type :str = err_type

    def __str__(self):
        return '<AIL_RT_ERROR %s : %s>' % (self.err_type, self.msg)


def print_global_error(err :AILRuntimeError, where :str=''):
    msg = err.msg
    t = err.err_type

    if where:
        sys.stderr.write('in \'%s\' :\n' % where)

    sys.stderr.write(('\t' if where else '') + '%s : %s \n' % (t, msg))
    sys.stderr.flush()

    sys.exit(1)


def raise_error_as_python(err :AILRuntimeError):
    msg = err.msg
    t = err.err_type

    raise _AILRuntimeError('%s : %s' % (t, msg))


class _AILRuntimeError(Exception):
    pass
