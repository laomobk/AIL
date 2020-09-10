'''garbage collector'''
import sys

from .error import AILRuntimeError
from . import aobjects as obj
from ..objects import integer


class GC:
    def __init__(self, ref_limit :int=10):
        self.__references_table :list= [None for _ in range(ref_limit)]
        self.__ref_limit = ref_limit

        self.__mark_up_table = []
        self.__out = None

        self.__fp = 0

    def set_output_stream(self, o):
        self.__out = o

    def __sprintln(self, *msg):
        if self.__out:
            for m in msg:
                self.__out.write(str(m))
                self.__out.write(' ')
            self.__out.write('\n')

    def __get_free_space_index(self) -> int:
        '''
        得到指向None的索引，并将 __fp 移动到此处
        :return : free space index, -1 if full
        '''
        if None not in self.__references_table:  # if no free space
            self.__fp = -1
            return self.__fp

        if self.__fp >= len(self.__references_table):  # 若移到引用表尽头
            self.__fp = self.__references_table.index(None)
            return self.__fp

        if self.__references_table[self.__fp] is not None:
            if self.__fp + 1 < len(self.__references_table):
                if self.__references_table[self.__fp + 1] is None:
                    self.__fp += 1  # move fp
                else:
                    self.__fp = self.__references_table.index(None)
        return self.__fp

    def register_object(self, objref :obj.AILObject) -> AILRuntimeError:
        '''
        注册一个对象，并将其的 reference ++

        return : 0 if no error, RuntimeError otherwise.
        '''
        self.__sprintln('reg object %s' % objref)

        if objref.reference < 1:
            objref.reference = 1
        fp = self.__get_free_space_index()
        if fp == -1:
            return AILRuntimeError('Too many objects!', 'ObjectLimitError')
        self.__references_table[fp] = objref
        return 0

    def gc(self) -> obj.AILObject:
        ts = 0
        if self.__scan_and_markup_unreachable():
            ts = self.__clean_up_ref_table()
        else:
            print(self.__mark_up_table)
            print(self.__references_table)
            self.__sprintln('No object marked.')
        return obj.ObjectCreater.new_object(integer.INTEGER_TYPE, ts)

    def __scan_and_markup_unreachable(self) -> bool:
        '''
        :return: 如果有标记对象则返回 True, 否则返回 False.
        '''
        self.__sprintln('scanning unreachable...')

        self.__mark_up_table = []
        table = self.__references_table

        marked = False

        for i, oref in enumerate(table):
            if oref == None:
                self.__mark_up_table.append(i)
                continue

            self.__visit_ref(oref)

            if table.count(oref) == 1 and i not in self.__mark_up_table:
                self.__mark_up_table.append(i)
                marked = True

                self.__sprintln('Alive! marking up %s' % oref)

        return marked

    def __visit_ref(self, ail_obj :obj.AILObject):

        if not isinstance(ail_obj, obj.AILObject):
            return
        self.__sprintln('Checking %s object\'s properties...' % ail_obj)

        prop = ail_obj.properties

        for p in prop.values():
            if p in self.__references_table and self.__references_table.count(p) == 1:
                pi = self.__references_table.index(p)

                if pi not in self.__mark_up_table:
                    self.__mark_up_table.append(pi)
                self.__visit_ref(p)

    def __clean_up_ref_table(self) -> int:
        '''
        :return: 被清理的对象的总大小
        '''
        dsize = 0
        for mi in (x for x in range(len(self.__references_table))   \
                            if x not in self.__mark_up_table):
            di = self.__references_table[mi]

            self.__references_table[mi] = None
            dsize += sys.getsizeof(di)

            self.__sprintln('free %s' % di)

            del di
        return dsize

    def _free(self, objref):
        if objref in self.__references_table:
            # objref.reference = 0
            objref.reference -= 1
            self.__references_table[self.__references_table.index(objref)] = None
