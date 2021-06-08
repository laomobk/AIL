import pickle

from typing import List, Union, Tuple

from .aopcode import *
from .tokentype import (
    AIL_STRING, AIL_IDENTIFIER, AIL_NUMBER,
    AIL_ASSI,
    AIL_INP_PLUS, AIL_INP_SUB, AIL_INP_MULT,
    AIL_INP_DIV, AIL_INP_MOD, AIL_INP_XOR,
    AIL_INP_BIN_OR, AIL_INP_LSHIFT, AIL_INP_RSHIFT,
    AIL_INP_BIN_AND
)

from .abytecode import (
    ByteCode,
    ByteCodeFileBuffer,
    LineNumberTableGenerator,
)

from .aconfig import BYTE_CODE_SIZE

from . import (
    aobjects as obj,
    aobjects as objs,
    asts as ast,
    error,
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

COMPILER_MODE_FUNC = 0x1
COMPILER_MODE_MAIN = 0x2

COMPILE_MAIN_NAME = '<main>'

_opcode_map = {
    '+': binary_add,
    '-': binary_sub,
    '*': binary_mult,
    '/': binary_div,
    'mod': binary_mod,
    '**': binary_pow,
    '<<': binary_lshift,
    '>>': binary_rshift,
    '&': binary_and,
    '|': binary_or,
    '^': binary_xor,
}

_assign_op_map = {
    AIL_INP_PLUS: inplace_add,
    AIL_INP_SUB: inplace_sub,
    AIL_INP_MULT: inplace_mult,
    AIL_INP_DIV: inplace_div,
    AIL_INP_MOD: inplace_mod,
    AIL_INP_XOR: inplace_xor,
    AIL_INP_BIN_OR: inplace_bin_or,
    AIL_INP_LSHIFT: inplace_lshift,
    AIL_INP_RSHIFT: inplace_rshift,
    AIL_INP_BIN_AND: inplace_bin_and,
}

_cell_action_map = {
    AIL_NUMBER: lambda n: convert_numeric_str_to_number(n),
    AIL_STRING: lambda s: s
}

_class_name_stack = list()


def _make_function_signature(tree: ast.FunctionDefineAST):
    func_signature_template = 'fun {bind_to}{name}({arg_list})'
    arg_list_str_list = []

    name = tree.name
    bind_to = '(%s) ' % tree.bindto if tree.bindto is not None else ''
    arg_list = tree.arg_list.arg_list

    for arg in arg_list:
        arg_name = arg.expr.value
        arg_list_str_list.append('%s%s' % ('*' if arg.star else '', arg_name))

    arg_list_str = ', '.join(arg_list_str_list)

    return func_signature_template.format(
            bind_to=bind_to, name=name, arg_list=arg_list_str)


class Compiler:
    def __init__(self, mode=COMPILER_MODE_MAIN, filename='<DEFAULT>',
                 ext_varname: tuple = (), name: str = COMPILE_MAIN_NAME):
        self.__general_bytecode = ByteCode()
        self.__buffer = ByteCodeFileBuffer()

        self.__buffer.bytecodes = self.__general_bytecode
        self.__lnotab = LineNumberTableGenerator()

        self.__buffer.lnotab = self.__lnotab
        self.__buffer.filename = filename
        self.__buffer.name = name

        self.__lnotab.init_table()

        self.__flag = 0x0

        self.__mode = mode

        self.__is_single_line = False

        self.__filename = filename
        self.__ext_varname = ext_varname
        self.__name = name

        self.__init_ext_varname(ext_varname)

    def __init_ext_varname(self, ext_varname: tuple):
        if self.__mode == COMPILER_MODE_FUNC:
            for n in ext_varname:
                self.__buffer.get_or_add_varname_index(n)

    def __update_lnotab(self, line: int):
        self.__lnotab.check(line)

    def __flag_set(self, f: int):
        self.__flag |= f

    def __flag_cmp(self, f: int) -> bool:
        return bool(self.__flag & f)

    def __bytecode_update(self, bytecode: ByteCode, lno: int):
        self.__general_bytecode.blist += bytecode.blist
        self.__lnotab.check(lno)

    @property
    def __now_offset(self) -> int:
        return len(self.__general_bytecode.blist)

    def __do_cell_ast(self, cell: ast.CellAST) -> Tuple[int, int]:
        """
        sign :
            0 : number or str
            1 : identifier
        return : (sign, index)
        """

        if cell.type in (AIL_NUMBER, AIL_STRING):
            c = _cell_action_map[cell.type](cell.value)

            ci = self.__buffer.add_const(c)
            sign = 0

        elif cell.type == AIL_IDENTIFIER:
            ci = self.__buffer.get_or_add_varname_index(cell.value)
            sign = 1

        return sign, ci

    def __get_operator(self, op: str):
        return _opcode_map[op]

    def __compile_binary_expr(self, tree: ast.AddSubExprAST, is_attr=False,
                              is_single=False) -> ByteCode:
        bc = ByteCode()

        # 先递归处理 left，然后再递归处理right

        if isinstance(tree, ast.CellAST):
            s, i = self.__do_cell_ast(tree)

            bc.add_bytecode(
                load_const if s == 0 else (load_attr if is_attr else load_variable),
                i, tree.ln)

            return bc

        elif isinstance(tree, ast.AssignExprAST):
            return self.__compile_assign_expr(tree, is_single)

        elif isinstance(tree, ast.CallExprAST):
            bc += self.__compile_call_expr(tree)

        elif isinstance(tree, ast.DefineExprAST):
            bc += self.__compile_assign_expr(tree, single=False)

        elif isinstance(tree, ast.SubscriptExprAST):
            bc += self.__compile_subscript_expr(tree)

        elif isinstance(tree, ast.ArrayAST):
            bc += self.__compile_array_expr(tree)

        elif isinstance(tree, ast.MapAST):
            bc += self.__compile_map_expr(tree)

        elif isinstance(tree, ast.MemberAccessAST):
            bc += self.__compile_member_access_expr(tree)

        elif isinstance(tree, ast.AssignExprAST):
            bc += self.__compile_assign_expr(tree, single=is_single)

        elif isinstance(tree, ast.UnaryExprAST):
            bc += self.__compile_unary_expr(tree, is_single)

        elif isinstance(tree, ast.TestExprAST):
            return self.__compile_test_expr(tree, 0)

        elif isinstance(tree, ast.FunctionDefineAST):
            bc += self.__compile_function(tree, anonymous_function=True)

        elif isinstance(tree, ast.TupleAST):
            bc += self.__compile_tuple_expr(tree)

        elif type(tree.left) in ast.BINARY_AST_TYPES:
            bc += self.__compile_binary_expr(tree.left)

        # right

        if not hasattr(tree, 'right'):
            return bc

        for op, rtree in tree.right:
            opc = self.__get_operator(op)
            rbc = self.__compile_binary_expr(rtree)
            bc += rbc

            bc.add_bytecode(opc, 0, rtree.ln)

        return bc

    def __compile_tuple_expr(self, tree: ast.TupleAST) -> ByteCode:
        bc = ByteCode()

        for elt in tree.items:
            bc += self.__compile_binary_expr(elt)

        bc.add_bytecode(build_tuple, len(tree.items), tree.ln)
        
        return bc

    def __compile_unary_expr(self, 
            tree: ast.UnaryExprAST, single=False) -> ByteCode:
        bc = ByteCode()

        rbc = self.__compile_binary_expr(tree.right_expr)

        bc += rbc

        if tree.op == '-':
            bc.add_bytecode(unary_negative, 0, tree.ln)
        elif tree.op == '~':
            bc.add_bytecode(unary_invert, 0, tree.ln)
        elif tree.op in ('++', '--'):
            operation = {'++': unary_inc, '--': unary_dec}.get(tree.op)
            store_ast = ast.AssignExprAST(
                    tree.right_expr, None, tree.ln)
            store_code = self.__compile_assign_expr(store_ast)
            bc.add_bytecode(operation, 0, tree.ln)
            bc += store_code
            if single:
                bc.add_bytecode(pop_top, 0, -1)

        return bc

    def __compile_member_access_expr(self, tree: ast.MemberAccessAST,
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
                bc.add_bytecode(load_attr, i, et.ln)

            else:
                etc = {
                    ast.CallExprAST: self.__compile_call_expr,
                    ast.SubscriptExprAST: self.__compile_subscript_expr
                }[type(et)](et, True)

                bc += etc

        lt = tree.members[-1]
        if isinstance(lt, ast.CellAST):
            ni = self.__buffer.get_or_add_varname_index(lt.value)
            bc.add_bytecode(store_attr if set_attr else load_attr, ni, lt.ln)

        elif isinstance(lt, ast.SubscriptExprAST):
            bc += self.__compile_subscript_expr(lt, True, set_attr)

        elif isinstance(lt, ast.CallExprAST):
            bc += self.__compile_call_expr(lt, True)

        return bc

    def __compile_inplace_assign_expr(
            self, tree: ast.AssignExprAST, single=False) -> ByteCode:
        opcode = _assign_op_map.get(tree.op)
        assert opcode is not None

        bc = ByteCode()
        ln = tree.ln

        left = tree.left

        store_target = {
            ast.CellAST: store_var,
            ast.SubscriptExprAST: store_subscr,
            ast.MemberAccessAST: store_attr
        }[type(left)]

        if store_target == store_var:
            namei = self.__buffer.get_or_add_varname_index(left.value)
            bc.add_bytecode(opcode, 0, ln)
            bc.add_bytecode(store_target, namei, ln)
        elif store_target == store_attr:
            pass 

    def __compile_assign_expr(self, 
            tree: ast.AssignExprAST, single = False) -> ByteCode:
        bc = ByteCode()

        left = tree.left

        type_map = {
            ast.CellAST: store_var,
            ast.SubscriptExprAST: store_subscr,
            ast.MemberAccessAST: store_attr,
            ast.TupleAST: None
        }

        store_target = type_map[type(left)]
        
        if tree.right is not None:
            vc = self.__compile_binary_expr(tree.right)
            bc += vc

        if store_target == store_var:
            ni = self.__buffer.get_or_add_varname_index(left.value)
            bc.add_bytecode(store_target, ni, tree.ln)

        elif store_target == store_attr:
            ebc = self.__compile_member_access_expr(tree.left, True)
            bc += ebc

        elif store_target == store_subscr:
            bc += self.__compile_subscript_expr(tree.left, False, True)

        elif store_target is None:
            left: ast.TupleAST
            bc.add_bytecode(unpack_sequence, len(left.items), left.ln)
            
            for item in left.items[::-1]:
                store_target = type_map[type(item)]

                if store_target == store_var:
                    ni = self.__buffer.get_or_add_varname_index(item.value)
                    bc.add_bytecode(store_target, ni, tree.ln)
                    bc.add_bytecode(pop_top, 0, -1)

                elif store_target == store_attr:
                    ebc = self.__compile_member_access_expr(item, True)
                    bc += ebc
                    bc.add_bytecode(pop_top, 0, -1)

                elif store_target == store_subscr:
                    bc += self.__compile_subscript_expr(item, False, True)
                    bc.add_bytecode(pop_top, 0, -1)

            return bc

        if single:
            bc.add_bytecode(pop_top, 0, tree.ln)

        return bc

    def __compile_assign_expr0(self, tree: ast.DefineExprAST, single=False) -> ByteCode:
        bc = ByteCode()

        ni = self.__buffer.get_or_add_varname_index(tree.name)
        expc = self.__compile_binary_expr(tree.value)

        bc += expc
        bc.add_bytecode(store_var, ni, tree.ln)

        if single:
            bc.add_bytecode(pop_top, 0, tree.ln)

        return bc

    def __compile_call_expr(self, tree: ast.CallExprAST, is_attr=False, 
                            plain_call=False) -> ByteCode:
        bc = ByteCode()

        lbc = self.__compile_binary_expr(tree.left, is_attr=is_attr)

        bc += lbc
        bc += self.__compile_func_call_arg_list(tree.arg_list)
        
        ex_call = False

        for item in tree.arg_list.arg_list:
            if item.star:
                ex_call = True
                break
        
        if ex_call:
            bc.add_bytecode(call_func_ex, 0, tree.ln)
        else:
            bc.add_bytecode(call_func, len(tree.arg_list.arg_list), tree.ln)

        if plain_call and not self.__is_single_line:
            bc.add_bytecode(pop_top, 0, -1)

        return bc

    def __compile_subscript_expr(self, tree: ast.SubscriptExprAST,
                                 is_attr=False, store=False) -> ByteCode:
        bc = ByteCode()

        lc = self.__compile_binary_expr(tree.left, is_attr=is_attr)
        ec = self.__compile_binary_expr(tree.expr)

        bc += lc
        bc += ec

        bc.add_bytecode(binary_subscr if not store else store_subscr, 0, tree.ln)

        return bc

    def __compile_array_expr(self, tree: ast.ArrayAST) -> ByteCode:
        bc = ByteCode()

        items = tree.items

        for et in items.item_list:
            etc = self.__compile_binary_expr(et)
            bc += etc

        bc.add_bytecode(build_array, len(items.item_list), tree.ln)

        return bc

    def __compile_map_expr(self, tree: ast.MapAST) -> ByteCode:
        bc = ByteCode()

        keys = tree.keys
        values = tree.values

        const_key = False
        
        # check keys whether is a const key
        for key in keys:
            if isinstance(key, ast.CellAST) and \
                    (key.type == AIL_NUMBER or key.type == AIL_STRING):
                continue
            break
        else:
            const_key = True

        if const_key:
            key_list = [key.value if key.type == AIL_STRING else eval(key.value)
                        for key in keys]

            for vt in values[::-1]:
                vtc = self.__compile_binary_expr(vt)
                bc += vtc
            list_index = self.__buffer.add_const(key_list)
            bc.add_bytecode(load_const, list_index, -1)
            bc.add_bytecode(build_const_key_map, len(keys), tree.ln)

            return bc

        for kt, vt in zip(keys[::-1], values[::-1]):
            ktc = self.__compile_binary_expr(kt)
            vtc = self.__compile_binary_expr(vt)
            bc += ktc
            bc += vtc

        bc.add_bytecode(build_map, len(keys), tree.ln)

        return bc

    def __compile_print_expr(self, tree: ast.PrintStmtAST) -> ByteCode:
        bc = ByteCode()

        expl = tree.value_list

        for et in expl:
            etc = self.__compile_binary_expr(et)
            bc += etc

        bc.add_bytecode(print_value, len(expl), tree.ln)

        return bc

    def __compile_input_expr(self, tree: ast.InputStmtAST) -> ByteCode:
        bc = ByteCode()

        expc = self.__compile_binary_expr(tree.msg)
        bc += expc

        vl = tree.value_list.value_list

        for name in vl:
            ni = self.__buffer.get_or_add_varname_index(name)
            bc.add_bytecode(load_varname, ni, tree.value_list.ln)

        bc.add_bytecode(input_value, len(vl), tree.ln)

        return bc

    def __compile_try_catch_expr(self, tree: ast.TryCatchStmtAST, extofs: int = 0):
        # structure of try-catch-finally block:
        # ? setup_finally:  $finally block  (has finally)   +
        # ? setup_try:      $catch block    (has catch)     +
        #
        #   [real_try_block]
        #   pop_try                         (has catch)     +
        #
        # ? jump_absolute:  $over catch     (has catch)     +
        #   
        # > catch block:                    (has catch)
        # 
        #   setup_catch:    $name_index                     +
        #   [real_catch_block]
        #   pop_catch                                       +
        #
        # ? push_none                       (has finally)   +
        #   pop_finally                     (has_finally)   +
        #
        # > finally block:                  (has finally)
        #
        #   [real_finally_block]
        #   end_finally                                     +

        bc = ByteCode()
        clbc = ByteCode()

        has_finally = len(tree.finally_block.stmts) > 0
        has_catch = len(tree.catch_block.stmts) > 0
        if not has_finally:
            assert has_catch  # otherwise, this try block is meaningless.

        head_extofs = extofs + \
                      BYTE_CODE_SIZE * (int(has_finally) + int(has_catch))

        try_block_extofs = head_extofs

        name_index = self.__buffer.get_or_add_varname_index(tree.name)

        try_bc = self.__compile_block(tree.try_block, try_block_extofs)
        catch_bc = ByteCode()
        finally_bc = ByteCode()

        catch_block_extofs = head_extofs + \
                             len(try_bc.blist) + \
                             BYTE_CODE_SIZE * (
                                int(has_catch)    # jump_absolute $over catch
                             ) * 2 + \
                             BYTE_CODE_SIZE  # setup_catch

        if has_catch:
            catch_bc = self.__compile_block(tree.catch_block, catch_block_extofs)
        else:
            catch_block_extofs -= BYTE_CODE_SIZE  # -setup_catch

        finally_block_extofs = catch_block_extofs + (
            BYTE_CODE_SIZE * 2 if has_finally else 0)
        # push_none and pop_finally
        if has_catch:
            finally_block_extofs += len(catch_bc.blist) + \
                                    BYTE_CODE_SIZE  # pop_catch

        if has_finally:
            finally_bc = self.__compile_block(
                    tree.finally_block, finally_block_extofs)
        
        whole_extofs = finally_block_extofs + len(finally_bc.blist) + \
                       BYTE_CODE_SIZE  # pop_finally

        # build block bytecode
        
        to_finally = finally_block_extofs - BYTE_CODE_SIZE  # -pop_finally
        jump_to_finally = finally_block_extofs - (
                          (BYTE_CODE_SIZE * 2) if has_finally else 0 )
                          # push_none and pop_finally
        to_catch = catch_block_extofs - BYTE_CODE_SIZE  # setup_catch
        
        if has_finally:
            bc.add_bytecode(setup_finally, to_finally, -1)
        if has_catch:
            bc.add_bytecode(setup_try, to_catch, -1)

        bc += try_bc 

        if has_catch:
            bc.add_bytecode(pop_try, 0, -1)
            bc.add_bytecode(jump_absolute, jump_to_finally, -1)

            bc.add_bytecode(setup_catch, name_index, -1)
            bc += catch_bc
            bc.add_bytecode(pop_catch, 0, -1)

        if has_finally:
            bc.add_bytecode(push_none, 0, -1)
            bc.add_bytecode(pop_finally, 0, -1)
            bc += finally_bc
            bc.add_bytecode(end_finally, 0, -1)

        return bc

    def __compile_try_catch_expr0(self,
                                  tree: ast.TryCatchStmtAST, extofs: int = 0):
        bc = ByteCode()
        clbc = ByteCode()  # clean err variable

        has_finally = len(tree.finally_block.stmts) > 0
        has_catch = len(tree.catch_block.stmts) > 0
        extofs += BYTE_CODE_SIZE * (2 if has_finally else 1)  # for setup_try

        ni = self.__buffer.get_or_add_varname_index(tree.name)

        tbc = self.__compile_block(tree.try_block, extofs)

        vi = self.__buffer.add_const(0)
        clbc.add_bytecode(load_const, vi, -1)
        clbc.add_bytecode(store_var, ni, -1)
        clbc.add_bytecode(delete_var, ni, -1)

        cat_ext = extofs + len(tbc.blist) + len(clbc.blist) + BYTE_CODE_SIZE * 3
        # for setup_catch and jump_absolute
        cabc = self.__compile_block(tree.catch_block, cat_ext)

        jump_over = cat_ext + len(cabc.blist) + BYTE_CODE_SIZE * 3
        # for pop_catch load_const, and pop_finally (if it has)
        to_catch = extofs + len(tbc.blist) + BYTE_CODE_SIZE * (
                3 if has_finally else 2) 
        # for load_const (if necessary), jump_absolute and setup_try

        if has_finally:
            fnbc = self.__compile_block(tree.finally_block, jump_over)
        else:
            fnbc = ByteCode()

        if has_finally:
            bc.add_bytecode(setup_finally, fn_ext, tree.ln)

        if has_catch:
            bc.add_bytecode(setup_try, to_catch, tree.ln)
            bc += tbc
            bc.add_bytecode(pop_try, 0, -1)

        if has_finally:
            bc.add_bytecode(load_const, self.__buffer.add_const(null), -1)
        
        if has_catch:
            bc.add_bytecode(jump_absolute, jump_over, -1)
            bc.add_bytecode(setup_catch, ni, -1)
            bc += cabc
            bc += clbc
            bc.add_bytecode(pop_catch, 0, -1)
        
        if has_finally:
            bc.add_bytecode(pop_finally, 0, -1)

        bc += fnbc

        return bc

    def __compile_comp_expr(self, tree: ast.CmpTestAST, extofs: int = 0) -> ByteCode:
        bc = ByteCode()

        # left
        if isinstance(tree, ast.CellAST):
            s, i = self.__do_cell_ast(tree)

            bc.add_bytecode(load_const if s == 0 else load_variable, i, tree.ln)

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
            bc.add_bytecode(compare_op, opi, et.ln)

        return bc

    def __compile_not_test_expr(self, tree: ast.NotTestAST, extofs: int = 0):
        bc = ByteCode()

        if isinstance(tree, ast.NotTestAST):
            bce = self.__compile_comp_expr(tree.expr, extofs)
            bc += bce
            bc.add_bytecode(binary_not, 0, tree.ln)

            return bc
        return self.__compile_comp_expr(tree, extofs)

    def __compile_or_expr(self, tree: ast.AndTestAST, extofs: int = 0) -> ByteCode:
        """
        extofs : 当 and 不成立约过的除右部以外的字节码偏移量
                 当为 0 时，则不处理extofs
        """
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

        r_ext = len(lbc.blist) + BYTE_CODE_SIZE

        for rt in tree.right:
            tbc = self.__compile_and_expr(rt, r_ext)
            rbcl.append(tbc)

        bc += lbc

        for jopc in range(1, len(rbcl) + 1):
            rbc = rbcl.pop(0)
            last_ofs = sum([len(x.blist) for x in rbcl]) + len(rbc.blist) + \
                       BYTE_CODE_SIZE * (len(rbcl) + 1)
            bc.add_bytecode(jump_forward_true_or_pop, last_ofs, -1)
            bc += rbc

        return bc

    def __compile_and_expr(self, tree: ast.AndTestAST, extofs: int = 0, with_or=False) -> ByteCode:
        """
        extofs : 当 and 不成立约过的除右部以外的字节码偏移量
                 当为 0 时，则不处理extofs
        """

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

        r_ext = len(lbc.blist) + BYTE_CODE_SIZE

        for rt in tree.right:
            tbc = self.__compile_not_test_expr(rt, r_ext)
            rbcl.append(tbc)

        bc += lbc

        for jopc in range(1, len(rbcl) + 1):
            rbc = rbcl.pop(0)
            last_ofs = sum([len(x.blist) for x in rbcl]) + len(rbc.blist) + \
                       BYTE_CODE_SIZE * (len(rbcl) + 1)
            bc.add_bytecode(jump_forward_if_false_or_pop, last_ofs, -1)
            bc += rbc

        return bc

    def __compile_test_expr(self, tree: ast.TestExprAST, extofs: int = 0) -> ByteCode:
        bc = ByteCode()

        if type(tree) in ast.BINARY_AST_TYPES and type(tree) != ast.TestExprAST:
            return self.__compile_binary_expr(tree)

        test = tree.test
        
        if isinstance(test, ast.CmpTestAST):
            return self.__compile_comp_expr(test, extofs)
        else:
            return self.__compile_or_expr(test, extofs)

    def __compile_while_stmt(self, tree: ast.WhileStmtAST, extofs: int):
        bc = ByteCode()
        extofs += BYTE_CODE_SIZE

        b = tree.block

        tc = self.__compile_test_expr(tree.test, extofs)

        bcc = self.__compile_block(b, len(tc.blist) + extofs + BYTE_CODE_SIZE)
        # _byte_code_size for 'setup_while'

        jump_over = extofs + len(bcc.blist) + BYTE_CODE_SIZE * 2
        # three times of _byte_code_size means (
        #   jump over setup_while, jump over block, jump over jump_absolute)

        tc = self.__compile_test_expr(tree.test, jump_over)
        # compile again. first time for the length of test opcodes
        # second time for jump offset

        back = extofs  # move to first opcode in block
        to = len(bcc.blist) + extofs + len(tc.blist) + BYTE_CODE_SIZE * 2
        # including setup_while and jump over block

        bc.add_bytecode(setup_while, to + BYTE_CODE_SIZE, -1)
        # jump over clean_loop
        bc += tc
        bc.add_bytecode(pop_jump_if_false_or_pop, to, -1)

        bc += bcc
        bc.add_bytecode(jump_absolute, back, -1)
        bc.add_bytecode(pop_loop, 0, -1)

        return bc

    def __compile_do_loop_stmt(self, tree: ast.DoLoopStmtAST, extofs: int):
        bc = ByteCode()

        tc = self.__compile_test_expr(tree.test, 0)  # first compile

        loopb_ext = extofs + BYTE_CODE_SIZE  # setup_do_loop

        bcc = self.__compile_block(tree.block, loopb_ext)

        jump_over = len(bcc.blist) + len(tc.blist) + extofs + BYTE_CODE_SIZE * 4

        bc.add_bytecode(setup_doloop, jump_over + BYTE_CODE_SIZE, -1)  # jump over clean_loop

        test_jump = extofs + len(bcc.blist)

        tc = self.__compile_test_expr(tree.test, test_jump)
 
        jump_back = extofs + BYTE_CODE_SIZE * 2  # over setup_doloop and jump_forward
        bc.add_bytecode(jump_forward, len(tc.blist) + BYTE_CODE_SIZE * 2, -1)
        bc += tc
        bc.add_bytecode(pop_jump_if_true_or_pop, jump_over, -1)
        bc += bcc
        bc.add_bytecode(jump_absolute, jump_back, -1)

        bc.add_bytecode(pop_loop, 0, -1)

        return bc

    def __compile_for_stmt(self, tree: ast.ForStmtAST, extofs: int):
        bc = ByteCode()

        extofs += BYTE_CODE_SIZE  # for init_for

        initbc = ByteCode()

        for et in tree.init_list.expr_list:
            initbc += self.__compile_assign_expr(et, single=True)

        updbc = ByteCode()

        for et in tree.update_list.expr_list:
            updbc += self.__compile_binary_expr(et, is_single=True)

        test_ext = extofs + len(initbc.blist) + len(updbc.blist) + BYTE_CODE_SIZE
        # _byte_code_size for jump_forward

        jump_back = test_ext - len(updbc.blist)

        if tree.test is not None:
            tbc = self.__compile_test_expr(tree.test, test_ext)
        else:
            tbc = ByteCode()
            tbc.add_bytecode(load_const, self.__buffer.add_const(True), tree.ln)

        block_ext = extofs + len(tbc.blist) + \
                    len(initbc.blist) + \
                    len(updbc.blist) + BYTE_CODE_SIZE * 2
        # _byte_code_size is for jump_if_false_or_pop, setup_for and jump_forward

        blc = self.__compile_block(tree.block, block_ext)

        jump_over = block_ext + len(blc.blist) + BYTE_CODE_SIZE

        bc.add_bytecode(setup_for, jump_over + BYTE_CODE_SIZE, -1)
        # jump over clean_loop
        bc += initbc
        bc.add_bytecode(jump_forward, len(updbc.blist) + BYTE_CODE_SIZE, -1)
        bc += updbc
        bc += tbc
        bc.add_bytecode(pop_jump_if_false_or_pop, jump_over, -1)
        bc += blc
        bc.add_bytecode(jump_absolute, jump_back, -1)
        bc.add_bytecode(pop_for, 0, -1)

        return bc

    def __compile_if_else_stmt(self, tree: ast.IfStmtAST, extofs: int):
        bc = ByteCode()

        has_else = len(tree.else_block.stmts) > 0

        tc = self.__compile_test_expr(tree.test, extofs)

        ifbc_ext = extofs + len(tc.blist) + BYTE_CODE_SIZE  # jump_if_false_or_pop

        ifbc = self.__compile_block(tree.block, ifbc_ext)

        jump_over_ifb = len(ifbc.blist) + len(tc.blist) + extofs + BYTE_CODE_SIZE + \
                        (BYTE_CODE_SIZE if has_else else 0)  # jump_absolute if has else

        if has_else:
            elbc = self.__compile_block(tree.else_block, jump_over_ifb)
        else:
            elbc = ByteCode()

        # 如果拥有 if 则条件为false时跳到else块

        jump_over = extofs + len(tc.blist) + len(ifbc.blist) \
                    + len(elbc.blist) + BYTE_CODE_SIZE * (2
                                                           if has_else
                                                           else 1)  # + _BYTE_CODE_SIZE
        # include 'jump_absolute' at the end of ifbc
        # last _byte_code_size is for 'jump_if_false_or_pop'

        if has_else:
            ifbc.add_bytecode(jump_absolute, jump_over, -1)

        test_jump = len(tc.blist) + len(ifbc.blist) + extofs + BYTE_CODE_SIZE
        # 不需要加elbc的长度

        # tc = self.__compile_test_expr(tree.test, test_jump)
        tc.add_bytecode(pop_jump_if_false_or_pop, test_jump, -1)

        bc += tc
        bc += ifbc
        bc += elbc

        return bc

    def __compile_return_expr(self, tree: ast.ReturnStmtAST) -> ByteCode:
        bc = ByteCode()
        bce = self.__compile_binary_expr(tree.expr)

        bc += bce
        bc.add_bytecode(return_value, 0, -1)

        return bc

    def __compile_break_expr(self, tree: ast.BreakStmtAST) -> ByteCode:
        bc = ByteCode()
        bc.add_bytecode(break_loop, 0, tree.ln)

        return bc

    def __compile_continue_expr(self, tree: ast.ContinueStmtAST) -> ByteCode:
        bc = ByteCode()
        bc.add_bytecode(continue_loop, 0, tree.ln)

        return bc

    def __compile_global_stmt(self, tree: ast.GlobalStmtAST) -> ByteCode:
        self.__buffer.global_names.add(tree.name)
        return ByteCode()  # empty

    def __compile_nonlocal_stmt(self, tree: ast.NonlocalStmtAST) -> ByteCode:
        self.__buffer.nonlocal_names.add(tree.name)
        return ByteCode()  # empty

    def __compile_assert_expr(self, tree: ast.AssertStmtAST, extofs: int) -> ByteCode:
        bc = ByteCode()

        ec = self.__compile_test_expr(tree.expr, extofs)
        ci = self.__buffer.add_const('AssertionError')

        jump = len(ec.blist) + BYTE_CODE_SIZE * 3

        bc += ec

        bc.add_bytecode(jump_forward_true_or_pop, jump, -1)
        bc.add_bytecode(load_const, ci, -1)
        bc.add_bytecode(throw_error, 0, tree.ln)

        return bc

    def __compile_throw_expr(self, tree: ast.ThrowStmtAST) -> ByteCode:
        bc = ByteCode()

        if tree.expr is None:
            bc.add_bytecode(push_none, 0, -1)

        else:
            ec = self.__compile_binary_expr(tree.expr)
            bc += ec
            
        bc.add_bytecode(throw_error, 0, tree.ln)

        return bc

    def __compile_load_stmt(self, tree: ast.LoadStmtAST) -> ByteCode:
        bc = ByteCode()

        ni = self.__buffer.add_const(tree.path)

        bc.add_bytecode(load_module, ni, tree.ln)

        return bc

    def __compile_import_stmt(self, tree: ast.ImportStmtAST) -> ByteCode:
        bc = ByteCode()
        ln = tree.ln

        nsi = self.__buffer.add_const(tree.path)
        ni = self.__buffer.get_or_add_varname_index(tree.name)

        bc.add_bytecode(import_name, nsi, ln)

        if len(tree.members) == 0:
            bc.add_bytecode(store_var, ni, ln)
            bc.add_bytecode(pop_top, 0, ln)  
            # pop top of stack after store_var
        else:  # likes from ... import ...
            for name in tree.members:
                mni = self.__buffer.get_or_add_varname_index(name)
                bc.add_bytecode(import_from, mni, ln)
                bc.add_bytecode(store_var, mni, ln)
                bc.add_bytecode(pop_top, 0, -1)
            bc.add_bytecode(pop_top, 0, -1)  # pop module object 

        return bc

    def __compile_function(
            self, 
            tree: ast.FunctionDefineAST, 
            anonymous_function: bool = False,
            just_make: bool = False,
            doc_string: str = '') -> ByteCode:
        bc = ByteCode()

        signature = _make_function_signature(tree)

        has_bindto = tree.bindto is not None

        ext = [c.expr.value for c in tree.arg_list.arg_list]
        exp_list = tree.arg_list.arg_list
        var_arg = exp_list[-1].expr.value \
                    if exp_list and exp_list[-1].star else None
        argc = len(exp_list) - (0 if var_arg is None else 1)
 
        name = tree.name

        if self.__mode == COMPILER_MODE_FUNC:
            name = '%s.%s' % (self.__name, tree.name)

        cobj = Compiler(mode=COMPILER_MODE_FUNC, 
                        filename=self.__filename, name=name,
                        ext_varname=ext).compile(tree.block).code_object
        cobj.argcount = argc
        cobj.var_arg = var_arg
        cobj._function_signature = signature

        if doc_string != '':
            cobj.doc_string = doc_string
        else:
            cobj.doc_string = tree.doc_str

        if self.__mode == COMPILER_MODE_FUNC:
            cobj.closure = True

        ci = self.__buffer.add_const(cobj)
        if anonymous_function:
            bc.add_bytecode(load_const, ci, -1)
            bc.add_bytecode(make_function, 0, -1)
            return bc

        namei = self.__buffer.get_or_add_varname_index(tree.name)

        bindtoi = self.__buffer.get_or_add_varname_index(tree.bindto) \
            if has_bindto else 0

        if tree.decorator:
            # make decorator call
            # compile decorator ast to:
            # 
            # @decorator
            # fun f() {...} -> fun f() {...} ; f = decorator(f)
            for dec in tree.decorator:
                decorator_access_ast = self.__compile_binary_expr(dec)
                bc += decorator_access_ast

            bc.add_bytecode(load_const, ci, tree.ln)
            bc.add_bytecode(make_function, 0, tree.ln)

            for _ in tree.decorator:
                bc.add_bytecode(call_func, 1, tree.ln)
        else:
            bc.add_bytecode(load_const, ci, tree.ln)
            bc.add_bytecode(make_function, 0, tree.ln)

        if has_bindto:
            bc.add_bytecode(load_varname, namei, tree.ln)
            bc.add_bytecode(bind_function, bindtoi, tree.ln)
        elif not just_make:
            bc.add_bytecode(store_var, namei, tree.ln)
            bc.add_bytecode(pop_top, 0, -1)
        
        return bc

    def __compile_func_call_arg_list(self, tree: ast.ArgListAST) -> ByteCode:
        bc = ByteCode()
        
        norm_arg_count = 0
        join_count = 0
        var_arg = False

        for item in tree.arg_list:
            if item.star:
                if norm_arg_count > 0:
                    bc.add_bytecode(build_array, norm_arg_count, -1)
                    norm_arg_count = 0
                    join_count += 1
                join_count += 1
                var_arg = True

            ibc = self.__compile_binary_expr(item.expr)
            bc += ibc

            if not item.star:
                norm_arg_count += 1

        if var_arg:
            if norm_arg_count > 0:
                bc.add_bytecode(build_array, norm_arg_count, -1)
                join_count += 1

            bc.add_bytecode(join_array, join_count, tree.ln)

        return bc

    def __compile_struct(self, tree: ast.StructDefineAST) -> ByteCode:
        bc = ByteCode()

        plist = tree.protected_list

        for n in tree.name_list:
            ni = self.__buffer.get_or_add_varname_index(n)
            bc.add_bytecode(load_varname, ni, tree.ln)
            if n in plist:
                bc.add_bytecode(set_protected, 0, tree.ln)

        ni = self.__buffer.get_or_add_varname_index(tree.name)

        bc.add_bytecode(load_varname, ni, tree.ln)
        bc.add_bytecode(store_struct, len(tree.name_list) + len(plist), tree.ln)

        return bc

    def __compile_class(self, tree: ast.ClassDefineAST) -> ByteCode:
        """
        structure of class definition:
          load_const               (code object of class define function)
          make_function 

          load_const               (class name)
        
        [has base(s)]
         *codes for bases expr     (bases)
        [else]
         ** nothing **

        """
        bc = ByteCode()
        
        func_bc = self.__compile_function(
            tree.func, just_make=True, doc_string=tree.doc_str)

        name_const_index = self.__buffer.add_const(tree.name)
        name_var_index = self.__buffer.get_or_add_varname_index(tree.name)

        bc += func_bc
        bc.add_bytecode(load_const, name_const_index, tree.ln)

        popc = 2 + len(tree.bases)  # class func, class name [, *bases]

        for base in tree.bases:
            bc += self.__compile_binary_expr(base)

        bc.add_bytecode(build_class, popc, tree.ln)
        bc.add_bytecode(store_var, name_var_index, tree.ln)
        bc.add_bytecode(pop_top, 0, -1)

        return bc

    def __compile_block(self, tree: ast.BlockAST, firstoffset=0) -> ByteCode:
        bc = self.__general_bytecode = ByteCode()
        last_ln = 0
        total_offset = firstoffset
        et = None

        for eti in range(len(tree.stmts)):
            et = tree.stmts[eti]

            # self.__lnotab.mark(et.ln, total_offset)

            if isinstance(et, ast.InputStmtAST):
                tbc = self.__compile_input_expr(et)

            elif isinstance(et, ast.PrintStmtAST):
                tbc = self.__compile_print_expr(et)

            elif isinstance(et, ast.DefineExprAST):
                tbc = self.__compile_assign_expr(et, single=True)

            elif isinstance(et, ast.IfStmtAST):
                tbc = self.__compile_if_else_stmt(et, total_offset)

            elif isinstance(et, ast.WhileStmtAST):
                tbc = self.__compile_while_stmt(et, total_offset)

            elif isinstance(et, ast.DoLoopStmtAST):
                tbc = self.__compile_do_loop_stmt(et, total_offset)

            elif isinstance(et, ast.FunctionDefineAST):
                tbc = self.__compile_function(et)

            elif isinstance(et, ast.ReturnStmtAST):
                tbc = self.__compile_return_expr(et)

            elif isinstance(et, ast.BreakStmtAST):
                tbc = self.__compile_break_expr(et)

            elif isinstance(et, ast.ContinueStmtAST):
                tbc = self.__compile_continue_expr(et)

            elif isinstance(et, ast.CallExprAST):
                tbc = self.__compile_call_expr(et, plain_call=True)

            elif isinstance(et, ast.LoadStmtAST):
                tbc = self.__compile_load_stmt(et)

            elif isinstance(et, ast.AssignExprAST):
                tbc = self.__compile_assign_expr(et, True)

            elif isinstance(et, ast.StructDefineAST):
                tbc = self.__compile_struct(et)

            elif isinstance(et, ast.ClassDefineAST):
                tbc = self.__compile_class(et)

            elif isinstance(et, ast.ForStmtAST):
                tbc = self.__compile_for_stmt(et, total_offset)

            elif isinstance(et, ast.AssertStmtAST):
                tbc = self.__compile_assert_expr(et, total_offset)

            elif isinstance(et, ast.ThrowStmtAST):
                tbc = self.__compile_throw_expr(et)

            elif isinstance(et, ast.TryCatchStmtAST):
                tbc = self.__compile_try_catch_expr(et, total_offset)

            elif isinstance(et, ast.ImportStmtAST):
                tbc = self.__compile_import_stmt(et)

            elif isinstance(et, ast.GlobalStmtAST):
                tbc = self.__compile_global_stmt(et)

            elif isinstance(et, ast.NonlocalStmtAST):
                tbc = self.__compile_nonlocal_stmt(et)

            elif isinstance(et, ast.UnaryExprAST):
                tbc = self.__compile_unary_expr(et, single=True)

            elif type(et) in ast.BINARY_AST_TYPES:
                tbc = self.__compile_binary_expr(et, is_single=True)

                if not self.__is_single_line:
                    tbc.add_bytecode(pop_top, 0, -1)

            else:
                print('W: Unknown AST type: %s' % type(et))

            total_offset += len(tbc.blist)

            if eti + 1 < len(tree.stmts):
                # self.__lnotab.update(tree.stmts[eti + 1].ln, total_offset)
                pass

            bc += tbc
        else:
            if et:
                # self.__lnotab.update(et.ln + 1, total_offset)
                pass

        return bc

    def __make_final_return(self) -> ByteCode:
        bc = ByteCode()

        if self.__is_single_line:
            return bc

        ni = self.__buffer.add_const(null)

        bc.add_bytecode(load_const, ni, -1)
        bc.add_bytecode(return_value, 0, -1)

        return bc

    def compile(self, astree: ast.BlockAST, single_line=False) -> ByteCodeFileBuffer:
        raise error.AILVersionError('AIL native mode no longer supported in AIL 2.x or later')

        self.__init__(self.__mode, self.__filename, self.__ext_varname, self.__name)
        self.__is_single_line = single_line

        self.__lnotab.firstlineno = astree.stmts[0].ln \
            if isinstance(astree, ast.BlockAST) and astree.stmts \
            else 1

        tbc = self.__compile_block(astree)

        # if tbc.blist and tbc.blist[-2] != return_value:
        tbc += self.__make_final_return()

        self.__buffer.bytecodes = tbc
        self.__buffer.first_lineno = astree.ln
        self.__buffer.lineno_list = tbc.lineno_list

        return self.__buffer

    def __test(self, tree) -> ByteCodeFileBuffer:
        bc = self.__compile_block(tree, 0)

        if bc.blist[-2] != return_value:
            bc += self.__make_final_return()
        self.__buffer.bytecodes = bc

        return self.__buffer


def convert_numeric_str_to_number(value: str) -> Union[int, float]:
    """
    将一个或许是数字型字符串转换成数字

    return : eval(value)    若value是数字型字符串
    return : None           若value不是数字型字符串
    """
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

    source = open('./tests/test.ail').read()

    lex = Lex()
    ts = lex.lex(source)

    p = Parser()
    t = p.parse(ts, source, '<test>')

    c = Compiler(t)
    bf = c.compile(t)

    test_utils.show_bytecode(bf)


if __name__ == '__main__':
    test_compiler()
