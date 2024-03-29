import sys
import os.path

from . import debugger


ERR_NOT_EXIT = False
THROW_ERROR_TO_PYTHON = True


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
def error_msg(
        line: int, msg: str, filename: str, errcode=1, source: str = None,
        offset: int = -1):
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
        s = SyntaxError()
        s.filename = filename
        s.lineno = line
        s.text = source_line
        s.msg = msg
        s.offset = offset + 1
        s.ail_syntax_error = True
        raise s
    else:
        sys.stderr.write(err_msg)
        sys.stderr.flush()

    if not ERR_NOT_EXIT:
        sys.exit(errcode)


def is_ail_syntax_error(err):
    return isinstance(err, SyntaxError) and hasattr(err, 'ail_syntax_error')


class BuiltinAILRuntimeError(Exception):
    pass


class AILSyntaxError(BuiltinAILRuntimeError):
    def __init__(self, msg, raw_msg, filename: str, line: int):
        super().__init__(raw_msg)
        self.msg = msg
        self.raw_msg = raw_msg
        self.filename = filename
        self.line = line


class AILVersionError(Exception):
    pass

