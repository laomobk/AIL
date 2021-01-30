# Function and PyFunction
import inspect
import types as t

from functools import lru_cache
from inspect import isbuiltin, isfunction

from ..core import aobjects as obj
from ..core.aobjects import AILObject
from ..core.error import AILRuntimeError
from . import wrapper
from . import types


_new_object = None
_compare_type = None
_not_loaded = True


def _make_cache():
    global _not_loaded
    if _not_loaded:
        global _new_object
        global _compare_type
        _new_object = obj.ObjectCreater.new_object
        _compare_type = obj.compare_type
        _not_loaded = False


def pyfunc_func_init(self: obj.AILObject, func: t.FunctionType):
    self.properties['__pyfunction__'] = func
    self.properties['__value__'] = func
    self.properties['__name__'] = func.__name__


def pyfunc_func_call(self: obj.AILObject, *args) -> obj.AILObject:
    _make_cache()

    fobj = self['__pyfunction__']

    try:
        rtn = fobj(*args)
        if rtn is None:
            return obj.null
        return _new_object(wrapper.WRAPPER_TYPE, rtn)
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
    if isfunction(pyfw):
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


FUNCTION_TYPE = obj.AILObjectType('<function type>', types.I_FUNC_TYPE,
                                  __init__=func_func_init,
                                  __str__=func_func_str,
                                  __repr__=func_func_str)

PY_FUNCTION_TYPE = obj.AILObjectType('<python funtion wrapper type>', 
                                     types.I_PYFUNC_TYPE,
                                     __init__=pyfunc_func_init,
                                     __call__=pyfunc_func_call,
                                     __str__=pyfunc_func_str,
                                     __repr__=pyfunc_func_str)


def convert_to_func_wrapper(pyf):
    _make_cache()
    if isfunction(pyf) or isbuiltin(pyf):
        return _new_object(
            PY_FUNCTION_TYPE, pyf)

    if not isinstance(pyf, AILObject):
        return pyf

    if _compare_type(pyf, PY_FUNCTION_TYPE) or \
            _compare_type(pyf, FUNCTION_TYPE):
        return pyf

