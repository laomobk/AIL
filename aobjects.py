
class AILConstant:
    __slots__ = ['const', 'type_']

    def __init__(self, const, type_ :int):
        self.const = const
        self.type_ = type_


class NullType:
    def __str__(self):
        return 'null'
    __repr__ = __str__


class AILCodeObject:
    __slots__ = ['consts', 'varnames', 'bytecodes', 'firstlineno', 
                 'argcount', 'name', 'lnotab']

    def __init__(self, consts :list, varnames :list, 
                 bytecodes :bytes, firstlineno :int,
                 argcount :int, name :str, lnotab :list):
        self.consts = consts
        self.varnames = varnames
        self.bytecodes = bytecodes
        self.firstlineno = firstlineno
        self.argcount = argcount  # if function or -1
        self.name = name
        self.lnotab = lnotab

    def __str__(self):
        return '<AIL CodeObject \'%s\'>' % self.name

    __repr__ = __str__


class AILBaseObject:
    '''Base object, do noting...'''
    def __init__(self, **kwargs):
        self.properties = kwargs


class ObjectCreater:
    @staticmethod
    def new_object():
        pass


null = NullType()
