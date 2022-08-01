
from ast import literal_eval
from typing import List, Tuple, Dict
from types import CodeType

from . import asts as ast
from .pyopcode import *

from .tokentype import AIL_IDENTIFIER, AIL_NUMBER, AIL_STRING

from .symbol import (
    SymbolTable, FunctionSymbolTable, ClassSymbolTable, SymbolAnalyzer, Symbol,
    SYM_LOCAL, SYM_GLOBAL, SYM_NONLOCAL, SYM_FREE, SYM_NORMAL
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

        self.line = line


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
    pass


class WhileFrameBlock(FrameBlock):
    def __init__(self, start: BasicBlock, body: BasicBlock, next_: BasicBlock):
        self.start = start
        self.body = body
        self.next = next_

    
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
        self._frame_stack: List[FrameBlock] = []
    
    @property
    def unit(self) -> CompileUnit:
        return self._unit

    def push_frame(self, frame: FrameBlock):
        self._frame_stack.append(frame)

    def pop_frame(self) -> FrameBlock:
        return self._frame_stack.pop()

    def _frame(self, frame: FrameBlock):
        return Compiler.__FrameStackManager(self, frame)

    def _check_oparg(self, arg: int, ln: int) -> int:
        final = arg & 0xff
        if arg >= 1 << 16:
            self._add_instruction(EXTENDED_ARG, arg >> 16, ln, False)
            self._add_instruction(EXTENDED_ARG, (arg >> 8) & 0xff, ln, False)
        elif arg >= 1 << 8:
            self._add_instruction(EXTENDED_ARG, arg >> 8, ln, False)
        return final

    def _check_stack_effect(self, op, stack_effect=None):
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
        
        self._unit._cur_stack_size = self._unit._cur_stack_size + effect
        cur_stack_size = self._unit._cur_stack_size

        stack_size = self._unit.stack_size
        if cur_stack_size > stack_size:
            self._unit.stack_size = cur_stack_size

    def _new_call_name(self, name: str, args: list, ln: int):
        self._add_instruction(LOAD_GLOBAL)
        for expr in args:
            self._compile(expr)

    def _add_instruction(
            self, op: int, arg: int, ln: int, 
            check=True, stack_effect=None) -> int:
        """
        :returns: returns the offset from head of this instruction
        """

        if check:
            arg = self._check_oparg(arg, ln)
        self._check_stack_effect(op, stack_effect)

        instr = Instruction()
        instr.line = ln
        instr.arg = arg
        instr.opcode = op

        return self._unit.block.add_instruction(instr)

    def _add_jump_op(self, op: int, target: BasicBlock, ln: int):
        instr = Instruction()
        instr.is_jabs = op != JUMP_FORWARD
        instr.is_jrel = op == JUMP_FORWARD
        instr.target = target
        instr.line = ln
        instr.arg = 0
        instr.opcode = op

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

    def _unwind_frame_block(self, block: FrameBlock):
        pass

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

        if name in self._unit.cellvars:
            self._add_instruction(
                LOAD_DEREF, self._unit.cellvars.index(name), cell.ln,
            )
        elif name in self._unit.freevars:
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
            self, name: str, args: List[ast.Expression], ln: int, ctx=None):
        if ctx is None:
            ctx = SYM_GLOBAL

        left = ast.CellAST(name, AIL_IDENTIFIER, ln)
        left.symbol = Symbol(name, ctx)

        self._compile_call_expr(
            ast.CallExprAST(
                left, 
                ast.ArgListAST(
                    [ast.ArgItemAST(e, False, e.ln) 
                        for e in args],
                    ln
                ),
                ln
            )
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
        instr.opcode = JUMP_IF_TRUE_OR_POP if condition else JUMP_IF_FALSE_OR_POP
        instr.line = expr.ln

        self._unit.block.add_instruction(instr)

    def _compile_if(self, stmt: ast.IfStmtAST):
        if_block = BasicBlock()
        next_block: BasicBlock = BasicBlock()

        self._compile_if_jump(stmt.test, 0, next_block)
        self._enter_next_block(if_block)
        self._compile(stmt.block)

        if len(stmt.else_block.stmts) != 0:
            self._add_jump_op(JUMP_FORWARD, next_block, -1)

        self._enter_next_block(next_block)
        self._compile_block(stmt.else_block)

    def _compile_binary_expr(self, expr):
        self._compile_expr(expr.left)

        for op, right in expr.right:
            self._compile_expr(right)
            opc = BIN_OP_MAP[op]
            self._add_instruction(opc, 0, right.ln)

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

    def _compile_call_arg(self, arg_list: ast.ArgListAST):
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
                CALL_FUNCTION, len(posarg), arg_list.ln,
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
                            stack_effect=-pos_arg_count+1
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
                    if pos_arg_count > 0 and in_pos_arg:
                        self._add_instruction(
                            BUILD_TUPLE, pos_arg_count, -1,
                            stack_effect=-pos_arg_count+1
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

    def _compile_call_expr(self, expr: ast.CallExprAST):
        self._compile(expr.left)

        self._compile_call_arg(expr.arg_list)

    def _compile_print_stmt(self, stmt: ast.PrintStmtAST):
        self._compile_call_name(
            'print', stmt.value_list, stmt.ln,
        )
        self._add_instruction(POP_TOP, 0, -1)

    def _compile_assign_expr(self, expr: ast.AssignExprAST, as_stmt=False):
        left = expr.left
        if not isinstance(left, ast.TupleAST):
            left = [left]
        else:
            left = left.items

        self._compile(expr.right)
        if not as_stmt:
            self._add_instruction(DUP_TOP, 0, -1)

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

    def _compile_store(self, target: ast.Expression):
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
            self._add_instruction(
                STORE_ATTR, self._add_name(target.member.value), target.ln)

    def _compile_while_stmt(self, stmt: ast.WhileStmtAST):
        start = BasicBlock()
        body = BasicBlock()
        next_ = BasicBlock()

        frame = WhileFrameBlock(start, body, next_)

        with self._frame(frame):
            self._enter_next_block(start)
            self._compile_if_jump(stmt.test, 0, next_)

            self._enter_next_block(body)
            self._compile(stmt.block)
            self._add_jump_op(JUMP_ABSOLUTE, start, -1)

        self._enter_next_block(next_)

    def _compile_break_stmt(self, stmt: ast.BreakStmtAST):
        frame = self._frame_stack[-1]

        index = len(self._frame_stack) - 2
        while type(frame) not in (WhileFrameBlock, ):
            self._unwind_frame_block(frame)
            frame = self._frame_stack[index]
            index -= 1

        if isinstance(frame, WhileFrameBlock):
            self._add_jump_op(JUMP_ABSOLUTE, frame.next, stmt.ln)

    def _compile_function(self, func: ast.FunctionDefineAST, as_stmt=False):
        sym: SymbolTable = func.symbol.namespace

        frees = sym.freevars
        unit = self._unit

        b = BasicBlock()
        self.enter_new_scope(sym, func.name, func.block.ln)
        self._unit.block = b
        self._unit.top_block = b

        self._compile_block(func.block)

        self._add_instruction(
            LOAD_CONST, self._add_const(None), -1
        )
        self._add_instruction(RETURN_VALUE, 0, -1)

        assembler = Assembler()
        code = assembler.assemble(self._unit.top_block, self)

        self._unit = unit

        effect = -1
        flag = 0

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
                    raise CompilerError('closure name neither in freevars nor cellvars')
            self._add_instruction(
                BUILD_TUPLE, len(frees), -1, stack_effect=-len(frees)+1,
            )
            flag = 0x8
            effect = -2

        self._add_instruction(LOAD_CONST, self._add_const(code), func.ln)
        self._add_instruction(LOAD_CONST, self._add_const(func.name), -1)
        self._add_instruction(
            MAKE_FUNCTION, flag, func.ln,
            stack_effect=effect,
        )

        if as_stmt:
            cell = ast.CellAST(func.name, AIL_IDENTIFIER, func.ln)
            cell.symbol = func.symbol
            self._compile_store(cell)

    def _compile_continue_stmt(self, stmt: ast.BreakStmtAST):
        frame = self._frame_stack[-1]

        index = len(self._frame_stack) - 2
        while type(frame) not in (WhileFrameBlock,):
            self._unwind_frame_block(frame)
            frame = self._frame_stack[index]
            index -= 1

        if isinstance(frame, WhileFrameBlock):
            self._add_jump_op(JUMP_ABSOLUTE, frame.start, stmt.ln)

    def _compile_member_access_expr(self, expr: ast.MemberAccessAST):
        self._compile_expr(expr.left)
        self._add_instruction(
            LOAD_ATTR, self._add_name(expr.member.value), expr.ln,
            stack_effect=1,
        )

    def _compile_expr(self, expr: ast.Expression):
        if isinstance(expr, ast.CellAST):
            return self._compile_cell(expr)

        elif isinstance(expr, ast.CallExprAST):
            return self._compile_call_expr(expr)

        elif isinstance(expr, ast.MemberAccessAST):
            return self._compile_member_access_expr(expr)

        elif type(expr) in ast.BIN_OP_AST:
            self._compile_binary_expr(expr)

    def _compile_block(self, block: ast.BlockAST):
        stmts = block.stmts

        for stmt in stmts:
            self._compile(stmt, as_stmt=True)

    def _compile(self, node: ast.AST, as_stmt: bool = False):
        if isinstance(node, ast.BlockAST):
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

        elif isinstance(node, ast.FunctionDefineAST):
            self._compile_function(node, True)

        elif type(node) in (ast.NonlocalStmtAST, ast.GlobalStmtAST):
            pass  # do not compile

        else:
            self._compile_expr(node)
            if as_stmt:
                self._add_instruction(POP_TOP, 0, -1)

    def _enter_next_block(self, block: BasicBlock):
        self._unit.block.next_block = block
        self._unit.block = block

    def _get_firstlineno(self, source: str) -> int:
        for no, ln in enumerate(source.split('\n')):
            if ln:
                return no + 1

    def enter_new_scope(
            self, symbol_table: SymbolTable, name: str, firstlineno: int=1):
        unit = CompileUnit()
        unit.prev_unit = self._unit
        unit.scope = symbol_table
        unit.name = name
        unit.firstlineno = firstlineno
        unit.freevars = tuple(symbol_table.freevars)
        unit.cellvars = tuple(symbol_table.cellvars)
        unit.nlocals = symbol_table.nlocals

        self._unit = unit

    def compile(
            self, node: ast.AST, source: str, filename: str, firstlineno=-1):
        st = SymbolAnalyzer().visit_and_make_symbol_table(
                source, filename, node)

        if firstlineno < 0:
            firstlineno = self._get_firstlineno(source)

        self.enter_new_scope(st, filename, firstlineno)

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

    def __set_wish(self, instr: Instruction):
        assert instr.target is not None

        wish = self._wish_table
        block = instr.target

        if block not in wish:
            followers = []
            wish[block] = followers
        else:
            followers = wish[block]

        followers.append(instr)

    def _set_jump_instr_argument(
            self, instr: Instruction, offset: int, now_offset: int):
        if instr.is_jabs:
            instr.arg = offset
        if instr.is_jrel:
            instr.arg = offset - now_offset

    def _assemble_jump_offset(self):
        block = self._task.block
        total_offset = 0

        while block is not None:
            instructions = block.instructions
            block.offset = total_offset

            if block in self._wish_table:
                for follower in self._wish_table[block]:
                    self._set_jump_instr_argument(
                        follower, block.offset, total_offset)

            for instr in instructions:
                if instr.opcode in OPCODE_JUMP:
                    if instr.target.offset == -1:
                        self.__set_wish(instr)
                    else:
                        self._set_jump_instr_argument(
                            instr, instr.target.offset, total_offset)
                total_offset += 2

            block = block.next_block

    def _make_bytecode_sequence(self) -> bytes:
        block = self._task.block

        sequence = bytearray()

        while block is not None:
            for instr in block.instructions:
                sequence.append(instr.opcode)
                sequence.append(instr.arg)
            block = block.next_block

        return bytes(sequence)

    def _make_lnotab(self, firstlineno=1) -> bytes:
        line = firstlineno
        ofs_inc = 0
        block = self._task.block

        lnotab = bytearray()

        while block is not None:
            for instr in block.instructions:
                if instr.line > line:
                    inc = instr.line - line
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

    def _make_code(self, code_str: bytes, lnotab: bytes) -> CodeType:
        unit = self._task.compiler.unit

        return CodeType(
            unit.argcount,
            unit.posonlyargcount,
            unit.kwonlyargcount,
            unit.nlocals,
            unit.stack_size,
            unit.flags,
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

    def _assemble_block(self) -> CodeType:
        self._assemble_jump_offset()
        code_str = self._make_bytecode_sequence()
        lnotab = self._make_lnotab(self._task.compiler.unit.firstlineno)

        return self._make_code(code_str, lnotab)

    def assemble(self, block: BasicBlock, compiler: Compiler) -> CodeType:
        self._task = AssembleTask()
        self._wish_table.clear()

        self._task.block = block
        self._task.compiler = compiler

        return self._assemble_block()


def test():
    from sys import argv
    from .alex import Lex
    from .aparser import Parser, ASTConverter
    from .test_utils import CFGDisassembler
    from .version import AIL_VERSION

    mode = argv[-1] if len(argv) > 1 else 'd'

    source = open('tests/test.ail', encoding='UTF-8').read()
    ts = Lex().lex(source, '<test>')
    node = Parser().parse(ts, source, '<test>')
    
    if mode != 'cp':
        compiler = Compiler()
        compiler.compile(node, source, '<test>')

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

    elif mode in ('r', 'rp'):
        if mode == 'r':
            assembler = Assembler()
            code = assembler.assemble(compiler.unit.top_block, compiler)

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
        exec(
            code, 
            {
                'write': print,
                'fx': lambda a, b, c, d: print(a, b, c, d),
                'd': {'d': 4},
                'a': 1,
                'b': 2,
                'c': 3,
            },
        )

    elif mode == 'x':
        converter = ASTConverter()
        py_node = converter.convert_module(node)
        code_py = compile(py_node, '<test>', 'exec').co_consts[0]

        assembler = Assembler()
        code_ail = assembler.assemble(compiler.unit.top_block, compiler).co_consts[0]

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

