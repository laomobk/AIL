'''garbage collector'''
from .error import AILRuntimeError

class GC:
    def __init__(self, ref_limit :int=8192):
        self.__references_table :list= [None for _ in range(ref_limit)]
        self.__ref_limit = ref_limit

    def __ref_table_init(self):
        try:
            self.__references_table = [None for _ in range]
        except MemoryError:
            pass

    def register_object(self, objref :object) -> AILRuntimeError:
        '''
        注册一个对象，并将其的 reference ++

        return : 0 if no error, RuntimeError otherwise.
        '''
        if len(self.__references_table) + 1 > self.__ref_limit:
            return AILRuntimeError('Too many objects!', 'ObjectLimitError')
        nelf.__references_table.append(objref)

        return 0
