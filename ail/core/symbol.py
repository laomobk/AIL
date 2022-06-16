from typing import List

from . import asts as ast

from .error import error_msg
from .tokentype import AIL_IDENTIFIER

SYM_FREE = 0x1
SYM_LOCAL = 0x2
SYM_GLOBAL = 0x4
SYM_REFERENCE = 0x8
SYM_NONLOCAL = 0x10

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


def _visit_param_list(
        symbol_table: 'SymbolTable', param_list: ast.ArgListAST):

    for param in param_list.arg_list:
        assert isinstance(param.expr, ast.CellAST) and \
               param.expr.type == AIL_IDENTIFIER

        symbol = Symbol(param.expr.value)
        symbol.flag |= SYM_LOCAL
        symbol_table.add_symbol(symbol)


class Symbol:
    def __init__(self, name, flag=0, namespace: 'SymbolTable' = None):
        self.name: str = name
        self.flag: int = flag
        self.namespace: 'SymbolTable' = namespace

    def __eq__(self, other: 'Symbol'):
        return other.name == self.name

    def __str__(self):
        return '<Symbol %s flag %s>' % (repr(self.name), bin(self.flag))

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

    def add_symbol(self, symbol: Symbol):
        symbols = self.symbols

        for sym in symbols:
            if sym.flag == symbol.flag and sym.name == symbol.name:
                return

        symbols.append(symbol)


class FunctionSymbolTable(SymbolTable):
    pass


class ClassSymbolTable(SymbolTable):
    pass


class SymbolAnalyzer:
    def __init__(self):
        self.__symbol_table: SymbolTable = None
        self.__filename = ''
        self.__source = ''
        self.__block_queue = []

    def __add_symbol(self, symbol: Symbol):
        self.__symbol_table.add_symbol(symbol)

    def __syntax_error(self, msg: str, ln: int):
        error_msg(ln, msg, self.__filename, source=self.__source)

    def _analyze_and_fill_symbol(self, symbol: Symbol, ctx: int) -> Symbol:
        name = symbol.name

        if ctx == CTX_STORE:
            if isinstance(self.__symbol_table, FunctionSymbolTable):
                if name in self.__symbol_table.global_directives:
                    symbol.flag |= SYM_GLOBAL
                elif name in self.__symbol_table.nonlocal_directives:
                    symbol.flag |= SYM_NONLOCAL
                else:
                    symbol.flag |= SYM_LOCAL
                return symbol
            assert isinstance(self.__symbol_table, SymbolTable)
            symbol.flag |= SYM_GLOBAL
            return symbol

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
                    Symbol(name.value), CTX_STORE)
                name.symbol = s
                self.__add_symbol(s)
            else:
                raise TypeError('invalid target type: %s' % type(target))

    def _visit_block(self, block: ast.BlockAST):
        stmts = block.stmts

        for stmt in stmts:
            self._visit(stmt)

    def _visit_binary_expr(self, expr):
        self._visit(expr.left)
        self._visit(expr.right)

    def _visit_cell(self, cell: ast.CellAST):
        if cell.type != AIL_IDENTIFIER:
            return

        s = self._analyze_and_fill_symbol(Symbol(cell.value), CTX_LOAD)
        cell.symbol = s
        self.__add_symbol(s)

    def _visit_call_expr(self, expr: ast.CallExprAST):
        self._visit(expr.left)

        for arg in expr.arg_list.arg_list:
            self._visit(arg.expr)

    def _visit_queue(self):
        for node in self.__block_queue:
            if isinstance(node, ast.FunctionDefineAST):
                node: ast.FunctionDefineAST

                body: ast.BlockAST = node.block
                table = FunctionSymbolTable()
                table.prev_table = self.__symbol_table

                analyzer = SymbolAnalyzer()
                table = analyzer.visit_and_make_symbol_table(
                    self.__source, self.__filename, body, table
                )

    def _visit(self, node: ast.AST):
        if isinstance(node, ast.BlockAST):
            self._visit_block(node)

        elif isinstance(node, ast.AssignExprAST):
            self._visit_assign_expr(node)

        elif isinstance(node, ast.CellAST):
            self._visit_cell(node)

        elif isinstance(node, ast.CallExprAST):
            self._visit_call_expr(node)

        elif type(node) in ast.BINARY_AST_TYPES:
            self._visit_binary_expr(node)

        elif isinstance(node, ast.NamespaceStmt):
            s = self._analyze_and_fill_symbol(Symbol(node.name), CTX_STORE)
            self.__add_symbol(s)
            self.__block_queue.append(node)

        elif isinstance(node, ast.FunctionDefineAST):
            name_symbol = self._analyze_and_fill_symbol(Symbol(node.name), CTX_STORE)
            self.__add_symbol(name_symbol)
            bandto_symbol = self._analyze_and_fill_symbol(Symbol(node.bindto), CTX_LOAD)
            self.__add_symbol(bandto_symbol)
            self.__block_queue.append(node)

        elif isinstance(node, ast.ClassDefineAST):
            self._visit(node.meta)
            for base in node.bases:
                self._visit(base)
            s = self._analyze_and_fill_symbol(Symbol(node.name), CTX_STORE)
            self.__add_symbol(s)
            self.__block_queue.append(node)

    def set_symbol_table(self, symbol_table: SymbolTable):
        self.__symbol_table = symbol_table

    def visit_and_make_symbol_table(
            self, source: str, filename: str, node: ast.BlockAST,
            symbol_table: SymbolTable = None) -> SymbolTable:
        self.__source = source
        self.__filename = filename

        if symbol_table is None:
            symbol_table = SymbolTable()
        self.__symbol_table = symbol_table

        self._visit(node)

        return self.__symbol_table
