from typing import List, TypeVar, Union
import ast
from opcode import *
from error import error_msg
from tokentype import LAP_STRING, LAP_IDENTIFIER, LAP_NUMBER

__author__ = 'LaomoBK'

___doc__ = ''' Compiler for AIL
将语法分析得出的语法树编译为字节码。'''

consts_t = TypeVar('ConstsType', int, float, str)

_BYTE_CODE_SIZE = 2  # each bytecode & arg size = 8 * 2

class ByteCode:
    '''表示字节码序列'''
    def __init__(self, blist :List[int]=[]):
        self.blist = blist

    def to_bytes(self) -> bytes:
        return bytes(self.blist)

    def __add__(self, b):
        return ByteCode(self.blist + b.blist)


class LineNumberTableGenerator:
    def __init__(self):
        self.__lnotab :List[int] = []

        self.__last_line = 0
        self.__last_ofs = 0

        self.__sum_line = 0
        self.__sum_ofs = 0

    def __update_lnotab(self):
        self.__lnotab += [self.__sum_ofs, self.__sum_line]
        self.__sum_ofs = self.__sum_line = 0  # reset.

    def check(self, lno):
        if self.__last_line != lno:
            self.__last_line = lno
            self.__update_lnotab()
            return

        self.__sum_line = lno - self.__last_line
        self.__sum_ofs += _BYTE_CODE_SIZE


class ByteCodeFileBuffer:
    '''
    用于存储即将存为字节码的数据
    '''
    def __init__(self):
        self.bytes :ByteCode = None
        self.consts :List[consts_t] = []
        self.varnames :List[str] = []
        self.lnotab :LineNumberTableGenerator = None

    def serialize(self) -> bytes:
        '''
        将这个Buffer里的数据转换为字节码
        '''
        pass

    def add_const(self, const :Union[consts_t]) -> int:
        '''
        若const not in self.consts: 
            将const加入到self.consts中
        return : const 在 self.consts 中的index
        '''
        if const not in self.consts:
            self.consts.append(const)

        if const in self.consts:
            return self.consts.index(const)
        return self.consts.index(const)

    def get_varname_index(self, name :str):
        return self.varnames.index(name)  \
                if name in self.varnames  \
                else None

    def add_varname(self, name :str):
        '''
        return : index of name in self.varnames
        '''

        if name not in self.varnames:
            self.varname.append(name)
            return self.varname.index(mame)
        return -1


class Compiler:
    def __init__(self, astree :ast.ExprAST):
        self.__ast = astree
        self.__now_ast :ast.ExprAST = astree
        self.__general_bytecode = ByteCode()
        self.__buffer = ByteCodeFileBuffer()

        self.__buffer.bytes = self.__general_bytecode
        self.__lnotab = LineNumberTableGenerator()

        self.__buffer.lnotab = self.__lnotab

    def __bytecode_update(self, bytecode :ByteCode):
        self.__general_bytecode.blist += bytecode

    def __do_call_ast(self, tree :ast.CallExprAST) -> ByteCode:
        b = ByteCode()

        # load_ast

        for east in tree.arg_list:
            if isinstance(east, ast.CellAST):
                pass

        i = self.__buffer.get_varname_index(tree.name)

    def __parse_bin_expr(self, tree :ast.BinaryExprAST) -> ByteCode:
        pass

    def __do_block(self, tree) -> ByteCode:
        if isinstance(tree, ):
            pass
