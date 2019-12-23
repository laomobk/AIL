from typing import List, TypeVar, Union, Tuple
import asts as ast
from opcodes import *
from error import error_msg
from tokentype import LAP_STRING, LAP_IDENTIFIER, LAP_NUMBER
import aobjects as obj


__author__ = 'LaomoBK'

___doc__ = ''' Compiler for AIL
将语法分析得出的语法树编译为字节码。'''

_BYTE_CODE_SIZE = 2  # each bytecode & arg size = 8 * 2

class ByteCode:
    '''表示字节码序列'''
    def __init__(self, blist :List[int]=[]):
        self.blist = blist

    def to_bytes(self) -> bytes:
        return bytes(self.blist)

    def add_bytecode(self, opcode :int, argv :int):
        self.blist += [opcode, argv]

    def __add__(self, b):
        return ByteCode(self.blist + b.blist)

    def __iadd__(self, b):
        self.blist + b.blist
        return self


class LineNumberTableGenerator:
    def __init__(self):
        self.__lnotab :List[int] = []

        self.__last_line = 0
        self.__last_ofs = 0

        self.__sum_line = 0
        self.__sum_ofs = 0

    @property
    def table(self) -> list:
        return self.__lnotab

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
        self.bytecodes :ByteCode = None
        self.consts  = []
        self.varnames :List[str] = []
        self.lnotab :LineNumberTableGenerator = None

    def serialize(self) -> bytes:
        '''
        将这个Buffer里的数据转换为字节码
        '''
        pass

    def add_const(self, const) -> int:
        '''
        若const not in self.consts: 
            将const加入到self.consts中
        return : const 在 self.consts 中的index
        '''
        if const not in self.consts:
            self.consts.append(const)

        return self.consts.index(const)

    def get_varname_index(self, name :str):
        return self.varnames.index(name)  \
                if name in self.varnames  \
                else None

    def get_or_add_varname_index(self, name :str):
        '''
        若 name 不存在 varname，则先加入到varname再返回
        return : index of name in self.varnames
        '''

        if name not in self.varnames:
            self.varnames.append(name)
        return self.varnames.index(name)


class Compiler:
    def __init__(self, astree :ast.ExprAST):
        self.__ast = astree
        self.__now_ast :ast.ExprAST = astree
        self.__general_bytecode = ByteCode()
        self.__buffer = ByteCodeFileBuffer()

        self.__buffer.bytecodes = self.__general_bytecode
        self.__lnotab = LineNumberTableGenerator()

        self.__buffer.lnotab = self.__lnotab

        self.__flag = 0x0

    def __flag_cmp(self, f :int) -> bool:
        return self.__flag & f

    def __bytecode_update(self, bytecode :ByteCode):
        self.__general_bytecode.blist += bytecode.blist
        self.__lnotab.check()

    def __do_cell_ast(self, cell :ast.CellAST) -> Tuple[int, int]:
        '''
        sign : 
            0 : number or str
            1 : identifier
        return : (sign, index)
        '''
        if cell.type in (LAP_NUMBER, LAP_STRING):
            c = {
                    LAP_NUMBER : lambda n : convert_numeric_str_to_number(n),
                    LAP_STRING : lambda s : s
                }[cell.type](cell.value)

            ci = self.__buffer.add_const(c)
            sign = 0

        elif cell.type == LAP_IDENTIFIER:
            ci = self.__buffer.get_or_add_varname_index(cell.value)
            sign = 1

        return (sign, ci)

    def __get_operator(self, op :str):
        return {
                '+' : binary_add,
                '-' : binary_sub,
                '*' : binary_muit,
                '/' : binary_div,
                'mod' : binary_mod,
                '^' : binary_pow
               }[op]

    def __compile_binary_expr(self, tree :ast.BinaryExprAST) -> ByteCode:
        bc = ByteCode()

        # 先递归处理 left，然后再递归处理right

        if isinstance(tree, ast.CellAST):
            s, i = self.__do_cell_ast(tree)

            bc.add_bytecode(load_const if s == 0 else load_global, i)

            return bc

        elif isinstance(tree, ast.CallExprAST):
            bc += self.__compile_call_expr(tree)

        elif type(tree.left) in ast.BINARY_AST_TYPES:
            bc += self.__compile_binary_expr(tree.left)

        # right

        if not hasattr(tree, 'right'):
            return bc

        for op, rtree in tree.right:
            opc = self.__get_operator(op)
            rbc = self.__compile_binary_expr(rtree)
            bc += rbc

            bc.add_bytecode(opc, 0)

        return bc

    def __compile_define_expr(self, tree :ast.DefineExprAST)  -> ByteCode:
        bc = ByteCode()

        ni = self.__buffer.get_or_add_varname_index(tree.name)
        expc = self.__compile_binary_expr(tree.value)

        bc += expc
        bc.add_bytecode(store_var, ni)

        return bc

    def __compile_call_expr(self, tree :ast.CallExprAST) -> ByteCode:
        bc = ByteCode()

        fni = self.__buffer.get_or_add_varname_index(tree.name)
        bc.add_bytecode(load_global, fni)

        expl = tree.arg_list.exp_list
        
        for et in expl:
            etc = self.__compile_binary_expr(et)
            bc += etc

        bc.add_bytecode(call_func, len(expl))

        return bc


    def __compile_block(self, tree) -> ByteCode:
        if isinstance(tree, ):
            pass


    def test(self, tree) -> ByteCodeFileBuffer:
        bc = self.__compile_define_expr(tree)
        self.__buffer.bytecodes = bc

        return self.__buffer


def convert_numeric_str_to_number(value :str) -> Union[int, float]:
    '''
    将一个或许是数字型字符串转换成数字

    return : eval(value)    若value是数字型字符串
    return : None           若value不是数字型字符串
    '''
    v = eval(value)
    if type(v) in (int, float):
        return v
    return None


def test_compiler():
    import test_utils
    from aparser import Parser
    from alex import Lex

    l = Lex('tests/test.ail')
    ts = l.lex()

    p = Parser(ts, 'tests/test.ail')
    t = p.parse()
    t = t.stmts[0]

    c = Compiler(t)
    bf = c.test(t)

    test_utils.show_bytecode(bf)


if __name__ == '__main__':
    test_compiler()
