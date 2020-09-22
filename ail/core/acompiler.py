
import pickle

from typing import List, Union, Tuple

from .opcodes import *
from .tokentype import LAP_STRING, LAP_IDENTIFIER, LAP_NUMBER

from .abytecode import (
    ByteCode, 
    ByteCodeFileBuffer, 
    LineNumberTableGenerator,
)

from . import (
    aobjects as obj, 
    aobjects as objs, 
    asts as ast, 
    test_utils
)

from ..objects import (
    string  as astr,
    integer as aint,
    bool    as abool,
    wrapper as awrapper,
    float   as afloat,
)

from ..objects.null import null


__author__ = 'LaomoBK'

_BYTE_CODE_SIZE = 2  # each bytecode & arg size = 8 * 2

COMPILER_MODE_FUNC = 0x1
COMPILER_MODE_MAIN = 0x2

_opcode_map = {
    '+' : binary_add,
    '-' : binary_sub,
    '*' : binary_muit,
    '/' : binary_div,
    'mod' : binary_mod,
    '^' : binary_pow,
}

_cell_action_map = {
    LAP_NUMBER : lambda n : convert_numeric_str_to_number(n),
    LAP_STRING : lambda s : s
}


class Compiler:
    def __init__(self, mode=COMPILER_MODE_MAIN, filename='<DEFAULT>',
                 ext_varname :tuple=()):
        self.__general_bytecode = ByteCode()
        self.__buffer = ByteCodeFileBuffer()

        self.__buffer.bytecodes = self.__general_bytecode
        self.__lnotab = LineNumberTableGenerator()

        self.__buffer.lnotab = self.__lnotab
        self.__buffer.name = filename

        self.__lnotab.init_table()

        self.__flag = 0x0

        self.__mode = mode

        self.__is_single_line = False

        self.__filename = filename
        self.__ext_varname = ext_varname

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
            c = _cell_action_map[cell.type](cell.value)

            ci = self.__buffer.add_const(c)
            sign = 0

        elif cell.type == LAP_IDENTIFIER:
            ci = self.__buffer.get_or_add_varname_index(cell.value)
            sign = 1

        return (sign, ci)

    def __get_operator(self, op :str):
        return _opcode_map[op]

    def __compile_binary_expr(self, tree :ast.BinaryExprAST, is_attr=False,
                              is_single=False) -> ByteCode:
        bc = ByteCode()

        # 先递归处理 left，然后再递归处理right

        if isinstance(tree, ast.CellAST):
            s, i = self.__do_cell_ast(tree)

            bc.add_bytecode(
                    load_const if s == 0 else (load_attr if is_attr else load_global), i)

            return bc

        elif isinstance(tree, ast.CallExprAST):
            bc += self.__compile_call_expr(tree)

        elif isinstance(tree, ast.DefineExprAST):
            bc += self.__compile_assign_expr(tree, single=False)

        elif isinstance(tree, ast.SubscriptExprAST):
            bc += self.__compile_subscript_expr(tree)

        elif isinstance(tree, ast.ArrayAST):
            bc += self.__compile_array_expr(tree)

        elif isinstance(tree, ast.MemberAccessAST):
            bc += self.__compile_member_access_expr(tree)

        elif isinstance(tree, ast.AssignExprAST):
            bc += self.__compile_assign_expr(tree, single=is_single)

        elif isinstance(tree, ast.UnaryExprAST):
            bc += self.__compile_unary_expr(tree)

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

    def __compile_unary_expr(self, tree: ast.UnaryExprAST) -> ByteCode:
        bc = ByteCode()

        rbc = self.__compile_binary_expr(tree.right_expr)

        bc += rbc

        if tree.op == '-':
            bc.add_bytecode(unary_negative, 0)

        return bc

    def __compile_member_access_expr(self, tree :ast.MemberAccessAST,
            set_attr=False) -> ByteCode:
        bc = ByteCode()
        
        # 先 left 后 right
        left = tree.left
        if isinstance(left, ast.SubscriptExprAST):
            bc += self.__compile_subscript_expr(left)
        elif isinstance(left, ast.CallExprAST):
            bc += self.__compile_call_expr(left)
        elif type(left) in ast.BINARY_AST_TYPES:
            bc += self.__compile_binary_expr(left)

        # right

        if not hasattr(tree, 'members'):
            return bc

        for et in tree.members[:-1]:
            if isinstance(et, ast.CellAST):
                s, i = self.__do_cell_ast(et)
                bc.add_bytecode(load_attr, i)

            else:
                etc = {
                        ast.CallExprAST : self.__compile_call_expr,
                        ast.SubscriptExprAST : self.__compile_subscript_expr
                     }[type(et)](et, True)

                bc += etc

        lt = tree.members[-1]
        if isinstance(lt, ast.CellAST):
            ni = self.__buffer.get_or_add_varname_index(lt.value)
            bc.add_bytecode(store_attr if set_attr else load_attr, ni)

        elif isinstance(lt, ast.SubscriptExprAST):
            bc += self.__compile_subscript_expr(lt, True, set_attr)

        elif isinstance(lt, ast.CallExprAST):
            bc += self.__compile_call_expr(lt, True)

        return bc

    def __compile_assign_expr(self, tree :ast.AssignExprAST, single=False) -> ByteCode:
        bc = ByteCode()

        left = tree.left

        store_target = {
            ast.CellAST : store_var,
            ast.SubscriptExprAST : store_subscr,
            ast.MemberAccessAST : store_attr
        }[type(left)]

        vc = self.__compile_binary_expr(tree.value)

        bc += vc

        if store_target == store_var:
            ni = self.__buffer.get_or_add_varname_index(left.value)
            bc.add_bytecode(store_target, ni)

        elif store_target == store_attr:
            ebc = self.__compile_member_access_expr(tree.left, True)
            bc += ebc

        elif store_target == store_subscr:
            bc += self.__compile_subscript_expr(tree.left, False, True)

        if single:
            bc.add_bytecode(pop_top, 0)

        return bc

    def __compile_assign_expr0(self, tree :ast.DefineExprAST, single=False)  -> ByteCode:
        bc = ByteCode()

        ni = self.__buffer.get_or_add_varname_index(tree.name)
        expc = self.__compile_binary_expr(tree.value)

        bc += expc
        bc.add_bytecode(store_var, ni)

        if single:
            bc.add_bytecode(pop_top, 0)

        return bc

    def __compile_call_expr(self, tree :ast.CallExprAST, is_attr=False) -> ByteCode:
        bc = ByteCode()

        lbc = self.__compile_binary_expr(tree.left, is_attr=is_attr)

        bc += lbc

        expl = tree.arg_list.exp_list
        
        for et in expl:
            etc = self.__compile_binary_expr(et)
            bc += etc

        bc.add_bytecode(call_func, len(expl))

        return bc

    def __compile_subscript_expr(self, tree :ast.SubscriptExprAST, 
            is_attr=False, store=False) -> ByteCode:
        bc = ByteCode()
        
        lc = self.__compile_binary_expr(tree.left, is_attr=is_attr)
        ec = self.__compile_binary_expr(tree.expr)

        bc += lc
        bc += ec
        
        bc.add_bytecode(binary_subscr if not store else store_subscr, 0)

        return bc

    def __compile_array_expr(self, tree :ast.ArrayAST) -> ByteCode:
        bc = ByteCode()

        items = tree.items

        for et in items.item_list:
            etc = self.__compile_binary_expr(et)
            bc += etc

        bc.add_bytecode(build_array, len(items.item_list))

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

    def __compile_try_catch_expr(self, tree :ast.TryCatchExprAST, extofs :int=0):
        bc = ByteCode()

        extofs += _BYTE_CODE_SIZE  # for setup_try
        has_finally = len(tree.finally_block.stmts) > 0

        tbc = self.__compile_block(tree.try_block, extofs)

        cat_ext = extofs + len(tbc.blist) + _BYTE_CODE_SIZE * 3
        # for setup_catch and jump_absolute
        cabc = self.__compile_block(tree.catch_block, cat_ext)

        jump_over = cat_ext + len(cabc.blist) + _BYTE_CODE_SIZE
        # for clean_catch
        to_catch = extofs + len(tbc.blist) + _BYTE_CODE_SIZE * 2
        # for jump_absoulte

        if has_finally:
            fn_ext = jump_over
            fnbc = self.__compile_block(tree.finally_block, jump_over)
        else:
            fnbc = ByteCode()

        ni = self.__buffer.get_or_add_varname_index(tree.name)

        bc.add_bytecode(setup_try, to_catch)
        bc += tbc
        bc.add_bytecode(clean_try, 0)
        bc.add_bytecode(jump_absolute, jump_over)
        bc.add_bytecode(setup_catch, ni)
        bc += cabc
        bc.add_bytecode(clean_catch, 0)
        bc += fnbc

        return bc

    def __compile_comp_expr(self, tree :ast.CmpTestAST, extofs :int=0) -> ByteCode:
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

        elif isinstance(tree, ast.TestExprAST):
            return self.__compile_test_expr(tree, extofs)

        elif type(tree.left) in ast.BINARY_AST_TYPES:
            bc += self.__compile_binary_expr(tree.left)

        else:
            bc += self.__compile_comp_expr(tree.left)

        # right

        for op, et in tree.right:
            opi = COMPARE_OPERATORS.index(op)

            etc = self.__compile_binary_expr(et)

            bc += etc
            bc.add_bytecode(compare_op, opi)

        return bc

    def __compile_not_test_expr(self, tree :ast.NotTestAST, extofs :int=0):
        bc = ByteCode()

        if isinstance(tree, ast.NotTestAST):
            bce = self.__compile_comp_expr(tree.expr, extofs)
            bc += bce
            bc.add_bytecode(binary_not, 0)

            return bc
        return self.__compile_comp_expr(tree, extofs)

    def __compile_or_expr(self, tree :ast.AndTestAST, extofs :int=0) -> ByteCode:
        '''
        extofs : 当 and 不成立约过的除右部以外的字节码偏移量
                 当为 0 时，则不处理extofs
        '''
        bc = ByteCode()
        
        if isinstance(tree, ast.AndTestAST):
            return self.__compile_and_expr(tree, extofs)
        if isinstance(tree, ast.NotTestAST):
            return self.__compile_not_test_expr(tree, extofs)
        if isinstance(tree, ast.TestExprAST):
            return self.__compile_test_expr(tree, extofs)
        if isinstance(tree.left, ast.TestExprAST):
            return self.__compile_test_expr(tree.left, extofs)

        lbc = self.__compile_and_expr(tree.left, with_or=True)

        rbcl = []

        r_ext = len(lbc.blist) + extofs + _BYTE_CODE_SIZE

        for rt in tree.right:
            tbc = self.__compile_and_expr(rt, r_ext)
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

        if isinstance(tree, ast.NotTestAST):
            return self.__compile_not_test_expr(tree)

        bc = ByteCode()

        # similar to or

        if type(tree) in ast.BINARY_AST_TYPES:
            return self.__compile_binary_expr(tree)

        elif isinstance(tree, ast.CmpTestAST):
            return self.__compile_comp_expr(tree)

        elif isinstance(tree, ast.TestExprAST):
            return self.__compile_test_expr(tree, extofs)

        elif isinstance(tree.left, ast.TestExprAST):
            return self.__compile_test_expr(tree.left, extofs)

        lbc = self.__compile_not_test_expr(tree.left)

        rbcl = []

        r_ext = len(lbc.blist) + extofs + _BYTE_CODE_SIZE

        for rt in tree.right:
            tbc = self.__compile_not_test_expr(rt, r_ext)
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
            return self.__compile_comp_expr(test, extofs)
        else:
            return self.__compile_or_expr(test, extofs)

    def __compile_while_stmt(self, tree :ast.WhileExprAST, extofs :int):
        bc = ByteCode()
        extofs += _BYTE_CODE_SIZE

        b = tree.block

        tc = self.__compile_test_expr(tree.test, extofs)

        bcc = self.__compile_block(b, len(tc.blist) + extofs + _BYTE_CODE_SIZE)
        # _byte_code_size for 'setup_while'

        jump_over = extofs + len(bcc.blist) + _BYTE_CODE_SIZE * 2
        # three times of _byte_code_size means (
        #   jump over setup_while, jump over block, jump over jump_absolute)
        
        tc = self.__compile_test_expr(tree.test, jump_over)
        # compile again. first time for the length of test opcodes
        # second time for jump offset

        back = extofs  # move to first opcode in block
        to = len(bcc.blist) + extofs + len(tc.blist) + _BYTE_CODE_SIZE * 2
        # including setup_while and jump over block

        bc.add_bytecode(setup_while, to + _BYTE_CODE_SIZE)  # jump over clean_loop
        bc += tc
        bc.add_bytecode(jump_if_false_or_pop, to)

        bc += bcc
        bc.add_bytecode(jump_absolute, back)
        bc.add_bytecode(clean_loop, 0)

        return bc

    def __compile_do_loop_stmt(self, tree :ast.DoLoopExprAST, extofs :int):
        bc = ByteCode()

        tc = self.__compile_test_expr(tree.test, 0)  # first compile

        loopb_ext = extofs + _BYTE_CODE_SIZE  # setup_do_loop

        bcc = self.__compile_block(tree.block, loopb_ext)

        jump_over = len(bcc.blist) + len(tc.blist) + extofs + _BYTE_CODE_SIZE * 2

        bc.add_bytecode(setup_doloop, jump_over + _BYTE_CODE_SIZE)  # jump over clean_loop

        test_jump = extofs + len(bcc.blist)

        tc = self.__compile_test_expr(tree.test, test_jump)

        bc += bcc
        bc += tc

        jump_back = extofs + _BYTE_CODE_SIZE  # over setup_doloop
        bc.add_bytecode(jump_if_false_or_pop, jump_back)
        bc.add_bytecode(clean_loop, 0)

        return bc

    def __compile_for_stmt(self, tree :ast.ForExprAST, extofs :int):
        bc = ByteCode()

        extofs += _BYTE_CODE_SIZE  # for init_for

        initbc = ByteCode()

        for et in tree.init_list.expr_list:
            initbc += self.__compile_assign_expr(et, single=True)

        test_ext = extofs + len(initbc.blist)

        jump_back = test_ext
        
        if tree.test is not None:
            tbc = self.__compile_test_expr(tree.test, test_ext)
        else:
            tbc = ByteCode()
            tbc.add_bytecode(load_const, self.__buffer.add_const(True))

        block_ext = extofs + len(tbc.blist) + len(initbc.blist) + _BYTE_CODE_SIZE
        # _byte_code_size is for jump_if_false_or_pop

        blc = self.__compile_block(tree.block, block_ext)

        updbc = ByteCode()

        for et in tree.update_list.expr_list:
            updbc += self.__compile_binary_expr(et, is_single=True)

        jump_over = block_ext + len(blc.blist) + len(updbc.blist) + _BYTE_CODE_SIZE
        # _byte_code_size for jump_absolute

        bc.add_bytecode(setup_for, jump_over + _BYTE_CODE_SIZE)  # jump over clean_loop
        bc += initbc
        bc += tbc
        bc.add_bytecode(jump_if_false_or_pop, jump_over)
        bc += blc
        bc += updbc
        bc.add_bytecode(jump_absolute, jump_back)
        bc.add_bytecode(clean_for, 0)

        return bc

    def __compile_if_else_stmt(self, tree :ast.IfExprAST, extofs :int):
        bc = ByteCode()

        has_else = len(tree.else_block.stmts) > 0
        
        tc = self.__compile_test_expr(tree.test, extofs)

        ifbc_ext = extofs + len(tc.blist)  + _BYTE_CODE_SIZE  # jump_if_false_or_pop

        ifbc = self.__compile_block(tree.block, ifbc_ext)

        jump_over_ifb = len(ifbc.blist) + len(tc.blist) + extofs + _BYTE_CODE_SIZE + \
                        (_BYTE_CODE_SIZE if has_else else 0)   # jump_absolute if has else

        if has_else:
            elbc = self.__compile_block(tree.else_block, jump_over_ifb)
        else:
            elbc = ByteCode()

        # 如果拥有 if 则条件为false时跳到else块
        
        jump_over = extofs + len(tc.blist) + len(ifbc.blist) \
                        + len(elbc.blist) + _BYTE_CODE_SIZE * (2
                                                    if has_else
                                                    else 1) #+ _BYTE_CODE_SIZE
        # include 'jump_absolute' at the end of ifbc
        # last _byte_code_size is for 'jump_if_false_or_pop'
        
        if has_else:
            ifbc.add_bytecode(jump_absolute, jump_over)

        test_jump = len(tc.blist) + len(ifbc.blist) + extofs + _BYTE_CODE_SIZE
        # 不需要加elbc的长度

        # tc = self.__compile_test_expr(tree.test, test_jump)
        tc.add_bytecode(pop_jump_if_false_or_pop, test_jump)

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

    def __compile_assert_expr(self, tree :ast.AssertExprAST, extofs :int) -> ByteCode:
        bc = ByteCode()

        ec = self.__compile_test_expr(tree.expr, extofs) 
        ci = self.__buffer.add_const('AssertionError')

        jump = extofs + len(ec.blist) + _BYTE_CODE_SIZE * 3

        bc += ec

        bc.add_bytecode(jump_if_true_or_pop, jump)
        bc.add_bytecode(load_const, ci)
        bc.add_bytecode(throw_error, 0)

        return bc


    def __compile_throw_expr(self, tree :ast.ThrowExprAST) -> ByteCode:
        bc = ByteCode()

        ec = self.__compile_binary_expr(tree.expr)

        bc += ec
        bc.add_bytecode(throw_error, 0)

        return bc

    def __compile_load_stmt(self, tree :ast.LoadAST) -> ByteCode:
        bc = ByteCode()

        ni = self.__buffer.add_const(tree.name)

        bc.add_bytecode(load_module, ni)

        return bc

    def __compile_function(self, tree :ast.FunctionDefineAST) -> ByteCode:
        bc = ByteCode()

        has_bindto = tree.bindto != None

        ext = [c.value for c in tree.arg_list.exp_list]

        cobj = Compiler(mode=COMPILER_MODE_FUNC, filename=tree.name,
                        ext_varname=ext).compile(tree.block).code_object
        cobj.argcount = len(tree.arg_list.exp_list)

        if self.__mode == COMPILER_MODE_FUNC:
            cobj.closure = True

        ci = self.__buffer.add_const(cobj)

        namei = self.__buffer.get_or_add_varname_index(tree.name)
        
        bindtoi = self.__buffer.get_or_add_varname_index(tree.bindto)  \
                    if has_bindto else 0
    
        bc.add_bytecode(load_const, ci)
        if has_bindto:
            bc.add_bytecode(load_varname, namei)
            bc.add_bytecode(bind_function, bindtoi)
        else:
            bc.add_bytecode(store_function, namei)

        return bc

    def __compile_plain_call(self, tree :ast.CallExprAST) -> ByteCode:
        bc = ByteCode()

        lbc = self.__compile_binary_expr(tree.left)

        bc += lbc

        for et in tree.arg_list.exp_list:
            bc += self.__compile_binary_expr(et)

        bc.add_bytecode(call_func, len(tree.arg_list.exp_list))
        
        if not self.__is_single_line:
            bc.add_bytecode(pop_top, 0)

        return bc

    def __compile_struct(self, tree :ast.StructDefineAST) -> ByteCode:
        bc = ByteCode()

        plist = tree.protected_list

        for n in tree.name_list:
            ni = self.__buffer.get_or_add_varname_index(n)
            bc.add_bytecode(load_varname, ni)
            if n in plist:
                bc.add_bytecode(set_protected, 0)

        ni = self.__buffer.get_or_add_varname_index(tree.name)

        bc.add_bytecode(load_varname, ni)
        bc.add_bytecode(store_struct, len(tree.name_list) + len(plist))

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
                tbc = self.__compile_assign_expr(et, single=True)
            
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

            elif isinstance(et, ast.LoadAST):
                tbc = self.__compile_load_stmt(et)

            elif isinstance(et, ast.AssignExprAST):
                tbc = self.__compile_assign_expr(et, True)

            elif isinstance(et, ast.StructDefineAST):
                tbc = self.__compile_struct(et)

            elif isinstance(et, ast.ForExprAST):
                tbc = self.__compile_for_stmt(et, total_offset)

            elif isinstance(et, ast.AssertExprAST):
                tbc = self.__compile_assert_expr(et, total_offset)

            elif isinstance(et, ast.ThrowExprAST):
                tbc = self.__compile_throw_expr(et)

            elif isinstance(et, ast.TryCatchExprAST):
                tbc = self.__compile_try_catch_expr(et, total_offset)

            elif type(et) in ast.BINARY_AST_TYPES:
                tbc = self.__compile_binary_expr(et, is_single=True)

                if not self.__is_single_line:
                    tbc.add_bytecode(pop_top, 0)

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

        if self.__is_single_line:
            return bc

        ni = self.__buffer.add_const(null)

        bc.add_bytecode(load_const, ni)
        bc.add_bytecode(return_value, 0)

        return bc

    def compile(self, astree :ast.BlockExprAST, single_line=False) -> ByteCodeFileBuffer:
        self.__init__(self.__mode, self.__filename, self.__ext_varname)
        self.__is_single_line = single_line

        self.__lnotab.firstlineno = astree.stmts[0].ln \
            if isinstance(astree, ast.BlockExprAST) and astree.stmts \
            else 1

        tbc = self.__compile_block(astree)

        # if tbc.blist and tbc.blist[-2] != return_value:
        tbc += self.__make_final_return()

        self.__buffer.bytecodes = tbc

        return self.__buffer

    def __test(self, tree) -> ByteCodeFileBuffer:
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
    try:
        v = eval(value)
    except SyntaxError:
        return -1

    if type(v) in (int, float):
        return v
    return None


def test_compiler():
    from .aparser import Parser
    from .alex import Lex

    l = Lex('./tests/test.ail')
    ts = l.lex()

    p = Parser('./tests/test.ail')
    t = p.parse(ts)

    c = Compiler(t)
    bf = c.compile(t)

    test_utils.show_bytecode(bf)


if __name__ == '__main__':
    test_compiler()
