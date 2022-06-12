from dataclasses import dataclass
from typing import List
from types import CodeType

from . import asts as ast
from . import pyopcode as opcode

from .symbol import SymbolTable
from .tokentype import AIL_NUMBER, AIL_STRING, AIL_IDENTIFIER


class CompilerError(Exception):
    pass


class DynamicArg:
    def __init__(self, value: int = 0):
        self.value = value


class DynamicInstruction:
    def __init__(self, instr: int = 0):
        self.instr = instr


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
        effect = opcode.OPCODE_STACK_EFFECT.get(instr, 0)

        if stack_effect is opcode.EFCT_DYNAMIC_EFFECT and stack_effect is None:
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
            self.__append_bytecode(opcode.EXTENDED_ARG, arg >> 8)
            size += 2
            arg &= 0xff

        self.code.append(instr)
        self.code.append(arg)
        size += 2

        self._check_lno(line, size)

        return size


class Block:
    def __init__(self, block_type: int):
        self.block_type = block_type


class CompilerState:
    def __init__(self):
        self.block_stack: List[Block] = []
        self.cobj_buffer: CodeObjectBuffer = None
        self.defined_name: List[str] = []


@dataclass
class GeneralCompileState:
    def __init__(self):
        # level = 0: global
        # level = 1: inside single level function
        # level > 1: inside a function which inside a function
        level: int
        symbol_table = SymbolTable()


class GenericPyCodeCompiler:
    def __init__(self, general_state: GeneralCompileState):
        self.__state = CompilerState()
        self.__general_state = general_state

    @property
    def cobj_buffer(self) -> CodeObjectBuffer:
        return self.__state.cobj_buffer

    def _get_defined_names(self, body: ast.BlockAST, names: List[str]):
        for stmt in body.stmts:
            name = None
            if isinstance(stmt, ast.FunctionDefineAST):
                name = stmt.name
            elif isinstance(stmt, ast.ClassDefineAST):
                name = stmt.name
            elif isinstance(stmt, ast.NamespaceStmt):
                name = stmt.name
            elif isinstance(stmt, ast.StructDefineAST):
                name = stmt.name
            else:
                continue

            names.append(name)

    def _visit_and_get_freevars(
            self, body: ast.BlockAST, freevars: List[str]) -> List[str]:
        defined_names = []
        self._get_defined_names(body, defined_names)

        for stmt in body.stmts:
            stmt

    def _compile_cell(self, cell: ast.CellAST):
        if cell.type in (AIL_STRING, AIL_NUMBER):
            ci = self.cobj_buffer.add_const(cell.value)
            self.cobj_buffer.add_bytecode(opcode.LOAD_CONST, ci, cell.ln)
            return
        name = cell.value
        load_instr = opcode.LOAD_NAME
        if self.__general_state.level > 1:
            if name in self.__state.defined_name:
                load_instr = opcode.LOAD_FAST
            else:
                load_instr = opcode.LOAD_DEREF

    def _compile_node(self, node: ast.AST):
        if isinstance(node, ast.CellAST):
            pass

    def compile(self, node: ast.AST, firstlineno=1) -> CodeType:
        self.__state.cobj_buffer = CodeObjectBuffer(firstlineno=firstlineno)

        self._compile_node(node)

        return None
