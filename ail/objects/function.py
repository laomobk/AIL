# Function and PyFunction
import inspect
import types as t

from functools import lru_cache

from ..core import aobjects as obj
from ..core.aobjects import AILObject
from ..core.error import AILRuntimeError
from . import wrapper
from . import types


def pyfunc_func_init(self: obj.AILObject, func: t.FunctionType):
    self.properties['__pyfunction__'] = func
    self.properties['__value__'] = func
    self.properties['__name__'] = func.__name__


def pyfunc_func_call(self: obj.AILObject, *args) -> obj.AILObject:
    fobj = self['__pyfunction__']

    try:
        rtn = fobj(*args)
        if rtn is None:
            return obj.null
        return obj.ObjectCreater.new_object(wrapper.WRAPPER_TYPE, rtn)
    except Exception as e:
        return AILRuntimeError(str(e), 'PythonError')


def pyfunc_func_str(self: obj.AILObject):
    return '<AIL Python function wrapper at %s>' % (hex(id(self)))


def func_func_init(self, cobj: t.CodeType, globals: dict, name: str):
    self['__code__'] = cobj
    self['__globals__'] = globals
    self['__name__'] = name


def func_func_str(self: obj.AILObject):
    return '<AIL function \'%s\' at %s>' % (self['__name__'], hex(id(self)))


def call(pyfw: obj.AILObject, *args):
    if inspect.isfunction(pyfw):
        try:
            return pyfw(*args)
        except Exception as e:
            return AILRuntimeError(str(e), 'PythonError')

    if not isinstance(pyfw, obj.AILObject):
        return AILRuntimeError('Cannot call an object that is not AILObject', 'TypeError')

    if pyfw['__class__'] not in (PY_FUNCTION_TYPE, FUNCTION_TYPE):
        return AILRuntimeError('%s is not callable' % pyfw['__class__'], 'TypeError')

    cfunc = pyfw['__pyfunction__']
    cfunc(*args)

    try:
        return cfunc(*args)
    except Exception as e:
        return AILRuntimeError(str(e), 'PythonError')


FUNCTION_TYPE = obj.AILObjectType('<AIL function type>', types.I_FUNC_TYPE,
                                  __init__=func_func_init,
                                  __str__=func_func_str,
                                  __repr__=func_func_str)

PY_FUNCTION_TYPE = obj.AILObjectType('<Python funtion wrapper>', types.I_PYFUNC_TYPE,
                                     __init__=pyfunc_func_init,
                                     __call__=pyfunc_func_call,
                                     __str__=pyfunc_func_str,
                                     __repr__=pyfunc_func_str)


@lru_cache(None)
def convert_to_func_wrapper(pyf):
    import inspect

    if inspect.isfunction(pyf) or inspect.isbuiltin(pyf):
        return obj.ObjectCreater.new_object(
            PY_FUNCTION_TYPE, pyf)

    if not isinstance(pyf, AILObject):
        return pyf

    if obj.compare_type(pyf, PY_FUNCTION_TYPE) or \
            obj.compare_type(pyf, FUNCTION_TYPE):
        return pyf

