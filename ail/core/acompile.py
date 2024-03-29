from ast import literal_eval
from typing import List, Tuple, Dict, Union
from types import CodeType

from . import asts as ast
from .pyopcode import *

from .tokentype import AIL_IDENTIFIER, AIL_NUMBER, AIL_STRING

from .symbol import (
    SymbolTable, FunctionSymbolTable, ClassSymbolTable, SymbolAnalyzer, Symbol,
    SYM_LOCAL, SYM_GLOBAL, SYM_NONLOCAL, SYM_FREE, SYM_NORMAL,
    do_mangle
)

CTX_LOAD = 0x1
CTX_STORE = 0x2

COMPILE_FLAG_GLOBAL = 0x1
COMPILE_FLAG_FUNC = 0x2

BIN_OP_MAP = {
    '+': BINARY_ADD,
    '-': BINARY_SUBTRACT,
    '*': BINARY_MULTIPLY,
    '/': BINARY_TRUE_DIVIDE,
    'mod': BINARY_MODULO,
    '//': BINARY_FLOOR_DIVIDE,
    '^': BINARY_XOR,
    '|': BINARY_OR,
    '&': BINARY_AND,
    '**': BINARY_POWER,
    '<<': BINARY_LSHIFT,
    '>>': BINARY_RSHIFT,
}

CMP_OP_MAP = {
    '<': 0,
    '<=': 1,
    '==': 2,
    '!=': 3,
    '>': 4,
    '>=': 5,
    'in': 6,
    'not in': 7,
    'is': 8,
    'is not': 9,
    'exception match': 10,
    'BAD': 11,
}

CO_OPTIMIZED = 0x0001
CO_NEWLOCALS = 0x0002
CO_VARARGS = 0x0004
CO_VARKEYWORDS = 0x0008
CO_NESTED = 0x0010
CO_GENERATOR = 0x0020
CO_NOFREE = 0x0040
CO_COROUTINE = 0x0080
CO_ITERABLE_COROUTINE = 0x0100
CO_ASYNC_GENERATOR = 0x0200

CO_FUTURE_DIVISION = 0x20000
CO_FUTURE_ABSOLUTE_IMPORT = 0x40000
CO_FUTURE_WITH_STATEMENT = 0x80000
CO_FUTURE_PRINT_FUNCTION = 0x100000
CO_FUTURE_UNICODE_LITERALS = 0x200000
CO_FUTURE_BARRY_AS_BDFL = 0x400000
CO_FUTURE_GENERATOR_STOP = 0x800000
CO_FUTURE_ANNOTATIONS = 0x1000000

FB_WHILE_LOOP = 1
FB_FOREACH_LOOP = 2
FB_FINALLY_END = 3
FB_FINALLY_TRY_WITH_BREAK = 4
FB_FINALLY_TRY = 5
FB_EXCEPT = 6
FB_HANDLER_FINISH = 7
FB_FOR_LOOP = 8
FB_WITH = 9


def _new_cell_fast(value: str, _type: int, ln: int, scope: int):
    return ast.CellAST(value, _type, ln, Symbol(value, scope))


class CompilerError(Exception):
    pass


class CodeObjectBuffer:
    def __init__(self, firstlineno=1):
        self.argcount = 0
        self.posonlyargcount = 0
        self.kwonlyargcount = 0
        self.nlocals = 0
        self.stacksize = 0
        self.flags = 0
        self.code = []
        self.constants = []
        self.names = []
        self.varnames = []
        self.filename = '<unknown>'
        self.name = '<unknown>'
        self.firstlineno = firstlineno
        self.lnotab = []
        self.freevars = []
        self.cellvars = []

        self.__real_time_stack_size = 0
        self.__now_line = firstlineno
        self.__code_increase = 0

    def _check_lno(self, line, increase=2):
        if self.__now_line != line:
            self.lnotab.extend((self.__code_increase, line - self.__now_line))
            self.__now_line = line
            self.__code_increase = 0
        self.__code_increase += increase

    def add_varname(self, name: str) -> int:
        if name in self.varnames:
            return self.varnames.index(name)
        self.varnames.append(name)
        return len(self.varnames) - 1

    def add_const(self, const: object) -> int:
        if const in self.constants:
            return self.constants.index(const)
        self.constants.append(const)
        return len(self.constants) - 1

    def __append_bytecode(self, instr, arg, stack_effect=None):
        effect = OPCODE_STACK_EFFECT.get(instr, 0)

        if stack_effect is EFCT_DYNAMIC_EFFECT and stack_effect is None:
            raise CompilerError('dynamic stack effect must be provided explicitly')

        if stack_effect is not None:
            effect = stack_effect

        self.__real_time_stack_size += effect
        if self.__real_time_stack_size > self.stacksize:
            self.stacksize = self.__real_time_stack_size

        self.code.extend((instr, arg))

    def add_bytecode(self, instr, arg, line: int, stack_effect=None) -> int:
        """
        :return: the size of appended bytecode
        """
        # check extend arg
        size = 0
        if arg > 255:
            self.__append_bytecode(EXTENDED_ARG, arg >> 8)
            size += 2
            arg &= 0xff

        self.code.append(instr)
        self.code.append(arg)
        size += 2

        self._check_lno(line, size)

        return size


class CompilerState:
    def __init__(self):
        self.block_stack: List = []
        self.cobj_buffer: CodeObjectBuffer = None


class Instruction:
    def __init__(self,
                 opcode=0, arg=0,
                 is_jabs=False, is_jrel=False, target=None,
                 line=-1):
        self.opcode = opcode
        self.arg = arg

        self.is_jabs = is_jabs
        self.is_jrel = is_jrel
        self.target: 'BasicBlock' = target

        self.stack_effect: int = 0

        self.line = line

    def __str__(self):
        if self.target is not None:
            return '<instr %s arg = %s target: %s>' % \
                   (OPCODE_TO_NAME_MAP[self.opcode], self.arg, self.target)
        return '<instr %s arg = %s>' % \
               (OPCODE_TO_NAME_MAP[self.opcode], self.arg)


class BasicBlock:
    def __init__(self):
        self.instructions: List[Instruction] = []
        self.next_block: 'BasicBlock' = None
        self.offset: int = -1

    def add_instruction(self, instr: Instruction) -> int:
        self.instructions.append(instr)
        return len(self.instructions) - 1

    def __str__(self):
        return '<BasicBlock %s>' % hex(id(self))

    __repr__ = __str__


class FrameBlock:
    def __init__(
            self, type_: int,
            start: BasicBlock, next_: BasicBlock, exit_: BasicBlock = None):
        self.type = type_
        self.start = start
        self.next = next_
        self.exit = exit_  # optional


class CompileUnit:
    def __init__(self):
        self.top_block: BasicBlock = None
        self.block: BasicBlock = None
        self.scope: SymbolTable = None

        self.filename: str = '<unknown>'
        self.name: str = '<unknown>'
        self.varnames: List[str] = []
        self.consts: List[object] = []
        self.names: List[str] = []
        self.freevars: Tuple[str] = ()
        self.cellvars: Tuple[str] = ()
        self.stack_size = 0
        self.argcount = 0
        self.posonlyargcount = 0
        self.kwonlyargcount = 0
        self.nlocals = 0
        self.flags = 0

        self.prev_unit: CompileUnit = None
        self.firstlineno: int = 1

        self.fb_stack: List[FrameBlock] = []

        self._cur_stack_size = 0

        self.annotations_setup = False


class Compiler:
    class __FrameStackManager:
        def __init__(self, compiler: 'Compiler', frame: FrameBlock):
            self._compiler = compiler
            self._frame = frame

        def __enter__(self):
            self._compiler.push_frame(self._frame)

        def __exit__(self, exc_type, exc_val, exc_tb):
            self._compiler.pop_frame()
            return False

    def __init__(self):
        self._unit: CompileUnit = None
        self._mode = ''

    @property
    def unit(self) -> CompileUnit:
        return self._unit

    def push_frame(self, frame: FrameBlock):
        self._unit.fb_stack.append(frame)

    def push_new_frame(self, type_: int,
                       start: BasicBlock, next_: BasicBlock, exit_: BasicBlock = None):
        self.push_frame(FrameBlock(type_, start, next_, exit_))

    def pop_frame(self) -> FrameBlock:
        return self._unit.fb_stack.pop()

    def _frame(self, frame: FrameBlock):
        return Compiler.__FrameStackManager(self, frame)

    def _do_mangle(self, name: str, check_global=True) -> str:
        cls = ''
        unit = self._unit

        if (name[:2] == '__' and name [-2:] == '__') or name[:2] != '__':
            return name

        while unit is not None:
            if isinstance(unit.scope, ClassSymbolTable):
                cls = unit.name
                break

            unit = unit.prev_unit
        else:
            return name

        # if check_global and (
        #     name in self._unit.scope.global_directives):
            
        #     return name

        return do_mangle(cls, name)

    def _check_oparg(self, arg: int, ln: int) -> int:
        final = arg & 0xff
        if arg >= 1 << 16:
            self._add_instruction(EXTENDED_ARG, arg >> 16, ln, False)
            self._add_instruction(EXTENDED_ARG, (arg >> 8) & 0xff, ln, False)
        elif arg >= 1 << 8:
            self._add_instruction(EXTENDED_ARG, arg >> 8, ln, False)
        return final

    def _get_stack_effect(self, op, stack_effect=None) -> int:
        if op in OPCODE_STACK_EFFECT:
            effect = OPCODE_STACK_EFFECT[op]
        else:
            effect = 0

        if effect is EFCT_DYNAMIC_EFFECT:
            if stack_effect is None:
                raise CompilerError(
                    'dynamic stack effect must be provided explicitly')
            else:
                effect = stack_effect

        return effect

    def _new_call_name(self, name: str, args: list, ln: int):
        # TODO: finish it.
        self._add_instruction(LOAD_GLOBAL, self._add_name(name), ln)
        for expr in args:
            self._compile(expr)
        self._add_instruction(
            CALL_FUNCTION, len(args), ln,
            stack_effect=-len(args)+1
        )

    def _add_instruction(
            self, op: int, arg: int, ln: int,
            check=True, stack_effect=None) -> int:
        """
        :returns: returns the offset from head of this instruction
        """

        if check:
            arg = self._check_oparg(arg, ln)

        instr = Instruction()
        instr.stack_effect = self._get_stack_effect(op, stack_effect)
        instr.line = ln
        instr.arg = arg
        instr.opcode = op

        return self._unit.block.add_instruction(instr)

    def _add_jump_op(self,
                     op: int, target: BasicBlock, ln: int, stack_effect=None):
        instr = Instruction()
        instr.is_jabs = op not in OPCODE_JUMP_REL
        instr.is_jrel = not instr.is_jabs
        instr.target = target
        instr.line = ln
        instr.arg = 0
        instr.opcode = op

        instr.stack_effect = self._get_stack_effect(op, stack_effect)
        self._unit.block.add_instruction(instr)

    def _add_const(self, const: object) -> int:
        if const in self._unit.consts:
            return self._unit.consts.index(const)
        self._unit.consts.append(const)
        return len(self._unit.consts) - 1

    def _add_varname(self, name: str) -> int:
        if name in self._unit.varnames:
            return self._unit.varnames.index(name)
        self._unit.varnames.append(name)
        return len(self._unit.varnames) - 1

    def _add_name(self, name: str) -> int:
        if name in self._unit.names:
            return self._unit.names.index(name)
        self._unit.names.append(name)
        return len(self._unit.names) - 1

    def _unwind_frame_block(self, block: FrameBlock, preserve_tos=False):
        if block.type == FB_FINALLY_END:
            block.exit = None
            self._add_instruction(POP_FINALLY, int(preserve_tos), -1)
            if preserve_tos:
                self._add_instruction(ROT_TWO, 0, -1)
            self._add_instruction(POP_TOP, 0, -1)

        elif block.type == FB_FINALLY_TRY_WITH_BREAK:
            self._add_instruction(POP_BLOCK, 0, -1)
            self._add_jump_op(CALL_FINALLY, block.exit, -1)
            self._add_instruction(POP_TOP, 0, -1)  # pop NULL

        elif block.type == FB_FINALLY_TRY:
            self._add_instruction(POP_BLOCK, 0, -1)
            self._add_jump_op(CALL_FINALLY, block.exit, -1)

        elif block.type == FB_EXCEPT:
            self._add_instruction(POP_BLOCK, 0, -1)

        elif block.type == FB_HANDLER_FINISH:
            self._add_instruction(POP_EXCEPT, 0, -1)

        elif block.type == FB_WITH:
            pass


    def _compile_build_tuple(self, elements: List[ast.Expression]) -> bool:
        all_constant = True

        for elt in elements:
            if not isinstance(elt, ast.CellAST) or elt.type == AIL_IDENTIFIER:
                break
        else:
            all_constant = True

        if all_constant:
            ci = self._add_const(tuple(
                (elt.value if elt.type == AIL_STRING else literal_eval(elt.value)
                    for elt in elements)
            ))
            self._add_instruction(LOAD_CONST, ci, -1)

        else:
            for elt in elements:
                self._compile(elt)
            self._add_instruction(
                BUILD_TUPLE, len(elements), -1, 
                stack_effect=-len(elements)+1
            )

    def _compile_const(self, cell: ast.CellAST):
        if cell.type == AIL_NUMBER:
            value = literal_eval(cell.value)
        else:
            value = cell.value
            assert isinstance(value, str)

        ci = self._add_const(value)
        self._add_instruction(LOAD_CONST, ci, cell.ln)

    def _compile_name(self, cell: ast.CellAST):
        name = cell.value
        ln = cell.ln
        symbol = cell.symbol

        if name in ('True', 'true'):
            ni = self._add_const(True)
            self._add_instruction(LOAD_CONST, ni, ln)
            return
        elif name in ('False', 'false'):
            ni = self._add_const(False)
            self._add_instruction(LOAD_CONST, ni, ln)
            return
        elif name in ('null', 'None'):
            ni = self._add_const(None)
            self._add_instruction(LOAD_CONST, ni, ln)
            return

        cellvar = name in self._unit.cellvars
        freevar = name in self._unit.freevars

        if not cellvar or not freevar:
            name = self._do_mangle(name)

        if cellvar:
            self._add_instruction(
                LOAD_DEREF, self._unit.cellvars.index(name), cell.ln,
            )
        elif freevar:
            self._add_instruction(
                LOAD_DEREF,
                self._unit.freevars.index(name) + len(self._unit.cellvars),
                cell.ln,
            )
        elif symbol.flag & SYM_LOCAL:
            ni = self._add_varname(name)
            self._add_instruction(LOAD_FAST, ni, ln)
        elif symbol.flag & SYM_GLOBAL:
            ni = self._add_name(name)
            self._add_instruction(LOAD_GLOBAL, ni, ln)
        elif symbol.flag & SYM_NORMAL:
            ni = self._add_name(name)
            self._add_instruction(LOAD_NAME, ni, ln)

    def _compile_call_name(
            self, name: str, args: List[ast.Expression], ln: int, scope=None):

        if scope is None:
            scope = SYM_GLOBAL

        left = ast.CellAST(name, AIL_IDENTIFIER, ln)
        left.symbol = Symbol(name, scope)

        self._compile_call_expr(
            ast.CallExprAST(
                left,
                ast.ArgListAST(
                    [ast.ArgItemAST(e, False, e.ln)
                     for e in args],
                    ln
                ),
                ln,
            ),
        )

    def _compile_cell(self, cell: ast.CellAST):
        if cell.type == AIL_IDENTIFIER:
            return self._compile_name(cell)
        return self._compile_const(cell)

    def _compile_bool_expr(self, expr: ast.AndTestAST):
        cond = isinstance(expr, ast.OrTestAST)
        end = BasicBlock()

        for e in [expr.left] + expr.right[:-1]:
            self._compile(e)
            self._add_jump_op(
                JUMP_IF_TRUE_OR_POP if cond else JUMP_IF_FALSE_OR_POP,
                end, -1
            )

        self._compile(expr.right[-1])
        self._enter_next_block(end)

    def _compile_logical_jump(
            self, expr: Union[ast.AndTestAST, ast.OrTestAST]):
        self._compile(expr.left)
        right = BasicBlock()
        next_ = BasicBlock()
        
        condition = isinstance(expr, ast.OrTestAST)

        self._add_jump_op(
            JUMP_IF_TRUE_OR_POP if condition else JUMP_IF_FALSE_OR_POP,
            next_, expr.ln)

    def _compile_if_jump(
            self, expr: ast.Expression, condition: int, target: BasicBlock):
        if isinstance(expr, ast.TestExprAST):
            expr = expr.test

        if isinstance(expr, ast.NotTestAST):
            return self._compile_if_jump(expr.expr, not condition, target)
        elif type(expr) in (ast.OrTestAST, ast.AndTestAST):
            # these code below is not available,
            # simply use the _compile_bool_expr to compile it.
            # TODO: simplify the code of if stmt with a bool expr as its condition
            """
            cond2 = isinstance(expr, ast.OrTestAST)
            if cond2 == condition:
                target2 = BasicBlock()
            else:
                target2 = target
            for e in [expr.left] + expr.right[:-1]:
                self._compile_if_jump(e, cond2, target2)
            self._compile_if_jump(expr.right[-1], condition, target)
            if target2 is not target:
                self._enter_next_block(target2)
            return
            """

        self._compile(expr)

        instr = Instruction()
        instr.is_jabs = True
        instr.target = target
        instr.opcode = POP_JUMP_IF_TRUE if condition else POP_JUMP_IF_FALSE
        instr.line = expr.ln

        self._unit.block.add_instruction(instr)

    def _compile_if(self, stmt: ast.IfStmtAST):
        if_block = BasicBlock()
        else_block = BasicBlock()
        next_block = BasicBlock()

        self._compile_if_jump(stmt.test, 0, else_block)
        self._enter_next_block(if_block)
        self._compile(stmt.block)

        if len(stmt.else_block.stmts) != 0:
            self._add_jump_op(JUMP_FORWARD, next_block, -1)

        self._enter_next_block(else_block)
        self._compile_block(stmt.else_block)

        self._enter_next_block(next_block)

    def _compile_binary_expr(self, expr):
        self._compile_expr(expr.left)

        for op, right in expr.right:
            self._compile_expr(right)
            opc = BIN_OP_MAP[op]
            self._add_instruction(opc, 0, right.ln)

    def _compile_unary_not(self, expr: ast.NotTestAST):
        self._compile(expr.expr)
        self._add_instruction(UNARY_NOT, 0, expr.ln)

    def _compile_compare_expr(self, expr: ast.CmpTestAST):
        self._compile(expr.left)
        n = len(expr.right)
        if n == 1:
            op, exp = expr.right[0]
            op = CMP_OP_MAP[op]
            self._compile(exp)
            self._add_instruction(COMPARE_OP, op, expr.ln)
        else:
            # a > b > c  -> a > b and b > c
            end = BasicBlock()
            count = 0

            for op, exp in expr.right:
                count += 1

                next_ = BasicBlock()

                self._compile(exp)

                if count < n:
                    self._add_instruction(DUP_TOP, 0, -1)
                    self._add_instruction(ROT_THREE, 0, -1)

                self._add_instruction(COMPARE_OP, CMP_OP_MAP[op], exp.ln)

                if count < n:
                    self._add_jump_op(JUMP_IF_FALSE_OR_POP, end, -1)
                self._enter_next_block(next_)

            self._enter_next_block(end)

    def _compile_call_arg(self, arg_list: ast.ArgListAST, call_method: bool):
        args = arg_list.arg_list

        kwarg = [arg for arg in args if arg.default is not None]
        posarg = [arg for arg in args
                  if arg.default is None and not arg.star and not arg.kw_star]
        kw_extra = len([arg for arg in args if arg.kw_star]) > 0
        extra = len([arg for arg in args if arg.star]) > 0

        if not kw_extra and not extra:
            if kwarg:
                key_tuple = tuple((arg.expr.value for arg in kwarg))
                instr_arg = len(kwarg) + len(posarg)
                for arg in posarg:
                    self._compile(arg.expr)
                for arg in kwarg:
                    self._compile(arg.default)
                ci = self._add_const(key_tuple)
                self._add_instruction(LOAD_CONST, ci, -1)
                self._add_instruction(
                    CALL_FUNCTION_KW, instr_arg, arg_list.ln,
                    stack_effect=-instr_arg - 1
                    # effect = arg len + func + key tuple - return
                )
                return
            for arg in posarg:
                self._compile(arg.expr)
            self._add_instruction(
                CALL_METHOD if call_method else CALL_FUNCTION,
                len(posarg), arg_list.ln,
                stack_effect=-len(posarg),
            )
            return
        else:
            flags = int(len(kwarg) > 0 or kw_extra > 0)

            in_pos_arg = False
            pos_arg_count = 0
            in_kw_arg = False

            seen_kw_part = False
            kw_arg_segment = []
            map_unpack_count = 0
            build_map_unpack = False

            build_tuple_unpack = False
            tuple_unpack_count = 0

            for ai, arg in enumerate(args):
                if arg.is_positional():
                    self._compile(arg.expr)
                    pos_arg_count += 1
                    in_pos_arg = True

                if arg.star:
                    if pos_arg_count > 0 and in_pos_arg:
                        self._add_instruction(
                            BUILD_TUPLE, pos_arg_count, -1,
                            stack_effect=-pos_arg_count + 1
                        )
                        in_pos_arg = False
                        pos_arg_count = 0
                        tuple_unpack_count += 1
                    self._compile(arg.expr)
                    build_tuple_unpack = True
                    tuple_unpack_count += 1

                if (arg.kw_star or arg.default is not None
                        and not seen_kw_part) or ai == len(args) - 1:
                    if arg.kw_star or arg.default is not None:
                        seen_kw_part = True
                    
                    # build an empty tuple if no pos arg.
                    self._add_instruction(
                        BUILD_TUPLE, pos_arg_count, -1,
                        stack_effect=-pos_arg_count + 1
                    )
                    in_pos_arg = False
                    pos_arg_count = 0
                    tuple_unpack_count += 1

                    if build_tuple_unpack:
                        self._add_instruction(
                            BUILD_TUPLE_UNPACK_WITH_CALL, tuple_unpack_count, -1,
                            stack_effect=-tuple_unpack_count
                        )

                if arg.default is not None:
                    kw_arg_segment.append(arg)
                    in_kw_arg = True

                if arg.kw_star or (ai == len(args) - 1 and seen_kw_part):
                    if in_kw_arg is True and kw_arg_segment:
                        in_kw_arg = False
                        for karg in kw_arg_segment:
                            self._compile(karg.expr)
                        keys = tuple((arg.expr.value for arg in kw_arg_segment))
                        self._add_instruction(
                            LOAD_CONST, self._add_const(keys), -1
                        )
                        self._add_instruction(
                            BUILD_MAP, len(keys), -1, stack_effect=-len(keys),
                        )
                        kw_arg_segment.clear()
                        map_unpack_count += 1

                    self._compile(arg.expr)
                    map_unpack_count += 1
                    build_map_unpack = True

                if ai == len(args) - 1 and build_map_unpack and map_unpack_count > 1:
                    self._add_instruction(
                        BUILD_MAP_UNPACK_WITH_CALL, map_unpack_count, -1,
                        stack_effect=-map_unpack_count
                    )

            if flags:
                effect = -2
            else:
                effect = -1
            self._add_instruction(
                CALL_FUNCTION_EX, flags, -1,
                stack_effect=effect,
            )

    def _compile_call_expr(self, expr: ast.CallExprAST, build_class=False):
        if build_class:
            self._add_instruction(LOAD_BUILD_CLASS, 0, -1)
        else:
            self._compile(expr.left)

        self._compile_call_arg(
            expr.arg_list, isinstance(expr.left, ast.MemberAccessAST))

    def _compile_print_stmt(self, stmt: ast.PrintStmtAST):
        self._compile_call_name(
            'print', stmt.value_list, stmt.ln,
        )
        self._add_instruction(POP_TOP, 0, -1)

    def _compile_assign_expr(self, expr: ast.AssignExprAST, as_stmt=False):
        self._compile(expr.right)

        if not as_stmt:
            self._add_instruction(DUP_TOP, 0, -1)

        self._compile_store(expr.left)

    def _compile_object_pattern(self, expr: ast.ObjectPatternExpr):
        self._compile_call_name(
            'ail::ObjectPattern',
            [
                expr.left,
                ast.DictAST(
                    [_new_cell_fast(val, AIL_STRING, -1, SYM_NORMAL)
                        for val in expr.keys],
                    expr.values,
                    expr.ln,
                ),
            ],
            expr.ln,
            SYM_GLOBAL,
        )

    def _compile_store(self, target: ast.Expression):
        if isinstance(target, ast.TupleAST):
            left = target.items
            # check left star
            before_star_count = 0
            seen_star = False
            for elt in left:
                if isinstance(elt, ast.StarredExpr):
                    seen_star = True

                if not seen_star:
                    before_star_count += 1

            if seen_star:
                arg = before_star_count + ((len(left) - before_star_count - 1) << 8)
                self._add_instruction(
                    UNPACK_EX, arg, -1, check=True,
                    stack_effect=len(left) - 1
                )

            elif len(left) > 1:
                self._add_instruction(
                    UNPACK_SEQUENCE, len(left), -1,
                    stack_effect=-len(left) - 1
                )

            for elt in left:
                if isinstance(elt, ast.StarredExpr):
                    elt = elt.value
                self._compile_store(elt)

        if isinstance(target, ast.CellAST):
            name: str = target.value
            sym: Symbol = target.symbol

            if name in self._unit.cellvars:
                self._add_instruction(
                    STORE_DEREF, self._unit.cellvars.index(name), target.ln,
                )

            elif name in self._unit.freevars:
                self._add_instruction(
                    STORE_DEREF,
                    self._unit.freevars.index(name) + len(self._unit.cellvars),
                    target.ln,
                )

            elif sym.flag & SYM_NORMAL:
                ni = self._add_name(name)
                self._add_instruction(STORE_NAME, ni, target.ln)

            elif sym.flag & SYM_LOCAL:
                ni = self._add_varname(name)
                self._add_instruction(STORE_FAST, ni, target.ln)

            elif sym.flag & SYM_GLOBAL:
                ni = self._add_name(name)
                self._add_instruction(STORE_GLOBAL, ni, target.ln)

        elif isinstance(target, ast.MemberAccessAST):
            self._compile(target.left)
            attr = self._do_mangle(target.member.value)
            self._add_instruction(
                STORE_ATTR, self._add_name(attr), target.ln)

    def _compile_do_loop(self, stmt: ast.DoLoopStmtAST):
        body = BasicBlock()
        test = BasicBlock()
        next_ = BasicBlock()

        frame = FrameBlock(FB_WHILE_LOOP, test, next_)

        with self._frame(frame):
            self._enter_next_block(body)
            self._compile(stmt.block)
            self._enter_next_block(test)
            self._compile(stmt.test)
            self._add_jump_op(POP_JUMP_IF_TRUE, next_, -1)
            self._add_jump_op(JUMP_ABSOLUTE, body, -1)
        
        self._enter_next_block(next_)

    def _compile_while_stmt(self, stmt: ast.WhileStmtAST):
        start = BasicBlock()
        next_ = BasicBlock()

        frame = FrameBlock(FB_WHILE_LOOP, start, next_)

        with self._frame(frame):
            self._enter_next_block(start)
            self._compile(stmt.test)
            self._add_jump_op(POP_JUMP_IF_FALSE, next_, -1)

            self._compile(stmt.block)
            self._add_jump_op(JUMP_ABSOLUTE, start, -1)

        self._enter_next_block(next_)

    def _compile_for_stmt(self, stmt: ast.ForStmtAST):
        for expr in stmt.init_list.expr_list:
            self._compile(expr, True)
        
        body = BasicBlock()
        update = BasicBlock()
        next_ = BasicBlock()

        self.push_new_frame(FB_FOR_LOOP, update, next_, None)
        
        self._enter_next_block(body)
        self._compile(stmt.test.test)
        self._add_jump_op(POP_JUMP_IF_FALSE, next_, -1)

        self._compile(stmt.block)
        
        self._enter_next_block(update)
        for expr in stmt.update_list.expr_list:
            self._compile(expr, True)
        self._add_jump_op(JUMP_ABSOLUTE, body, -1)

        self.pop_frame()

        self._enter_next_block(next_)

    def _compile_foreach_stmt(self, stmt: ast.ForeachStmt):
        start = BasicBlock()
        next_ = BasicBlock()

        frame = FrameBlock(FB_FOREACH_LOOP, start, next_)

        with self._frame(frame):
            self._compile(stmt.iter)
            self._add_instruction(GET_ITER, 0, stmt.ln)
            self._enter_next_block(start)
            self._add_jump_op(FOR_ITER, next_, stmt.ln)
            self._compile_store(stmt.target)
            self._compile_block(stmt.body)
            self._add_jump_op(JUMP_ABSOLUTE, start, stmt.ln)

        self._enter_next_block(next_)

    def _compile_break_stmt(self, stmt: ast.BreakStmtAST):
        frame = self._unit.fb_stack[-1]

        index = len(self._unit.fb_stack) - 1
        while index >= 0:
            self._unwind_frame_block(frame)

            if frame.type in (FB_WHILE_LOOP, FB_FOREACH_LOOP):
                self._add_jump_op(JUMP_ABSOLUTE, frame.next, stmt.ln)
                return
            elif frame.type == FB_FOR_LOOP:
                self._add_jump_op(JUMP_ABSOLUTE, frame.next, stmt.ln)

            index -= 1
            frame = self._unit.fb_stack[index]

    def _compile_return_stmt(self, stmt: ast.ReturnStmtAST):
        expr = stmt.expr
        preserve_tos = \
            isinstance(expr, ast.CellAST) and expr.type == AIL_IDENTIFIER

        if preserve_tos:
            self._compile(stmt.expr)

        if self._unit.fb_stack:
            frame = self._unit.fb_stack[-1]

            index = len(self._unit.fb_stack) - 1
            while index >= 0:
                self._unwind_frame_block(frame, preserve_tos)
                index -= 1
                frame = self._unit.fb_stack[index]

        if not preserve_tos:
            self._compile(expr)

        self._add_instruction(RETURN_VALUE, 0, stmt.ln)

    def _compile_match_expr(self, expr: ast.MatchExpr):
        self._compile_name(
            ast.CellAST(
                'ail::match', AIL_IDENTIFIER, expr.ln, Symbol('ail::match', SYM_GLOBAL)))
        self._compile(expr.target)

        case_bb = BasicBlock() 
        next_ = BasicBlock()

        for case in expr.cases:
            self._enter_next_block(case_bb)
            next_case_bb = BasicBlock()
            if len(case.patterns) > 0:
                self._add_instruction(DUP_TOP_TWO, 0, case.ln)
                self._compile_build_tuple(case.patterns)
                self._add_instruction(CALL_FUNCTION, 2, -1, stack_effect=-2)
                self._add_jump_op(POP_JUMP_IF_FALSE, next_case_bb, -1)
            self._compile(case.expr)
            self._add_instruction(ROT_THREE, 0, -1)

            # pop the match function and target
            self._add_instruction(POP_TOP, 0, -1)
            self._add_instruction(POP_TOP, 0, -1)

            self._add_jump_op(JUMP_FORWARD, next_, -1)
            case_bb = next_case_bb

        self._enter_next_block(next_case_bb)

        self._add_instruction(POP_TOP, 0, -1)
        self._add_instruction(POP_TOP, 0, -1)

        self._compile_call_name(
            'py::UnhandledMatchError',
            [ast.CellAST('unhandled match value', AIL_STRING, -1)],
            -1, SYM_GLOBAL,
        )
        self._add_instruction(RAISE_VARARGS, 1, -1, stack_effect=-1)

        self._enter_next_block(next_)

    def _compile_namespace_stmt(self, stmt: ast.NamespaceStmt):
        stmt.block.stmts.append(
            ast.ReturnStmtAST(
                ast.CallExprAST(
                    _new_cell_fast('py::locals', AIL_IDENTIFIER, -1, SYM_GLOBAL),
                    ast.ArgListAST([], -1),
                    -1,
                ),
                -1
            )
        )

        func_expr = ast.FunctionDefineAST(
            stmt.name,
            ast.ArgListAST(
                [ast.ArgItemAST(
                    _new_cell_fast('ail::_register_function', AIL_IDENTIFIER, -1, SYM_LOCAL),
                    False, -1,
                )],
                stmt.ln
            ),
            stmt.block,
            None, stmt.ln, symbol=stmt.symbol,
        )

        func_expr.namespace_body = True

        self._compile_call_name('ail::namespace', [func_expr], -1)
        self._compile_store(_new_cell_fast(stmt.name, AIL_IDENTIFIER, -1, stmt.symbol.flag))

    def _compile_unary_expr(self, expr: ast.UnaryExprAST):
        right = expr.expr
        
        # check constant
        if isinstance(right, ast.CellAST) and right.type == AIL_NUMBER:
            right.value = expr.op + right.value
            self._compile_const(right)
            return

        op = {
            '+': UNARY_POSITIVE,
            '-': UNARY_NEGATIVE,
        }[expr.op]

        self._compile(right)
        self._add_instruction(op, 0, expr.ln)

    def _compile_list(self, expr: ast.ListAST):
        item_list = expr.items.item_list

        for elt in item_list:
            self._compile(elt)

        self._add_instruction(
            BUILD_LIST, len(item_list), expr.ln,
            stack_effect=-len(item_list) + 1)

    def _compile_tuple(self, expr: ast.TupleAST):
        item_list = expr.items

        for elt in item_list:
            self._compile(elt)

        self._add_instruction(
            BUILD_TUPLE, len(item_list), expr.ln,
            stack_effect=-len(item_list) + 1)

    def _compile_dict(self, expr: ast.DictAST):
        keys = expr.keys
        values = expr.values

        for k, v in zip(keys, values):
            self._compile(k)
            self._compile(v)

        self._add_instruction(
            BUILD_MAP,
            len(keys),
            expr.ln,
            stack_effect=-2 * len(keys) + 1,
        )

    def _compile_class(self, cls: ast.ClassDefineAST, as_stmt=False):
        for deco in cls.decorator:
            self._compile(deco)

        cls.func.block.stmts.insert(
            0,
            ast.AssignExprAST(
                ast.CellAST(
                    '__module__', AIL_IDENTIFIER, cls.ln,
                    Symbol('__module__', SYM_NORMAL)
                ),
                ast.CellAST(
                    '__name__', AIL_IDENTIFIER, cls.ln,
                    Symbol('__name__', SYM_GLOBAL)
                ),
                cls.ln
            ),
        )

        cls.func.block.stmts.insert(
            1,
            ast.AssignExprAST(
                ast.CellAST(
                    '__qualname__', AIL_IDENTIFIER, cls.ln,
                    Symbol('__qualname__', SYM_NORMAL)
                ),
                ast.CellAST(
                    cls.name, AIL_STRING, cls.ln
                ),
                cls.ln
            ),
        )

        args = [
            cls.func,
            ast.CellAST(cls.name, AIL_STRING, cls.ln),
        ]

        for base in cls.bases:
            args.append(base)

        if cls.meta:
            args.append(
                ast.ArgItemAST(
                    ast.CellAST('metaclass', AIL_IDENTIFIER, cls.ln),
                    False, cls.ln,
                    default=cls.meta,
                )
            )

        self._compile_call_expr(
            ast.CallExprAST(
                None,
                ast.ArgListAST(
                    [
                        arg if isinstance(arg, ast.ArgItemAST)
                        else ast.ArgItemAST(arg, False, cls.ln)
                        for arg in args
                    ],
                    cls.ln
                ),
                cls.ln
            ), True
        )

        for _ in cls.decorator:
            self._add_instruction(CALL_FUNCTION, 1, -1, stack_effect=0)

        self._compile_store(
            ast.CellAST(cls.name, AIL_IDENTIFIER, cls.ln,
                        symbol=Symbol(cls.name, cls.symbol.flag))
        )

    def _compile_function(
            self, func: ast.FunctionDefineAST, as_stmt=False, namespace_body=False):
        sym: SymbolTable = func.symbol.namespace

        got_decorator = len(func.decorator) > 0
        for deco in func.decorator:
            self._compile(deco)

        if namespace_body:
            self._add_instruction(
                LOAD_FAST, self._add_varname('ail::_register_function'), func.ln,
            )

        frees = sym.freevars
        unit = self._unit

        b = BasicBlock()

        self.enter_new_scope(sym, func.name, func.block.ln)
        self._unit.block = b
        self._unit.top_block = b

        co_flags = 0

        for param in func.param_list.arg_list:
            assert isinstance(param.expr, ast.CellAST)
            # param_name = self._do_mangle(param.expr.value)
            # param.expr.value = param_name
            self._add_varname(param.expr.value)

            if param.star:
                co_flags |= 0x04
            if param.kw_star:
                co_flags |= 0x08

        self._compile_block(func.block, namespace_body=func.namespace_body)

        self._add_instruction(
            LOAD_CONST, self._add_const(None), -1
        )
        self._add_instruction(RETURN_VALUE, 0, -1)

        assembler = Assembler()
        code = assembler.assemble(self._unit.top_block, self, co_flags)

        self._unit = unit

        effect = -1
        flag = 0

        defaults = [x.default for x in func.param_list.arg_list if x.default is not None]
        if defaults:
            for default in defaults:
                self._compile(default)
            self._add_instruction(
                BUILD_TUPLE, len(defaults), func.ln, stack_effect=-len(defaults) + 1)
            flag |= 0x1
            effect -= 1

        if frees:
            for name in frees:
                if name in self._unit.cellvars:
                    self._add_instruction(
                        LOAD_CLOSURE,
                        self._unit.cellvars.index(name),
                        func.ln
                    )
                elif name in self._unit.freevars:
                    self._add_instruction(
                        LOAD_CLOSURE,
                        self._unit.freevars.index(name) + len(self._unit.cellvars),
                        func.ln
                    )
                else:
                    raise CompilerError(
                        'closure name neither in freevars nor cellvars')
            self._add_instruction(
                BUILD_TUPLE, len(frees), -1, stack_effect=-len(frees) + 1,
            )
            flag |= 0x8
            effect -= -1

        self._add_instruction(LOAD_CONST, self._add_const(code), func.ln)
        self._add_instruction(LOAD_CONST, self._add_const(func.name), -1)
        self._add_instruction(
            MAKE_FUNCTION, flag, func.ln,
            stack_effect=effect,
        )

        if namespace_body:
            self._add_instruction(DUP_TOP, 0, -1)

        for _ in func.decorator:
            self._add_instruction(
                CALL_FUNCTION, 1, -1, 
                stack_effect=0
            )

        if as_stmt or namespace_body:
            cell = ast.CellAST(func.name, AIL_IDENTIFIER, func.ln)
            cell.symbol = func.symbol
            self._compile_store(cell)

        if namespace_body:
            self._add_instruction(
                CALL_FUNCTION, 1, -1, stack_effect=-1
            )
            self._add_instruction(POP_TOP, 0, -1)

    def _compile_continue_stmt(self, stmt: ast.ContinueStmtAST):
        frame = self._unit.fb_stack[-1]

        index = len(self._unit.fb_stack) - 1
        while index >= 0:
            self._unwind_frame_block(frame)

            if frame.type in (FB_WHILE_LOOP, FB_FOREACH_LOOP):
                self._add_jump_op(JUMP_ABSOLUTE, frame.start, stmt.ln)
                return

            elif frame.type == FB_FOR_LOOP:
                self._add_jump_op(JUMP_ABSOLUTE, frame.start, stmt.ln)
                return

            index -= 1
            frame = self._unit.fb_stack[index]

    def _compile_try(self, stmt: ast.TryCatchStmtAST):
        if stmt.finally_block is not None:
            self._compile_try_finally_stmt(stmt)
        else:
            self._compile_try_catch_stmt(stmt)

    # Code generated for try { T } catch E1 V1 { C1 } ... catch En Vn { Cn }
    # (the top of value stack at the right)
    #
    # Value Stack               Label       OP                  Arg
    # []                                    SETUP_FINALLY       L1
    # []                                    <code for T>
    # []                                    POP_BLOCK
    # []                                    JUMP_FORWARD        L0
    #
    # --- if an exception occurred
    #
    # [tb, val, exc]            L1          DUP
    # [tb, val, exc, exc]                   <eval E1>
    # [tb, val, exc, exc, E1]               COMPARE_OP          <exception match>
    # [tb, val, exc, 1 or 0]                POP_JUMP_IF_FALSE   L2
    # [tb, val, exc]                        POP_TOP
    # [tb, val]                             <assign to V1>
    # [tb]                                  POP_TOP
    # []                                    <code for C1>
    # []                                    JUMP_FORWARD        L0
    # ...
    # [tb, val, exc]            Ln          DUP_TOP
    # [tb, val, exc, exc]                   <eval En>
    # [tb, val, exc, exc, E1]               COMPARE_OP          <exception match>
    # [tb, val, exc, 1 or 0]                POP_JUMP_IF_FALSE   L(n + 1)
    # [tb, val, exc]                        POP_TOP
    # [tb, val]                             <assign to Vn>
    # [tb]                                  POP_TOP
    # []                                    <code for Cn>
    # []                                    JUMP_FORWARD        L0
    #
    # []                        L(n + 1)    END_FINALLY
    #
    # []                        L0          <next statement>
    def _compile_try_catch_stmt(self, stmt: ast.TryCatchStmtAST):
        body = BasicBlock()
        handler = BasicBlock()
        next_handler = BasicBlock()
        next_ = BasicBlock()

        self._enter_next_block(body)

        self.push_new_frame(FB_EXCEPT, None, None, None)

        self._add_jump_op(SETUP_FINALLY, handler, -1)
        self._compile(stmt.try_block)
        self._add_instruction(POP_BLOCK, 0, -1)
        self._add_jump_op(JUMP_FORWARD, next_, -1)

        self.pop_frame()
        self._enter_next_block(handler)
        for case in stmt.catch_cases:
            if case.exc_expr is not None:
                self._add_instruction(DUP_TOP, 0, case.exc_expr.ln)
                self._compile(case.exc_expr)
                self._add_instruction(COMPARE_OP, 10, -1)
                self._add_jump_op(POP_JUMP_IF_FALSE, next_handler, -1)
                self._add_instruction(POP_TOP, 0, -1)
                self._compile_store(case.alias_expr)
                self._add_instruction(POP_TOP, 0, -1)
            else:
                self._add_instruction(POP_TOP, 0, case.ln)
                self._add_instruction(POP_TOP, 0, -1)
                self._add_instruction(POP_TOP, 0, -1)

            # h_body = BasicBlock()
            # h_finally = BasicBlock()

            # self._enter_next_block(h_body)
            # self._add_jump_op(SETUP_FINALLY, h_finally, -1)

            self.push_new_frame(FB_HANDLER_FINISH, None, None, None)
            self._compile(case.block)
            self.pop_frame()

            # self._add_instruction(POP_TOP, 0, -1)
            # self._add_instruction(POP_BLOCK, 0, -1)

            # self._add_instruction(BEGIN_FINALLY, 0, -1)
            # self._enter_next_block(h_finally)

            self._add_instruction(POP_EXCEPT, 0, -1)
            self._add_jump_op(JUMP_FORWARD, next_, -1)  # skip END_FINALLY

            handler = next_handler
            self._enter_next_block(handler)
            next_handler = BasicBlock()

        self._add_instruction(END_FINALLY, 0, -1)
        self._enter_next_block(next_)

    # Code generated for try { T } finally { F }:
    # (the top of value stack at the right)
    #
    # Value stack           Label       OP              Arg
    # []                                SETUP_FINALLY   L
    # []                                <code for T>
    # []                                BEGIN_FINALLY
    # [null?]               L1          <code for F>
    # [null?]                           END_FINALLY
    #
    # P.S.
    # There not always a NULL in value stack when executing END_FINALLY,
    # for example, when the codes in T had raised an exception and spread to
    # this Try Structure, the value stack will be pushed traceback info, and
    # reraise them when finish the executing F.
    def _compile_try_finally_stmt(self, stmt: ast.TryCatchStmtAST):
        try_body = BasicBlock()
        finally_body = BasicBlock()

        cur_bblock = self._unit.block

        # compile finally body first to determine if there have 'continue'
        # statement to break the finally body

        self._enter_next_block(finally_body)
        finally_bblock = self._unit.block

        self.push_new_frame(FB_FINALLY_END, None, finally_body, finally_body)
        self._compile(stmt.finally_block)
        break_finally = self._unit.fb_stack[-1].exit is None
        self.pop_frame()
        self._add_instruction(END_FINALLY, 0, -1)
        if break_finally:
            self._add_instruction(POP_TOP, 0, -1, )

        self._enter_next_block(try_body)

        cur_bblock.next_block = self._unit.block
        finally_bblock.next_block = None

        if break_finally:
            self._add_instruction(
                LOAD_CONST, self._add_const(None), -1
            )
        self._add_jump_op(SETUP_FINALLY, finally_body, -1)

        self.push_new_frame(
            FB_FINALLY_TRY_WITH_BREAK if break_finally else FB_FINALLY_TRY,
            None, None, finally_body,
        )
        if len(stmt.catch_cases) == 0:
            self._compile(stmt.try_block)
        else:
            self._compile_try_catch_stmt(stmt)

        self.pop_frame()

        self._add_instruction(POP_BLOCK, 0, -1)
        self._add_instruction(BEGIN_FINALLY, 0, -1)
        self._enter_next_block(finally_bblock)

    def _compile_with(self, stmt: ast.WithStmt, pos: int = 0):
        finally_block = BasicBlock()
        body = BasicBlock()

        item = stmt.items[pos]
        self._compile(item.context_expr)
        self._add_jump_op(SETUP_WITH, finally_block, -1)

        if item.optional_var is None:
            self._add_instruction(POP_TOP, 0, -1)
        else:
            self._compile_store(item.optional_var)
        
        self._enter_next_block(body)
        self.push_new_frame(FB_WITH, None, None, finally_block)

        if len(stmt.items) - 1 > pos:
            pos += 1
            self._compile_with(stmt, pos)
            return

        self._add_instruction(POP_BLOCK, 0, -1)  # pop try block
        self._add_instruction(BEGIN_FINALLY, 0, -1)
        self._compile_block(stmt.body)

        self.pop_frame()
        
        self._enter_next_block(finally_block)
        self.push_new_frame(FB_FINALLY_END, 0, finally_block, finally_block)

        self._add_instruction(WITH_CLEANUP_START, 0, -1)
        self._add_instruction(WITH_CLEANUP_FINISH, 0, -1)

        self._add_instruction(END_FINALLY, 0, -1 )
        self.pop_frame()

    def _compile_member_access_expr(self, expr: ast.MemberAccessAST):
        self._compile_expr(expr.left)

        attr = self._do_mangle(expr.member.value)

        if expr.call_method:
            self._add_instruction(
                LOAD_METHOD, self._add_name(attr), expr.ln,
                stack_effect=1,
            )
        else:
            self._add_instruction(
                LOAD_ATTR, self._add_name(attr), expr.ln,
                stack_effect=1,
            )

    def _compile_throw_stmt(self, stmt: ast.ThrowStmtAST):
        if stmt.expr is None:
            self._add_instruction(
                RAISE_VARARGS, 0, -1,
                stack_effect=0
            )
            return

        self._compile(stmt.expr)
        self._add_instruction(
            RAISE_VARARGS, 1, -1,
            stack_effect=-1,
        )

    def _compile_subscript_expr(self, expr: ast.SubscriptExprAST):
        self._compile(expr.left)

        exp = expr.expr

        if isinstance(exp, ast.SliceExpr):
            exp_count = 2

            if exp.start is not None:
                self._compile(exp.start)
            else:
                ci = self._add_const(None)
                self._add_instruction(LOAD_CONST, ci, exp.ln)

            if exp.stop is not None:
                self._compile(exp.stop)
            else:
                ci = self._add_const(None)
                self._add_instruction(LOAD_CONST, ci, exp.ln)

            if exp.step is not None:
                exp_count += 1
                self._compile(exp.step)

            self._add_instruction(
                BUILD_SLICE, exp_count, exp.ln,
                stack_effect=-exp_count + 1)
        else:
            self._compile(exp)

        self._add_instruction(BINARY_SUBSCR, 0, expr.ln)

    def _compile_py_import_stmt(self, stmt: ast.PyImportStmt):
        for item in stmt.names:
            alias = item.alias if item.alias else item.name
            self._add_instruction(LOAD_CONST, self._add_const(0), -1)
            self._add_instruction(LOAD_CONST, self._add_const(None), -1)
            self._add_instruction(IMPORT_NAME, self._add_name(item.name), -1)
            self._compile_store(
                _new_cell_fast(
                    alias, AIL_IDENTIFIER, stmt.ln, item.symbol.flag))

    def _compile_py_import_from_stmt(self, stmt: ast.PyImportFromStmt):
        self._add_instruction(LOAD_CONST, self._add_const(0), stmt.ln)
        self._add_instruction(
            LOAD_CONST, self._add_const(
                tuple((item.name for item in stmt.names))
            ), -1
        )
        self._add_instruction(IMPORT_NAME, self._add_name(stmt.module), -1)

        for name in stmt.names:
            alias = name.alias if name.alias else name.name
            self._add_instruction(IMPORT_FROM, self._add_name(name.name), -1)
            self._compile_store(
                _new_cell_fast(alias, AIL_IDENTIFIER, -1, name.symbol.flag)
            )

    def _compile_annotation_assign_stmt(self, stmt: ast.AnnAssignStmt):
        if not self._unit.annotations_setup:
            self._add_instruction(SETUP_ANNOTATIONS, 0, stmt.ln)
            self._unit.annotations_setup = True

        if stmt.value is not None:
            self._compile(stmt.value)
            self._compile_store(stmt.target)

        if not isinstance(stmt.target, ast.CellAST):
            return

        self._compile(stmt.annotation)
        self._add_instruction(
            LOAD_NAME, self._add_name('__annotations__'), -1
        )

        assert isinstance(stmt.target, ast.CellAST)

        self._add_instruction(
            LOAD_CONST, self._add_const(stmt.target.value), -1
        )

        self._add_instruction(STORE_SUBSCR, 0, -1)

    def _compile_load_stmt(self, stmt: ast.LoadStmtAST):
        ln = stmt.ln

        self._compile_call_name(
            '__ail_import__',
            [
                _new_cell_fast('0', AIL_NUMBER, ln, 0),
                _new_cell_fast(stmt.path, AIL_STRING, ln, 0),
                ast.CallExprAST(
                    _new_cell_fast('py::locals', AIL_IDENTIFIER, -1, SYM_GLOBAL),
                    ast.ArgListAST([], -1),
                    -1,
                )
            ],
            ln,
            SYM_GLOBAL,
        )

    def _compile_import_stmt(self, stmt: ast.ImportStmtAST):
        members = stmt.members
        if members is None:
            members = []

        if len(members) == 0:
            target = _new_cell_fast(
                stmt.name, AIL_IDENTIFIER, stmt.ln,
                stmt.symbol.flag
            )
        else:
            target = ast.TupleAST(
                [_new_cell_fast(
                        name, AIL_IDENTIFIER, -1, stmt.member_symbols[i].flag)
                    for i, name in enumerate(stmt.members)],
                True,
                stmt.ln,
            )

        self._compile_call_name(
            '__ail_import__',
            [
                _new_cell_fast('1', AIL_NUMBER, -1, 0),
                _new_cell_fast(stmt.path, AIL_STRING, -1, 0),
                _new_cell_fast('None', AIL_IDENTIFIER, -1, 0),
                _new_cell_fast(stmt.name, AIL_STRING, -1, 0),
                ast.ListAST(
                    ast.ItemListAST(
                        [_new_cell_fast(m, AIL_STRING, -1, 0) for m in stmt.members],
                        -1,
                    ),
                    -1,
                )
            ],
            -1,
            SYM_GLOBAL,
        )

        self._compile_store(target)

    def _compile_if_expr(self, expr: ast.IfExpr):
        body = BasicBlock()
        orelse = BasicBlock()
        end = BasicBlock()

        self._compile(expr.test)
        self._add_jump_op(POP_JUMP_IF_FALSE, orelse, -1)
        self._enter_next_block(body)
        self._compile(expr.body)
        self._add_jump_op(JUMP_FORWARD, end, -1)
        self._enter_next_block(orelse)
        self._compile(expr.orelse)
        self._enter_next_block(end)

    def _compile_pyasm_expr(self, expr: ast.PyASMExpr):
        if expr.op in OP_CONST:
            ci = self._add_const(expr.arg)
            self._add_instruction(
                expr.op, ci, expr.ln, stack_effect=expr.effect
            )
        elif expr.op in OP_NAME:
            ni = self._add_name(expr.arg)
            self._add_instruction(
                expr.op, ni, expr.ln, stack_effect=expr.effect
            )
        elif expr.op in OP_VARNAME:
            ni = self._add_varname(expr.arg)
            self._add_instruction(
                expr.op, ni, expr.ln, stack_effect=expr.effect
            )
        else:
            self._add_instruction(expr.op, expr.arg, expr.ln, stack_effect=expr.effect)

    def _compile_pyasm_group(self, group: ast.PyASMGroupExpr):
        for expr in group.stmts:
            self._compile_pyasm_expr(expr)

    def _compile_expr(self, expr: ast.Expression):
        if isinstance(expr, ast.CellAST):
            return self._compile_cell(expr)

        elif isinstance(expr, ast.CallExprAST):
            return self._compile_call_expr(expr)

        elif isinstance(expr, ast.MemberAccessAST):
            return self._compile_member_access_expr(expr)

        elif isinstance(expr, ast.SubscriptExprAST):
            return self._compile_subscript_expr(expr)

        elif isinstance(expr, ast.ListAST):
            return self._compile_list(expr)

        elif isinstance(expr, ast.TupleAST):
            self._compile_tuple(expr)

        elif isinstance(expr, ast.DictAST):
            self._compile_dict(expr)

        elif isinstance(expr, ast.IfExpr):
            self._compile_if_expr(expr)

        elif isinstance(expr, ast.UnaryExprAST):
            self._compile_unary_expr(expr)

        elif isinstance(expr, ast.NotTestAST):
            self._compile_unary_not(expr)

        elif isinstance(expr, ast.MatchExpr):
            self._compile_match_expr(expr)

        elif isinstance(expr, ast.PyASMGroupExpr):
            self._compile_pyasm_group(expr)

        elif isinstance(expr, ast.PyASMExpr):
            self._compile_pyasm_expr(expr)

        elif type(expr) in ast.BIN_OP_AST:
            self._compile_binary_expr(expr)

        else:
            raise Warning('Compiler: Node %s (value = %s) cannot be compiled' %
                          (type(expr), expr))

    def _compile_block(self, block: ast.BlockAST, namespace_body=False):
        stmts = block.stmts

        for stmt in stmts:
            self._compile(stmt, as_stmt=True, namespace_body=namespace_body)

    def _compile(self, node: ast.AST, as_stmt: bool = False, namespace_body=False):
        if isinstance(node, ast.BlockAST) or isinstance(node, ast.ProgramBlock):
            self._compile_block(node)

        elif isinstance(node, ast.IfStmtAST):
            self._compile_if(node)

        elif type(node) in (ast.OrTestAST, ast.AndTestAST):
            self._compile_bool_expr(node)

        elif isinstance(node, ast.TestExprAST):
            self._compile(node.test)

        elif isinstance(node, ast.CmpTestAST):
            self._compile_compare_expr(node)

        elif isinstance(node, ast.PrintStmtAST):
            self._compile_print_stmt(node)

        elif isinstance(node, ast.AssignExprAST):
            self._compile_assign_expr(node, as_stmt)

        elif isinstance(node, ast.WhileStmtAST):
            self._compile_while_stmt(node)

        elif isinstance(node, ast.BreakStmtAST):
            self._compile_break_stmt(node)

        elif isinstance(node, ast.ContinueStmtAST):
            self._compile_continue_stmt(node)

        elif isinstance(node, ast.FunctionDefineAST):
            self._compile_function(node, as_stmt, namespace_body)

        elif isinstance(node, ast.ReturnStmtAST):
            self._compile_return_stmt(node)

        elif isinstance(node, ast.ForStmtAST):
            self._compile_for_stmt(node)

        elif isinstance(node, ast.ForeachStmt):
            self._compile_foreach_stmt(node)

        elif isinstance(node, ast.DoLoopStmtAST):
            self._compile_do_loop(node)

        elif isinstance(node, ast.TryCatchStmtAST):
            self._compile_try(node)

        elif isinstance(node, ast.WithStmt):
            self._compile_with(node)

        elif isinstance(node, ast.ThrowStmtAST):
            self._compile_throw_stmt(node)

        elif isinstance(node, ast.ClassDefineAST):
            self._compile_class(node)

        elif isinstance(node, ast.NamespaceStmt):
            self._compile_namespace_stmt(node)

        elif isinstance(node, ast.PyImportStmt):
            self._compile_py_import_stmt(node)

        elif isinstance(node, ast.PyImportFromStmt):
            self._compile_py_import_from_stmt(node)

        elif isinstance(node, ast.AnnAssignStmt):
            self._compile_annotation_assign_stmt(node)

        elif isinstance(node, ast.ObjectPatternExpr):
            self._compile_object_pattern(node)

        elif isinstance(node, ast.LoadStmtAST):
            self._compile_load_stmt(node)

        elif isinstance(node, ast.ImportStmtAST):
            self._compile_import_stmt(node)

        elif isinstance(node, ast.PyASMGroupExpr):
            self._compile_pyasm_group(node)

        elif isinstance(node, ast.PyASMExpr):
            self._compile_pyasm_expr(node)

        elif type(node) in (ast.NonlocalStmtAST, ast.GlobalStmtAST):
            pass  # do not compile

        else:
            self._compile_expr(node)
            if as_stmt:
                if self._mode == 'single':
                    self._add_instruction(PRINT_EXPR, 0, -1)
                else:
                    self._add_instruction(POP_TOP, 0, -1)

    def _enter_next_block(self, block: BasicBlock):
        self._unit.block.next_block = block
        self._unit.block = block

    def _get_firstlineno(self, source: str) -> int:
        for no, ln in enumerate(source.split('\n')):
            if ln:
                return no + 1
        return 1

    def enter_new_scope(
            self, symbol_table: SymbolTable, name: str, firstlineno: int = 1):
        unit = CompileUnit()
        unit.prev_unit = self._unit
        unit.scope = symbol_table
        unit.name = name
        unit.firstlineno = firstlineno
        unit.freevars = tuple(symbol_table.freevars)
        unit.cellvars = tuple(symbol_table.cellvars)
        unit.nlocals = symbol_table.nlocals
        unit.argcount = symbol_table.argcount

        self._unit = unit

        return unit

    def compile(
            self, node: ast.AST, source: str, filename: str,
            firstlineno=-1, mode: str = 'exec'):

        from .pyexec import AIL_CP_MODES

        if mode not in AIL_CP_MODES:
            raise ValueError('compile mode must in (%s, %s %s)' %
                             tuple((repr(x) for x in AIL_CP_MODES)))

        self._mode = mode

        st = SymbolAnalyzer().visit_and_make_symbol_table(
            source, filename, node)

        if firstlineno < 0:
            firstlineno = self._get_firstlineno(source)

        unit = self.enter_new_scope(st, filename, firstlineno)
        unit.filename = filename

        b = BasicBlock()
        self._unit.top_block = b
        self._unit.block = b

        self._compile(node)

        self._add_instruction(
            LOAD_CONST, self._add_const(None), -1
        )
        self._add_instruction(RETURN_VALUE, 0, -1)


class AssembleTask:
    def __init__(self):
        self.bytecode = bytearray()
        self.lnotab = bytearray()
        self.block: BasicBlock = None
        self.compiler: Compiler = None


class Assembler:
    def __init__(self):
        self._task: AssembleTask = None
        self._wish_table: Dict[BasicBlock, List[Instruction]] = {}

    def __set_wish(self, instr: Instruction, offset: int):
        assert instr.target is not None

        wish = self._wish_table
        block = instr.target

        if block not in wish:
            followers = []
            wish[block] = followers
        else:
            followers = wish[block]

        followers.append((instr, offset))

    def _set_jump_instr_argument(
            self, instr: Instruction, offset: int, now_offset: int):
        if instr.is_jabs:
            instr.arg = offset
        if instr.is_jrel:
            instr.arg = offset - now_offset - 2  # skip self

    def _assemble_jump_offset(self):
        not_extended_arg_recompile = True

        while True:
            block = self._task.block
            total_offset = 0
            while block is not None:
                instructions = block.instructions
                block.offset = total_offset

                if block in self._wish_table:
                    for follower, offset in self._wish_table[block]:
                        self._set_jump_instr_argument(
                            follower, block.offset, offset)

                for instr in instructions:
                    if instr.opcode in OPCODE_JUMP:
                        if instr.target.offset == -1:
                            self.__set_wish(instr, total_offset)
                        else:
                            self._set_jump_instr_argument(
                                instr, instr.target.offset, total_offset)
                    total_offset += 2

                block = block.next_block

            if not_extended_arg_recompile:
                break

    def _make_bytecode_sequence(self) -> bytes:
        block = self._task.block

        sequence = bytearray()

        stack_size = 0

        while block is not None:
            for instr in block.instructions:
                effect = instr.stack_effect
                tmp_size = effect + stack_size
                if tmp_size > stack_size:
                    stack_size = tmp_size

                sequence.append(instr.opcode)
                sequence.append(instr.arg)

            block = block.next_block

        self._task.compiler.unit.stack_size = stack_size

        return bytes(sequence)

    def _make_lnotab(self, firstlineno=1) -> bytes:
        line = firstlineno
        ofs_inc = 0
        block = self._task.block

        lnotab = bytearray()

        while block is not None:
            for instr in block.instructions:
                if instr.line != line and instr.line > 0:
                    inc = instr.line - line
                    if inc < 0:
                        inc = 0x100 + inc
                    lnotab.append(ofs_inc)
                    lnotab.append(inc)
                    ofs_inc = 0
                    line = instr.line
                ofs_inc += 2
            block = block.next_block

        return bytes(lnotab)

    def _compute_flags(self) -> int:
        sym = self._task.compiler.unit.scope
        flags = 0

        if isinstance(sym, FunctionSymbolTable):
            flags |= CO_NEWLOCALS | CO_OPTIMIZED

        return flags

    def _make_code(self, code_str: bytes, lnotab: bytes, extra_flags=0) -> CodeType:
        unit = self._task.compiler.unit

        co_flags = extra_flags | unit.flags | self._compute_flags()

        return CodeType(
            unit.argcount,
            unit.posonlyargcount,
            unit.kwonlyargcount,
            unit.nlocals,
            unit.stack_size,
            co_flags,
            code_str,
            tuple(unit.consts),
            tuple(unit.names),
            tuple(unit.varnames),
            unit.filename,
            unit.name,
            unit.firstlineno,
            lnotab,
            tuple(unit.freevars),
            tuple(unit.cellvars),
        )

    def _assemble_block(self, extra_flags: int = 0) -> CodeType:
        self._assemble_jump_offset()
        code_str = self._make_bytecode_sequence()
        lnotab = self._make_lnotab(self._task.compiler.unit.firstlineno)

        return self._make_code(code_str, lnotab, extra_flags)

    def assemble(
            self, block: BasicBlock, compiler: Compiler, extra_flags=0) -> CodeType:
        self._task = AssembleTask()
        self._wish_table.clear()

        self._task.block = block
        self._task.compiler = compiler

        co = self._assemble_block(extra_flags)
        return co


def test():
    from sys import argv, settrace
    from .alex import Lex
    from .aparser import Parser, ASTConverter
    from .test_utils import CFGDisassembler, get_opcode_trader
    from .version import AIL_VERSION
    from .namespace import fill_namespace

    mode = argv[-1] if len(argv) > 1 else 'd'

    source = open('tests/test.ail', encoding='UTF-8').read()
    ts = Lex().lex(source, '<test>')
    node = Parser().parse(ts, source, '<test>')

    if mode not in ('cp', 'rp'):
        compiler = Compiler()
        compiler.compile(node, source, '<test>', mode='exec')

    if mode == 'd':
        disassembler = CFGDisassembler()
        disassembler.disassemble(compiler.unit.top_block, compiler.unit)

    elif mode in ('c', 'cp'):
        from ..debug.dis import dis

        if mode == 'c':
            assembler = Assembler()
            code = assembler.assemble(compiler.unit.top_block, compiler)

            print('using \'dis\' module to perform disassemble: ')
            print('AIL version: %s' % AIL_VERSION)
        else:
            print('using AIL Convertor to convert AIL code:')
            print('AIL version: %s' % AIL_VERSION)
            print('using python builtin compiler to compile AIL code:')
            print('using \'dis\' module to perform disassemble: ')
            converter = ASTConverter()
            py_node = converter.convert_module(node)
            code = compile(py_node, '<test>', 'exec')

        dis(code)

    elif mode in ('r', 'rp', 'rt'):
        if mode in ('r', 'rt'):
            assembler = Assembler()
            code = assembler.assemble(compiler.unit.top_block, compiler)

            if mode == 'rt':
                settrace(get_opcode_trader())

            print('executing the code object generated by AIL')
            print('code object: %s' % code)
        else:
            converter = ASTConverter()
            py_node = converter.convert_module(node)
            code = compile(py_node, '<test>', 'exec')
            print('executing the code object generated by Python')
            print('code object: %s' % code)

        print('AIL version: %s' % AIL_VERSION)
        print('--------------------\n')

        try:
            ns = {}
            fill_namespace(ns)

            exec(
                code,
                ns,
            )
        finally:
            settrace(None)

    elif mode == 'x':
        converter = ASTConverter()
        py_node = converter.convert_module(node)
        code_py = compile(py_node, '<test>', 'exec')

        assembler = Assembler()
        code_ail = assembler.assemble(compiler.unit.top_block, compiler)

        print('compare code object: %s and %s' % (code_py, code_ail))

        attrs = (
            'co_argcount',
            'co_posonlyargcount',
            'co_kwonlyargcount',
            'co_nlocals',
            'co_stacksize',
            'co_flags',
            'co_code',
            'co_consts',
            'co_names',
            'co_varnames',
            'co_freevars',
            'co_cellvars',
            'co_filename',
            'co_name',
            'co_firstlineno',
            'co_lnotab',
        )

        for attr in attrs:
            print('comparing attribute: %s' % attr)
            print('  ail:')
            print('    ' + repr(getattr(code_ail, attr)))
            print('  python:')
            print('    ' + repr(getattr(code_py, attr)))


if __name__ == '__main__':
    test()
