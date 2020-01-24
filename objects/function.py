# Function and PyFunction
import aobjects as obj
import types
from error import AILRuntimeError
import objects
import inspect


def pyfunc_func_init(self :obj.AILObject, func :types.FunctionType):
    self['__pyfunction__'] = func


def pyfunc_func_call(self :obj.AILObject, *args) -> obj.AILObject:
    fobj = self['__pyfunction__']

    try:
        rtn = fobj(*args)
        if rtn is None:
            return obj.null
        return obj.ObjectCreater.new_object(objects.wrapper.WRAPPER_TYPE, rtn)
    except Exception as e:
        return AILRuntimeError(str(e), 'PythonError')


def call_function(pyfw :obj.AILObject, *args):
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


FUNCTION_TYPE = obj.AILObjectType('<AIL function type>')
PY_FUNCTION_TYPE = obj.AILObjectType('<Python funtion wrapper>',
                                     __init__=pyfunc_func_init,
                                     __call__=pyfunc_func_call)

