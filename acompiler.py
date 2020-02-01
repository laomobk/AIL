from typing import List, TypeVar, Union, Tuple
import asts as ast
from opcodes import *
from error import error_msg
from tokentype import LAP_STRING, LAP_IDENTIFIER, LAP_NUMBER
import aobjects as obj
import debugger
import aobjects as objs

import objects.string as astr
import objects.integer as aint
import objects.bool as abool
import objects.wrapper as awrapper
import objects.float as afloat
from objects.null import null

__author__ = 'LaomoBK'

___doc__ = ''' Compiler for AIL
将语法分析得出的语法树编译为字节码。'''

_BYTE_CODE_SIZE = 2  # each bytecode & arg size = 8 * 2

COMPILER_MODE_FUNC = 0x1
COMPILER_MODE_MAIN = 0x2


class ByteCode:
    '''表示字节码序列'''
    def __init__(self):
        self.blist = []

    def to_bytes(self) -> bytes:
        return bytes(self.blist)

    def add_bytecode(self, opcode :int, argv :int):
        self.blist += [opcode, argv]

    def __add__(self, b):
        return ByteCode(self.blist + b.blist)

    def __iadd__(self, b):
        self.blist += b.blist
        return self

    #@debugger.debug_python_runtime
    def __setattr__(self, n, v):
        #print('attr set %s = %s' % (n, v))
        super().__setattr__(n, v)


class LineNumberTableGenerator:
    def __init__(self):
        self.__lnotab :List[int] = []

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

    def check(self, lno :int):
        if self.__last_line != lno:
            self.__last_line = lno
            self.__update_lnotab()
            return

        self.__sum_line = lno - self.__last_line
        self.__sum_ofs += _BYTE_CODE_SIZE

    def mark(self, lno :int, offset :int):
        self.__last_line = lno
        self.__last_ofs = offset

    def update(self, lno :int, offset :int):
        self.__sum_line = lno - self.__last_line
        self.__sum_ofs = offset - self.__last_ofs

        self.__update_lnotab()


class ByteCodeFileBuffer:
    '''
    用于存储即将存为字节码的数据
    '''
    def __init__(self):
        self.bytecodes :ByteCode = None
        self.consts  = []
        self.varnames :List[str] = []
        self.lnotab :LineNumberTableGenerator = None
        self.argcount = 0
        self.name = '<DEFAULT>'

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
        # convert const to ail object
        target = {
                    str : astr.STRING_TYPE,
                    int : aint.INTEGER_TYPE,
                    float : afloat.FLOAT_TYPE,
                    bool : abool.BOOL_TYPE,
                 }.get(type(const), awrapper.WRAPPER_TYPE)

        allowed_type = (objs.AILCodeObject, )

        if const != null:
            if target == awrapper.WRAPPER_TYPE and type(const) in allowed_type:
                ac = const
            else:
                ac = objs.ObjectCreater.new_object(target, const)
        else:
            ac = null

        if ac not in self.consts:
            self.consts.append(ac)

        return self.consts.index(ac)

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

    @property
    def code_object(self) -> obj.AILCodeObject:
        return obj.AILCodeObject(self.consts, self.varnames, self.bytecodes.blist, 
                                 self.lnotab.firstlineno, self.argcount,
                                 self.name, self.lnotab)


class Compiler:
    def __init__(self, astree :ast.BlockExprAST, mode=COMPILER_MODE_MAIN, filename='<DEFAULT>',
                 ext_varname :tuple=()):
        self.__ast = astree
        self.__now_ast :ast.ExprAST = astree
        self.__general_bytecode = ByteCode()
        self.__buffer = ByteCodeFileBuffer()

        self.__buffer.bytecodes = self.__general_bytecode
        self.__lnotab = LineNumberTableGenerator()

        self.__buffer.lnotab = self.__lnotab
        self.__buffer.name = filename

        self.__lnotab.firstlineno = astree.stmts[0].ln \
                if isinstance(astree, ast.BlockExprAST) and astree.stmts  \
                else 1

        self.__lnotab.init_table()

        self.__flag = 0x0

        self.__mode = mode

        self.__init_ext_varname(ext_varname)

    def __init_ext_varname(self, ext_varname :tuple):
        if self.__mode == COMPILER_MODE_FUNC:
            for n in ext_varname:
                self.__buffer.get_or_add_varname_index(n)

    def __update_lnotab(self, line :int):
        self.__lnotab.check(line)

    def __flag_set(self, f :int):
        self.__flag |= f

    def __flag_cmp(self, f :int) -> bool:
        return self.__flag & f

    def __bytecode_update(self, bytecode :ByteCode):
        self.__general_bytecode.blist += bytecode.blist
        self.__lnotab.check()

    @property
    def __now_offset(self) -> int:
        return len(self.__general_bytecode.blist)

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
                'MOD' : binary_mod,
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

    def __compile_print_expr(self, tree :ast.PrintExprAST) -> ByteCode:
        bc = ByteCode()

        expl = tree.value_list

        for et in expl:
            etc = self.__compile_binary_expr(et)
            bc += etc

        bc.add_bytecode(print_value, len(expl))
        
        return bc

    def __compile_input_expr(self, tree :ast.InputExprAST) -> ByteCode:
        bc = ByteCode()

        expc = self.__compile_binary_expr(tree.msg)
        bc += expc

        vl = tree.value_list.value_list

        for name in vl:
            ni = self.__buffer.get_or_add_varname_index(name)
            bc.add_bytecode(load_varname, ni)

        bc.add_bytecode(input_value, len(vl))

        return bc

    def __compile_comp_expr(self, tree :ast.CmpTestAST) -> ByteCode:
        bc = ByteCode()
        
        # left
        if isinstance(tree, ast.CellAST):
            s, i = self.__do_cell_ast(tree)

            bc.add_bytecode(load_const if s == 0 else load_global, i)

            return bc

        elif type(tree) in ast.BINARY_AST_TYPES:
            return self.__compile_binary_expr(tree)

        elif isinstance(tree, ast.CallExprAST):
            return self.__compile_call_expr(tree)

        elif type(tree.left) in ast.BINARY_AST_TYPES:
            bc += self.__compile_binary_expr(tree.left)

        # right

        for op, et in tree.right:
            opi = COMPARE_OPERATORS.index(op)

            etc = self.__compile_binary_expr(et)

            bc += etc
            bc.add_bytecode(compare_op, opi)

        return bc

    def __compile_or_expr(self, tree :ast.AndTestAST, extofs :int=0) -> ByteCode:
        '''
        extofs : 当 and 不成立约过的除右部以外的字节码偏移量
                 当为 0 时，则不处理extofs
        '''
        bc = ByteCode()
        
        if isinstance(tree, ast.AndTestAST):
            return self.__compile_and_expr(tree, extofs)

        lbc = self.__compile_and_expr(tree.left, with_or=True)

        rbcl = []

        for rt in tree.right:
            tbc = self.__compile_and_expr(rt)
            rbcl.append(tbc)

        # count right total offset
        # jump_ofs = lofs + rofs + extofs + (EACH_BYTECODE_SIZE)
        jopc = len(rbcl)# jump operator count | jopc = len(rbcl) + len([left bytecode offset])
        jofs = extofs + sum([len(b.blist) for b in rbcl]) + len(lbc.blist) + _BYTE_CODE_SIZE * jopc

        bc += lbc
        
        for tbc in rbcl:
            bc.add_bytecode(jump_if_true_or_pop, jofs)
            bc += tbc
            jopc += 1

        return bc

    def __compile_and_expr(self, tree :ast.AndTestAST, extofs :int=0, with_or=False) -> ByteCode:
        '''
        extofs : 当 and 不成立约过的除右部以外的字节码偏移量
                 当为 0 时，则不处理extofs
        '''
        bc = ByteCode()

        # similar to or

        if type(tree) in ast.BINARY_AST_TYPES:
            return self.__compile_binary_expr(tree)

        if isinstance(tree, ast.CmpTestAST):
            return self.__compile_comp_expr(tree)

        lbc = self.__compile_comp_expr(tree.left)

        rbcl = []

        for rt in tree.right:
            tbc = self.__compile_comp_expr(rt)
            rbcl.append(tbc)
            
        # count right total offset
        # jump_ofs = lofs + rofs + extofs + (EACH_BYTECODE_SIZE)
        jopc = len(rbcl)# jump operator count | jopc = len(rbcl) + len([left bytecode offset])
        jofs = extofs + sum([len(b.blist) for b in rbcl]) + len(lbc.blist) + _BYTE_CODE_SIZE * jopc

        bc += lbc
        
        for tbc in rbcl:
            bc.add_bytecode(jump_if_false_or_pop, jofs)
            bc += tbc
            jopc += 1

        return bc

    def __compile_test_expr(self, tree :ast.TestExprAST, extofs :int=0) -> ByteCode:
        bc = ByteCode()
        test = tree.test

        if type(test) in ast.BINARY_AST_TYPES:
            return self.__compile_binary_expr(test)
        elif isinstance(test, ast.CmpTestAST):
            return self.__compile_comp_expr(test)
        else:
            return self.__compile_or_expr(test, extofs)

    def __compile_while_stmt(self, tree :ast.WhileExprAST, extofs :int):
        bc = ByteCode()

        b = tree.block

        tc = self.__compile_test_expr(tree.test, extofs)

        bcc = self.__compile_block(b, len(tc.blist) + extofs)

        jump_over = extofs + len(bcc.blist) + _BYTE_CODE_SIZE * 2
        # three times of _byte_code_size means (
        #   jump over setup_while, jump over block, jump over jump_absolute)
        
        tc = self.__compile_test_expr(tree.test, jump_over)
        # compile again. first time for the length of test opcodes
        # second time for jump offset

        bc += tc

        back = extofs  # move to first opcode in block
        to = len(bcc.blist) + extofs + len(tc.blist) + _BYTE_CODE_SIZE * 2
        # including setup_while and jump over block
        bc.add_bytecode(setup_while, to)

        bc += bcc
        bc.add_bytecode(jump_absolute, back)

        return bc

    def __compile_do_loop_stmt(self, tree :ast.DoLoopExprAST, extofs :int):
        bc = ByteCode()

        tc = self.__compile_test_expr(tree.test, 0)  # first compile
        bcc = self.__compile_block(tree.block, extofs)

        jump_over = len(bcc.blist) + len(tc.blist) + extofs + _BYTE_CODE_SIZE * 2

        bc.add_bytecode(setup_doloop, jump_over)

        test_jump = extofs + len(bcc.blist)

        tc = self.__compile_test_expr(tree.test, test_jump)

        bc += bcc
        bc += tc

        jump_back = extofs + _BYTE_CODE_SIZE  # over setup_doloop
        bc.add_bytecode(jump_if_true_or_pop, jump_back)

        return bc

    def __compile_if_else_stmt(self, tree :ast.IfExprAST, extofs :int):
        bc = ByteCode()

        has_else = len(tree.else_block.stmts) > 0

        tc = self.__compile_test_expr(tree.test, extofs)

        ifbc = self.__compile_block(tree.block, extofs)

        jump_over_ifb = len(ifbc.blist) + len(tc.blist) + extofs

        if has_else:
            elbc = self.__compile_block(tree.else_block, jump_over_ifb)
        else:
            elbc = ByteCode()

        # 如果拥有 if 则 条件为false时跳到else块
        
        jump_over = extofs + len(tc.blist) + len(ifbc.blist) \
                        + len(elbc.blist) + (_BYTE_CODE_SIZE
                                                if has_else
                                                else 0) + _BYTE_CODE_SIZE
        # include 'jump_absolute' at the end of ifbc
        # last _byte_code_size is for 'jump_if_false_or_pop'
        
        if has_else:
            ifbc.add_bytecode(jump_absolute, jump_over)

        test_jump = len(tc.blist) + len(ifbc.blist) + extofs + _BYTE_CODE_SIZE # * 2
        # 不需要加elbc的长度, 乘2是为了越过block

        # tc = self.__compile_test_expr(tree.test, test_jump)
        tc.add_bytecode(jump_if_false_or_pop, test_jump)

        bc += tc
        bc += ifbc
        bc += elbc

        return bc

    def __compile_return_expr(self, tree :ast.ReturnAST) -> ByteCode:
        bc = ByteCode()
        bce = self.__compile_binary_expr(tree.expr)

        bc += bce
        bc.add_bytecode(return_value, 0)

        return bc

    def __compile_break_expr(self, tree :ast.BreakAST) -> ByteCode:
        bc = ByteCode()
        bc.add_bytecode(break_loop, 0)

        return bc

    def __compile_continue_expr(self, tree :ast.ContinueAST) -> ByteCode:
        bc = ByteCode()
        bc.add_bytecode(continue_loop, 0)

        return bc

    def __compile_function(self, tree :ast.FunctionDefineAST) -> ByteCode:
        bc = ByteCode()

        ext = [c.value for c in tree.arg_list.exp_list]

        cobj = Compiler(tree.block, mode=COMPILER_MODE_FUNC, filename=tree.name,
                        ext_varname=ext).compile(tree.block).code_object
        cobj.argcount = len(tree.arg_list.exp_list)

        ci = self.__buffer.add_const(cobj)

        namei = self.__buffer.get_or_add_varname_index(tree.name)
    
        bc.add_bytecode(load_const, ci)
        bc.add_bytecode(store_function, namei)

        return bc

    def __compile_plain_call(self, tree :ast.CallExprAST) -> ByteCode:
        bc = ByteCode()

        ni = self.__buffer.get_or_add_varname_index(tree.name)

        bc.add_bytecode(load_global, ni)

        for et in tree.arg_list.exp_list:
            bc += self.__compile_binary_expr(et)

        bc.add_bytecode(call_func, len(tree.arg_list.exp_list))
        bc.add_bytecode(pop_top, 0)

        return bc

    def __compile_block(self, tree :ast.BlockExprAST, firstoffset=0) -> ByteCode:
        bc = self.__general_bytecode = ByteCode()
        last_ln = 0
        total_offset = firstoffset
        et = None

        for eti in range(len(tree.stmts)):
            et = tree.stmts[eti]

            #self.__lnotab.mark(et.ln, total_offset)

            if isinstance(et, ast.InputExprAST):
                tbc = self.__compile_input_expr(et)

            elif isinstance(et, ast.PrintExprAST):
                tbc = self.__compile_print_expr(et)

            elif isinstance(et, ast.DefineExprAST):
                tbc = self.__compile_define_expr(et)
            
            elif isinstance(et, ast.IfExprAST):
                tbc = self.__compile_if_else_stmt(et, total_offset)

            elif isinstance(et, ast.WhileExprAST):
                tbc = self.__compile_while_stmt(et, total_offset)

            elif isinstance(et, ast.DoLoopExprAST):
                tbc = self.__compile_do_loop_stmt(et, total_offset)

            elif isinstance(et, ast.FunctionDefineAST):
                tbc = self.__compile_function(et)

            elif isinstance(et, ast.ReturnAST):
                tbc = self.__compile_return_expr(et)

            elif isinstance(et, ast.BreakAST):
                tbc = self.__compile_break_expr(et)

            elif isinstance(et, ast.ContinueAST):
                tbc = self.__compile_continue_expr(et)

            elif isinstance(et, ast.CallExprAST):
                tbc = self.__compile_plain_call(et)

            else:
                print('W: Unknown AST type: %s' % type(et))
 
            total_offset += len(tbc.blist) 

            if eti + 1 < len(tree.stmts):
                #self.__lnotab.update(tree.stmts[eti + 1].ln, total_offset)
                pass

            bc += tbc
        else:
            if et:
                #self.__lnotab.update(et.ln + 1, total_offset)
                pass

        return bc

    def __make_final_return(self) -> ByteCode:
        bc = ByteCode()

        ni = self.__buffer.add_const(null)

        bc.add_bytecode(load_const, ni)
        bc.add_bytecode(return_value, 0)

        return bc

    def compile(self, astree :ast.BlockExprAST) -> ByteCodeFileBuffer:
        tbc = self.__compile_block(astree)

        # if tbc.blist and tbc.blist[-2] != return_value:
        tbc += self.__make_final_return()

        self.__buffer.bytecodes = tbc

        return self.__buffer

    def test(self, tree) -> ByteCodeFileBuffer:
        bc = self.__compile_block(tree, 0)

        if bc.blist[-2] != return_value:
            bc += self.__make_final_return()
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
    #t = t.stmts[0]

    c = Compiler(t)
    bf = c.test(t)

    test_utils.show_bytecode(bf)


if __name__ == '__main__':
    test_compiler()
