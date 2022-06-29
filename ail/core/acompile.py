
from ast import literal_eval
from typing import List, Tuple, Dict
from types import CodeType

from . import asts as ast
from .pyopcode import *

from .tokentype import AIL_IDENTIFIER, AIL_NUMBER, AIL_STRING

from .symbol import (
    SymbolTable, FunctionSymbolTable, ClassSymbolTable, SymbolAnalyzer,
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


FB_TRY = 0x1
FB_LOOP = 0x2
FB_WITH = 0x4


class FrameBlock:
    def __init__(self, fb_type: int):
        self.fb_type = fb_type

    
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
        self.freevars: List[str] = []
        self.cellvars: List[str] = []
        self.stack_size = 0
        self.argcount = 0
        self.posonlyargcount = 0
        self.kwonlyargcount = 0
        self.nlocals = 0
        self.flags = 0

        self.prev_unit: CompileUnit = None
        self.firstlineno: int = 1

        self.fb_stack: List[FrameBlock] = []


class Compiler:
    def __init__(self):
        self._unit: CompileUnit = None
    
    @property
    def unit(self) -> CompileUnit:
        return self._unit

    def _check_oparg(self, arg: int, ln: int) -> int:
        final = arg & 0xff
        if arg > 1 << 16:
            self._add_instruction(EXTENDED_ARG, arg >> 16, ln, False)
            self._add_instruction(EXTENDED_ARG, (arg >> 8) & 0xff, ln, False)
        elif arg > 1 << 8:
            self._add_instruction(EXTENDED_ARG, arg >> 8, ln, False)
        return final

    def _check_stack_effect(self, op):
        if op in OPCODE_STACK_EFFECT:
            effect = OPCODE_STACK_EFFECT[op]
        else:
            effect = 0

        stack_size = self._unit.stack_size
        if stack_size + effect > stack_size:
            self._unit.stack_size = stack_size + effect

    def _add_instruction(self, op: int, arg: int, ln: int, check=True) -> int:
        """
        :returns: returns the offset from head of this instruction
        """

        if check:
            self._check_oparg(arg, ln)
        self._check_stack_effect(op)

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

    def _compile_const(self, cell: ast.CellAST):
        value = literal_eval(cell.value)
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

        if symbol.flag & SYM_LOCAL:
            ni = self._add_varname(name)
            self._add_instruction(LOAD_FAST, ni, ln)
        elif symbol.flag & SYM_GLOBAL:
            ni = self._add_varname(name)
            self._add_instruction(LOAD_GLOBAL, ni, ln)
        elif symbol.flag & SYM_NORMAL:
            ni = self._add_name(name)
            self._add_instruction(LOAD_NAME, ni, ln)

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

    def _compile_expr(self, expr: ast.Expression):
        if isinstance(expr, ast.CellAST):
            return self._compile_cell(expr)
        elif type(expr) in ast.BIN_OP_AST:
            self._compile_binary_expr(expr)

    def _compile_block(self, block: ast.BlockAST):
        stmts = block.stmts

        for stmt in stmts:
            self._compile(stmt)

    def _compile(self, node: ast.AST):
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

        else:
            self._compile_expr(node)

    def _enter_next_block(self, block: BasicBlock):
        self._unit.block.next_block = block
        self._unit.block = block

    def enter_new_scope(
            self, symbol_table: SymbolTable, name: str, firstlineno: int=1):
        unit = CompileUnit()
        unit.prev_unit = self._unit
        unit.scope = symbol_table
        unit.name = name
        unit.firstlineno = firstlineno

        self._unit = unit

    def compile(
            self, node: ast.AST, source: str, filename: str, firstlineno=1):
        st = SymbolAnalyzer().visit_and_make_symbol_table(
                source, filename, node)
        self.enter_new_scope(st, filename, firstlineno)

        b = BasicBlock()
        self._unit.top_block = b
        self._unit.block = b

        self._compile(node)


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
            block = block.next_block
            for instr in block.instructions:
                sequence.append(instr.opcode)
                sequence.append(instr.arg)

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

        return bytes(lnotab)

    def _make_code(self, code_str: bytes, lnotab: bytes) -> CodeType:
        unit = self._task.compiler.unit

        return CodeType(
            argcount=unit.argcount,
            posonlyargcount=unit.posonlyargcount,
            kwonlyargcount=unit.kwonlyargcount,
            nlocals=unit.nlocals,
            stacksize=unit.stack_size,
            flags=unit.flags,
            codestring=code_str,
            constants=tuple(unit.consts),
            names=tuple(unit.names),
            varnames=tuple(unit.varnames),
            filename=unit.filename,
            name=unit.name,
            firstlineno=unit.firstlineno,
            lnotab=lnotab,
            freevars=tuple(unit.freevars),
            cellvars=tuple(unit.cellvars),
        )

    def _assemble_block(self):
        self._assemble_jump_offset()
        bytecode_seq = self._make_bytecode_sequence()
        lnotab = self._make_lnotab(self._task.compiler.unit.firstlineno)

    def assemble(self, block: BasicBlock, compiler: Compiler):
        self._task = AssembleTask()
        self._wish_table.clear()

        self._task.block = block
        self._task.compiler = compiler


def test():
    from .alex import Lex
    from .aparser import Parser
    from .test_utils import CFGDisassembler

    source = open('tests/test.ail').read()
    ts = Lex().lex(source, '<test>')
    node = Parser().parse(ts, source, '<test>')
    
    compiler = Compiler()
    compiler.compile(node, source, '<test>')
    
    disassembler = CFGDisassembler()
    disassembler.disassemble(compiler.unit.top_block, compiler.unit)


if __name__ == '__main__':
    test()

