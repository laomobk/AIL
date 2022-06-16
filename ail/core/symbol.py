
from typing import List

from . import asts as ast
from .error import error_msg


SYM_FREE = 0x1
SYM_LOCAL = 0x2
SYM_GLOBAL = 0x4
SYM_REFERENCE = 0x8

CTX_LOAD = 0x1
CTX_STORE = 0x2


def _do_mangle(cls_name: str, name: str) -> str:
    if cls_name == '':
        return name

    if name[:2] == '__' and name[-2:] != '__':
        return '__%s_%s' % (cls_name, name)

    return name


def _get_first_cell(expr) -> ast.CellAST:
    if type(expr) not in (
            ast.CellAST, ast.SubscriptExprAST, ast.MemberAccessAST):
        return expr
    if isinstance(expr, ast.CellAST):
        return expr
    return _get_first_cell(expr.left)


class Symbol:
    def __init__(self, name):
        self.name: str = name
        self.flag: int = 0
        self.namespace: 'SymbolTable' = None

    def __eq__(self, other: 'Symbol'):
        return other.name == self.name

    def __str__(self):
        return '<Symbol %s>' % repr(self.name)

    __repr__ = __str__


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

        if isinstance(self.__symbol_table, FunctionSymbolTable) and \
                self.__symbol_table.is_free(symbol):
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
                s = self._analyze_and_fill_symbol(
                        Symbol(target.value), CTX_STORE)
                self.__add_symbol(s)
                target.symbol = s
            elif isinstance(target, ast.MemberAccessAST) or \
                 isinstance(target, ast.SubscriptExprAST):
                name = _get_first_cell(target)
                s = self._analyze_and_fill_symbol(
                        Symbol(name.value), CTX_LOAD)
                name.symbol = s
                self.__add_symbol(s)
            else:
                raise TypeError('invalid target type: %s' % type(target))

    def _visit_block(self, block: ast.BlockAST):
        stmts = block.stmts

        for stmt in stmts:
            self._visit(stmt)

    def _visit(self, node: ast.AST):
        if isinstance(node, ast.BlockAST):
            self._visit_block(node)
        elif isinstance(node, ast.AssignExprAST):
            self._visit_assign_expr(node)

    def set_symbol_table(self, symbol_table: SymbolTable):
        self.__symbol_table = symbol_table

    def visit_and_make_symbol_table(
            self, source: str, filename: str, top_ast: ast.ProgramBlock, 
            symbol_table: SymbolTable = None) -> SymbolTable:
        self.__source = source
        self.__filename = filename

        if symbol_table is None:
            symbol_table = SymbolTable()
        self.__symbol_table = symbol_table

        self._visit(top_ast)
        
        return self.__symbol_table

