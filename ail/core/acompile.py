
from typing import List, Tuple
from types import CodeType

from . import asts as ast
from .pyopcode import *

from .tokentype import AIL_IDENTIFIER, AIL_NUMBER, AIL_STRING

from .symbol import (
    SymbolTable, FunctionSymbolTable, ClassSymbolTable,
    SYM_LOCAL, SYM_GLOBAL, SYM_NONLOCAL, SYM_FREE
)

CTX_LOAD = 0x1
CTX_STORE = 0x2

COMPILE_FLAG_GLOBAL = 0x1
COMPILE_FLAG_FUNC = 0x2


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
                 is_jabs=False, is_jrel=False, target=0,
                 line=0):
        self.opcode = opcode
        self.arg = arg

        self.is_jabs = is_jabs
        self.is_jrel = is_jrel
        self.target = target

        self.line = line


class BasicBlock:
    def __init__(self, leader: Instruction):
        self.leader: Instruction = leader
        self.instructions = [leader]
        self.next_block: 'BasicBlock' = None

    def add_instruction(self, instr: Instruction) -> int:
        self.instructions.append(instr)
        return len(self.instructions) - 1


class Compiler:
    def __init__(self):
        self._current_block: BasicBlock = None
        self._current_scope: SymbolTable = None

        self._varnames: List[str] = []
        self._consts: List[object] = []
        self._varname: List[str] = []
        self._freevars = List[str] = []
        self._cellvars = List[str] = []
        self._stack_size = 0

    def _check_oparg(self, arg: int, ln: int) -> int:
        final = arg & 0xff
        if arg > 1 << 16:
            self._add_instruction(EXTENDED_ARG, arg >> 16, ln, False)
            self._add_instruction(EXTENDED_ARG, (arg >> 8) & 0xff, ln, False)
        elif arg > 1 << 8:
            self._add_instruction(EXTENDED_ARG, arg >> 8, ln, False)
        return final

    def _add_instruction(self, op: int, arg: int, ln: int, check=True) -> int:
        """
        :returns: returns the offset from head of this instruction
        """
        if check:
            arg = self._check_oparg(arg, ln)

        effect = OPCODE_STACK_EFFECT[op]
        stack_size = self._stack_size
        if stack_size + effect > stack_size:
            self._stack_size = stack_size + effect

        instr = Instruction()
        instr.line = ln
        instr.arg = arg

        return self._current_block.add_instruction(instr)

    def _add_const(self, const: object) -> int:
        if const in self._consts:
            return self._consts.index(const)
        self._consts.append(const)
        return len(self._consts) - 1

    def _add_varname(self, name: str) -> int:
        if name in self._varnames:
            return self._varnames.index(name)
        self._varnames.append(name)
        return len(self._varnames) - 1

    def _compile_const(self, cell: ast.CellAST):
        value = cell.value
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

    def _compile_cell(self, cell: ast.CellAST):
        pass

    def _compile_if(self, stmt: ast.IfStmtAST):
        pass

    def compile(self, node: ast.AST):
        self._current_block = BasicBlock(Instruction())
