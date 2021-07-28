
from . import error


# null = NullType()

class AILCodeObject:
    __slots__ = ('consts', 'varnames', 'bytecodes', 'firstlineno', 'lineno_list',
                 'argcount', 'name', 'lnotab', 'closure', 'is_main', 'filename',
                 '_closure_outer', 'global_names', 'nonlocal_names', 'var_arg',
                 'doc_string', '_function_signature')

    def __init__(self, consts: list, varnames: list,
                 bytecodes: list, firstlineno: int, filename: str,
                 argcount: int, name: str, lnotab: list, lineno_list: tuple,
                 closure: bool = False, is_main: bool = False,
                 global_names: list=None, nonlocal_names: list=None,):
        self.consts = consts
        self.varnames = varnames
        self.bytecodes = tuple(bytecodes)
        self.firstlineno = firstlineno
        self.argcount = argcount  # if function or -1
        self.name = name
        self.filename = filename
        self.lnotab = lnotab
        self.closure = closure
        self.is_main = is_main
        self.lineno_list = lineno_list
        self.global_names = global_names
        self.nonlocal_names = nonlocal_names

        self.var_arg: str = None
        self.doc_string: str = ''

        self._closure_outer: list = list()  # empty if not closure

        self._function_signature = ''

    def __str__(self):
        return '<AIL CodeObject \'%s\'>' % self.name

    __repr__ = __str__


class AILObjectType:
    """Object Type"""

    def __init__(self, 
            tname: str, otype=None, methods: dict = None, **required):
        super().__init__()
        self.name = tname
        self.required = required
        self.methods = methods if methods is not None else dict()

    def __str__(self):
        return '<AIL Type \'%s\'>' % self.name

    __repr__ = __str__


# cache
_STRING_TYPE = None
_INTEGER_TYPE = None
_FLOAT_TYPE = None
_COMPLEX_TYPE = None
_ARRAY_TYPE = None
_MAP_TYPE = None
_WRAPPER_TYPE = None
_PY_FUNCTION_TYPE = None
_BYTES_TYPE = None
_null = None
_not_loaded = True


def convert_to_ail_object(pyobj: object) -> object:
    return pyobj


def get_state():
    global _MAIN_INTERPRETER_STATE
    return _MAIN_INTERPRETER_STATE


_MAIN_INTERPRETER_STATE = None
