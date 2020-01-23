from .error import AILRuntimeError

class PyFunctionWrapper:
    def __init__(self, callable_, argc :int, argv :int):
        self.callable = callable_
        self.argc = argc
        self.argv = argv

    def call(self, *args):
        try:
            rtn = self.callable(*args)
        except Exception as e:
            return AILRuntimeError(str(e), 'PyRuntimeError')
        return rtn
