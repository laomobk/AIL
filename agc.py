'''garbage collector'''

class GC:
    def __init__(self, ref_limit :int=8192):
        self.__references_table :list= [None for _ in range(ref_limit)]
        self.__ref_limit = ref_limit

    def __ref_table_init(self):
        try:
            self.__references_table = [None for _ in range]
        except MemoryError:
            pass

    def reg_object(self, objref :object):
        pass