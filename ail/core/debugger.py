import sys

from . import aconfig


def debug_python_runtime(func):
    def wrapper(*args, **kw):
        f = sys._getframe().f_back.f_back
    
        print('frame : %s' % f)
        print('lno : %s' % f.f_lineno)

        rtn = func(*args, **kw)

        return rtn
    return wrapper

