
from typing import List

from . import asts as ast
from .error import error_msg


SYM_FREE = 0x1
SYM_LOCAL = 0x2
SYM_GLOBAL = 0x3

CTX_LOAD = 0x1
CTX_STORE = 0x2


def _do_mangle(cls_name: str, name: str) -> str:
    if cls_name == '':
        return name

    if name[:2] == '__' and name[-2:] != '__':
        return '__%s_%s' % (cls_name, name)

    return name


class Symbol:
    def __init__(self, name):
        self.name: str = name
        self.flag: int = 0
        self.namespace: 'SymbolTable' = None
        self.ln = 0

    def __eq__(self, other: 'Symbol'):
        return other.name == self.name


class SymbolTable:
    def __init__(self):
        self.symbols: List[Symbol] = []
        self.global_directives: List[str] = []
        self.nonlocal_directives: List[str] = []
        self.cur_class: str = ''
        self.prev_table: 'SymbolTable' = None

    def is_global(self, symbol: Symbol) -> bool:
        if self.prev_table is None:
            # so this is the symbol table for global scope
            return symbol in self.symbols
        return self.prev_table.is_global(symbol)

    def _check_free(self, symbol: Symbol):
        if self.prev_table is None:
            # the global scope cannot check free variable
            return False

        if symbol in self.symbols:
            return True
        return False

    def is_free(self, symbol: Symbol) -> int:
        assert self.prev_table is not None
        if self.prev_table is not None:
            return self.prev_table._check_free(symbol)


class FunctionSymbolTable(SymbolTable):
    pass


class ClassSymbolTable(SymbolTable):
    pass


class SymbolAnalyzer:
    def __init__(self):
        self.__symbol_table: SymbolTable = None
        self.__filename = ''
        self.__source = ''

    def __add_symbol(self, symbol: Symbol):
        self.__symbol_table.symbols.append(symbol)

    def __syntax_error(self, msg: str, ln: int):
        error_msg(ln, msg, self.__filename, source=self.__source)

    def _analyze_and_fill_symbol(self, symbol: Symbol, ctx: int) -> Symbol:
        name = symbol.name

        if ctx == CTX_STORE:
            if isinstance(self.__symbol_table, FunctionSymbolTable):
                symbol.flag |= SYM_LOCAL
            assert isinstance(self.__symbol_table, SymbolTable)
            symbol.flag |= SYM_GLOBAL
            return Symbol
        assert ctx == CTX_LOAD

        if self.__symbol_table.is_free(symbol):
            symbol.flag |= SYM_FREE
        elif self.__symbol_table.is_global(symbol):
            symbol.flag |= SYM_GLOBAL
        else:
            symbol.flag |= SYM_LOCAL

        return symbol

    def _visit_assign_expr(self, expr: ast.AssignExprAST):
        self._visit(expr.right)

        left = []

        if isinstance(expr.left, ast.TupleAST):
            left = expr.left.items
        else:
            left.append(expr.left)

        for target in left:
            if isinstance(target, ast.CellAST):
                self.__add_symbol(
                    self._analyze_and_fill_symbol(Symbol(target.value), CTX_STORE))

    def _visit(self, node: ast.AST):
        if isinstance(node, ast.AssignExprAST):
            self._visit_assign_expr(node)

    def set_symbol_table(self, symbol_table: SymbolTable):
        self.__symbol_table = symbol_table

    def visit_and_make_symbol_table(self, source: str, filename: str):
        pass
