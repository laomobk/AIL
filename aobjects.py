import inspect
import objects.ailobject as aobj
import objects

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

    def __getattr__(self, item :str):
        if item[:5] == 'aprop':
            return self.__getitem__(item[6:])
        return super().__getattribute__(item)

    def __setattr__(self, key :str, value):
        if key[:5] == 'aprop':
            self.__setitem__(key[6:])
        super().__setattr__(key, value)

    def __str__(self):
        try:
            return self['__str__'](self)
        except:
            return '<AIL %s object at %s>' % (self['__class__'].name, hex(id(self)))

    __repr__ = __str__

class AILObjectType:
    '''Object Type'''
    def __init__(self, tname :str, **required):
        self.name = tname
        self.required = required

    def __str__(self):
        return '<AIL Type \'%s\'>' % self.name

    __repr__ = __str__


class ObjectCreater:
    __required_normal = {
        '__str__' : aobj.obj_func_str,
        '__init__' : aobj.obj_func_init,
    }

    @staticmethod
    def new_object(obj_type :AILObjectType, *args) -> AILObject:
        '''
        ATTENTION : 返回的对象的引用为0
        :return : obj_type 创建的对象，并将 *args 作为初始化参数
        '''

        obj = AILObject()  # create an object
        obj.properties['__class__'] = obj_type

        for k, v in obj_type.required.items():
            obj.properties[k] = v

        # check normal required

        missing_req = [x for x in ObjectCreater.__required_normal.keys() if x not in obj_type.required.keys()]

        for mis in missing_req:
            obj.properties[mis] = ObjectCreater.__required_normal[mis]

        # call init method
        init_mthd = obj['__init__']
        init_mthd(obj, *args)

        return obj


def compare_type(a :AILObject, b :AILObject) -> bool:
    return a['__class__'] == b
