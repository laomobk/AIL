import pickle

from types import CodeType
from typing import List, Set

from . import aobjects as obj

from .aconfig import BYTE_CODE_SIZE

from ..objects import (
    string  as astr,
    integer as aint,
    bool    as abool,
    wrapper as awrapper,
    float   as afloat,
    array,
)

from ..objects.null import null


class LineNumberTableGenerator:
    def __init__(self):
        self.__lnotab: List[int] = []

        self.__last_line = 0
        self.__last_ofs = 0

        self.__sum_line = 0
        self.__sum_ofs = 0

        self.firstlineno = 1

    @property
    def table(self) -> list:
        return self.__lnotab

    def __update_lnotab(self):
        self.__lnotab += [self.__sum_ofs, self.__sum_line]
        self.__sum_ofs = self.__sum_line = 0  # reset.

    def init_table(self):
        self.__lnotab += [0, self.firstlineno]

    def check(self, lno: int):
        if self.__last_line != lno:
            self.__last_line = lno
            self.__update_lnotab()
            return

        self.__sum_line = lno - self.__last_line
        self.__sum_ofs += BYTE_CODE_SIZE

    def mark(self, lno: int, offset: int):
        self.__last_line = lno
        self.__last_ofs = offset

    def update(self, lno: int, offset: int):
        self.__sum_line = lno - self.__last_line
        self.__sum_ofs = offset - self.__last_ofs

        self.__update_lnotab()


class ByteCode:
    """表示字节码序列"""

    def __init__(self, blist=None):
        self.blist = blist if blist is not None else list()
        self.lineno_list = list()

    def to_bytes(self) -> bytes:
        return bytes(self.blist)

    def add_bytecode(self, opcode: int, argv: int, lineno: int):
        self.blist += [opcode, argv]
        self.lineno_list.append(lineno)

    def __add__(self, b: 'ByteCode'):
        bc = ByteCode(self.blist + b.blist)
        bc.lineno_list = self.lineno_list + b.lineno_list

    def __iadd__(self, b: 'ByteCode'):
        self.blist += b.blist
        self.lineno_list.extend(b.lineno_list)
        return self

    # @debugger.debug_python_runtime
    def __setattr__(self, n, v):
        # print('attr set %s = %s' % (n, v))
        super().__setattr__(n, v)


class ByteCodeFileBuffer:
    """
    用于存储即将存为字节码的数据
    """

    def __init__(self):
        self.bytecodes: ByteCode = None
        self.consts = []
        self.varnames: List[str] = []
        self.lnotab: LineNumberTableGenerator = None
        self.argcount = 0
        self.name = '<DEFAULT>'
        self.first_lineno = 0
        self.lineno_list: List[int] = []
        self.filename = '<FILE>'
        self.global_names: Set[str] = set()
        self.nonlocal_names: Set[str] = set()

    def serialize(self) -> bytes:
        """
        将这个Buffer里的数据转换为字节码
        """
        pass

    def add_const(self, const) -> int:
        """
        若const not in self.consts:
            将const加入到self.consts中
        :return: const 在 self.consts 中的index
        """
        # convert const to ail object
        target = {
            str: astr.STRING_TYPE,
            int: aint.INTEGER_TYPE,
            float: afloat.FLOAT_TYPE,
            bool: abool.BOOL_TYPE,
            list: array.ARRAY_TYPE,
        }.get(type(const), awrapper.WRAPPER_TYPE)

        allowed_type = (obj.AILCodeObject,)

        if const != null:
            if target == awrapper.WRAPPER_TYPE and type(const) in allowed_type:
                ac = const
            else:
                ac = obj.ObjectCreater.new_object(target, const)
        else:
            ac = null

        if ac not in self.consts:
            self.consts.append(ac)

        return self.consts.index(ac)

    def get_varname_index(self, name: str):
        return self.varnames.index(name) \
            if name in self.varnames \
            else None

    def get_or_add_varname_index(self, name: str):
        """
        若 name 不存在 varname，则先加入到varname再返回
        :return: index of name in self.varnames
        """

        if name not in self.varnames:
            self.varnames.append(name)
        return self.varnames.index(name)

    @property
    def code_object(self) -> obj.AILCodeObject:
        return obj.AILCodeObject(self.consts, self.varnames, self.bytecodes.blist,
                                 self.lnotab.firstlineno, self.filename, self.argcount,
                                 self.name, self.lnotab.table, tuple(self.lineno_list),
                                 global_names=tuple(self.global_names),
                                 nonlocal_names=tuple(self.nonlocal_names))

    def dump_obj(self):
        """
        dump code object with pickle.
        """
        import re
        fnc = re.compile(r'<|>')
        fn = fnc.sub('_', 'ail.%s.compiled.ailc' % self.name)
        pickle.dump(self.code_object, open(fn, 'wb'))
