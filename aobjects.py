import objects.ailobject as aobj

class AILConstant:
    __slots__ = ['const', 'type_']

    def __init__(self, const, type_ :int):
        self.const = const
        self.type_ = type_


class NullType:
    def __str__(self):
        return 'null'
    __repr__ = __str__

null = NullType()

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


class AILObject:
    '''Base object, do noting...'''
    def __init__(self, **kwargs):
        self.properties = kwargs
        self.reference = 0

    def __getitem__(self, key :str):
        return self.properties[key]   \
            if key in self.properties   \
            else None

    def __setitem__(self, key :str, value):
        self.properties[key] = value


class AILObjectType:
    '''Object Type'''
    def __init__(self, tname :str, **required):
        self.name = tname
        self.required = required

    def __str__(self):
        return '<AIL Type \'%s\'>' % self.name


class ObjectCreater:
    __required_normal = {
        '__str__' : aobj.obj_func_str,
        '__init__' : aobj.obj_func_init,
    }

    @staticmethod
    def new_object(obj_type :AILObjectType, *args):
        obj = AILObject()  # create an object
        obj.properties = obj_type.required
        obj_type['__class__'] = obj_type

        #check normal required

        missing_req = [x for x in ObjectCreater.__required_normal.keys() if x not in obj_type.required.keys()]

        for mis in missing_req:
            obj.properties[mis] = ObjectCreater.__required_normal[mis]

        obj.reference += 1

        return obj


def compare_type(a :AILObject, b :AILObject) -> bool:
    return a['__class__'] == b['__class__']
