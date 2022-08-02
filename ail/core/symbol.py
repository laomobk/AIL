from typing import List, Set

from . import asts as ast

from .error import error_msg
from .tokentype import AIL_IDENTIFIER, AIL_CONSTANTS

SYM_FREE = 0x1
SYM_LOCAL = 0x2
SYM_GLOBAL = 0x4
SYM_REFERENCE = 0x8
SYM_NONLOCAL = 0x10
SYM_NORMAL = 0x20

FROM_STORE = 0x1
FROM_IMPORT = 0x2
FROM_PARAMETER = 0x4

CTX_LOAD = 0x1
CTX_STORE = 0x2


def do_mangle(cls_name: str, name: str) -> str:
    return '_%s%s' % (cls_name, name)


def check_mangle(name: str):
    return name[:2] == '__' and name[-2:] != '__'


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
        symbol.from_flag = FROM_PARAMETER
        symbol_table.add_symbol(symbol)
        param.expr.symbol = symbol
        symbol_table.local_maybe.add(param.expr.value)


class Symbol:
    def __init__(
            self, name, flag=0,
            namespace: 'SymbolTable' = None, from_flag=FROM_STORE):
        self.name: str = name
        self.flag: int = flag
        self.from_flag: int = from_flag
        self.namespace: 'SymbolTable' = namespace

    def __eq__(self, other: 'Symbol'):
        return other.name == self.name

    def __str__(self):
        return '<Symbol %s flag %s>' % (
                repr(self.name), bin(self.flag))

    __repr__ = __str__


class SymbolTable:
    def __init__(self, name: str = 'top'):
        self.store_symbols: List[Symbol] = []
        self.symbols: List[Symbol] = []
        self.global_directives: Set[str] = set()
        self.nonlocal_directives: Set[str] = set()
        self.prev_table: 'SymbolTable' = None
        self.name = name
        self.freevars: Set[str] = set()
        self.cellvars: Set[str] = set()
        self.nlocals = 0
        self.local_maybe: Set[str] = set()

    def is_local(self, symbol: Symbol) -> bool:
        for s in self.store_symbols:
            if s.name == symbol.name:
                return True
        return False

    def is_global(self, symbol: Symbol) -> bool:
        if self.prev_table is None:
            # so this is the symbol table for global scope
            for s in self.store_symbols:
                if s.name == symbol.name:
                    return True
            return False
        return self.prev_table.is_global(symbol)

    def _check_free(self, symbol: Symbol):
        if self.prev_table is None:
            # the global scope cannot check free variable
            return False

        for s in self.store_symbols:
            if s.name == symbol.name:
                return True
        return False

    def is_free(self, symbol: Symbol) -> int:
        assert self.prev_table is not None
        if self.prev_table is not None:
            return self.prev_table._check_free(symbol)

    def add_store_symbol(self, symbol: Symbol):
        for sym in self.store_symbols:
            if sym.name == symbol.name:
                return
        self.store_symbols.insert(0, symbol)

    def add_symbol(self, symbol: Symbol):
        symbols = self.symbols

        for sym in symbols:
            if sym.name == symbol.name:
                return

        symbols.insert(0, symbol)

    def mangle(self, symbol: Symbol):
        name = symbol.name
        if not check_mangle(name):
            return

        cur_tab = self
        while cur_tab is not None:
            if isinstance(cur_tab, ClassSymbolTable):
                break
            cur_tab = cur_tab.prev_table
        else:
            return  # no class symbol table found

        symbol.name = do_mangle(cur_tab.name, symbol.name)

    def __str__(self):
        return '<SymbolTable of %s>' % self.name

    __repr__ = __str__


class FunctionSymbolTable(SymbolTable):
    def __init__(self, name: str):
        super().__init__(name)
        self.is_namespace = False

    def __str__(self):
        return '<Function SymbolTable of %s>' % self.name

    __repr__ = __str__


class ClassSymbolTable(SymbolTable):
    def __init__(self, name: str):
        super().__init__(name)

    def __str__(self):
        return '<Class SymbolTable of %s>' % self.name

    __repr__ = __str__


class SymbolAnalyzer:
    def __init__(self):
        self.__symbol_table: SymbolTable = None
        self.__filename = ''
        self.__source = ''
        self.__block_queue = []

    def __add_symbol(self, symbol: Symbol):
        self.__symbol_table.add_symbol(symbol)

    def __add_store_symbol(self, symbol: Symbol):
        self.__symbol_table.add_store_symbol(symbol)

    def __syntax_error(self, msg: str, ln: int):
        error_msg(ln, msg, self.__filename, source=self.__source)

    def _analyze_and_fill_symbol(
            self, symbol: Symbol, ctx: int, ignore_nonlocal: bool = False) -> Symbol:
        self.__symbol_table.mangle(symbol)
        name = symbol.name

        if ctx == CTX_STORE:
            if type(self.__symbol_table) is not SymbolTable:
                if name in self.__symbol_table.global_directives:
                    symbol.flag |= SYM_GLOBAL
                elif name in self.__symbol_table.nonlocal_directives and \
                        not ignore_nonlocal:
                    symbol.flag |= SYM_FREE
                    self.__symbol_table.freevars.add(name)
                else:
                    symbol.flag |= SYM_LOCAL
                    self.__symbol_table.local_maybe.add(symbol.name)
                return symbol
            assert isinstance(self.__symbol_table, SymbolTable)
            symbol.flag |= SYM_NORMAL
            return symbol

        assert ctx == CTX_LOAD

        sym_name = symbol.name

        for sym in self.__symbol_table.symbols:
            if sym.name == sym_name:
                if ignore_nonlocal and sym.flag & SYM_NONLOCAL:
                    pass
                else:
                    return sym

        if type(self.__symbol_table) is not SymbolTable and \
                (self.__symbol_table.is_free(symbol) or
                 name in self.__symbol_table.nonlocal_directives) and \
                not ignore_nonlocal:
            symbol.flag |= SYM_FREE
            self.__symbol_table.freevars.add(name)
        elif type(self.__symbol_table) is not SymbolTable:
            if self.__symbol_table.is_local(symbol):
                symbol.flag |= SYM_LOCAL
            else:
                symbol.flag |= SYM_GLOBAL
        else:
            symbol.flag |= SYM_NORMAL

        return symbol

    def _visit_assign_expr(
            self, expr: ast.AssignExprAST, ignore_nonlocal: bool = False):
        self._visit(expr.right)

        left = []

        if isinstance(expr.left, ast.TupleAST):
            left = expr.left.items
        else:
            left.append(expr.left)

        for target in left:
            if isinstance(target, ast.StarredExpr):
                target = target.value

            if isinstance(target, ast.CellAST):
                s = self._analyze_and_fill_symbol(
                    Symbol(target.value), CTX_STORE, ignore_nonlocal)
                self.__add_store_symbol(s)
                target.symbol = s

            elif isinstance(target, ast.MemberAccessAST) or \
                    isinstance(target, ast.SubscriptExprAST):
                name = _get_first_cell(target)
                s = self._analyze_and_fill_symbol(
                    Symbol(name.value), CTX_STORE, ignore_nonlocal)
                name.symbol = s
                self.__add_store_symbol(s)
            else:
                raise TypeError('invalid target type: %s' % type(target))

    def _visit_block(self, block: ast.BlockAST):
        stmts = block.stmts

        for stmt in stmts:
            self._visit(stmt)

    def _visit_binary_expr(self, expr):
        self._visit(expr.left)

        for _, e in expr.right:
            self._visit(e)

    def _visit_cell(self, cell: ast.CellAST):
        if cell.type != AIL_IDENTIFIER or cell.value in AIL_CONSTANTS:
            return

        s = self._analyze_and_fill_symbol(Symbol(cell.value), CTX_LOAD)
        cell.symbol = s
        self.__add_symbol(s)

    def _visit_call_expr(self, expr: ast.CallExprAST):
        self._visit(expr.left)

        for arg in expr.arg_list.arg_list:
            self._visit(arg.expr)
            if arg.default is not None:
                self._visit(arg.default)

    def _visit_queue(self):
        for symbol, node in self.__block_queue:
            if isinstance(node, ast.FunctionDefineAST):
                self._visit_func_def(node, symbol)
            elif isinstance(node, ast.ClassDefineAST):
                self._visit_class_def(node, symbol)
            elif isinstance(node, ast.NamespaceStmt):
                self._visit_namespace_def(node, symbol)

    def _visit_func_def(self, node: ast.FunctionDefineAST, symbol: Symbol):
        table = FunctionSymbolTable(node.name)
        table.prev_table = self.__symbol_table
        _visit_param_list(table, node.param_list)

        analyzer = SymbolAnalyzer()
        table = analyzer.visit_and_make_symbol_table(
            self.__source, self.__filename, node.block, table
        )
        symbol.namespace = table

    def _visit_class_def(self, node: ast.ClassDefineAST, symbol: Symbol):
        table = ClassSymbolTable(node.name)
        table.prev_table = self.__symbol_table

        analyzer = SymbolAnalyzer()
        table = analyzer.visit_and_make_symbol_table(
            self.__source, self.__filename, node.func.block, table
        )
        symbol.namespace = table

    def _visit_namespace_def(self, node: ast.NamespaceStmt, symbol: Symbol):
        table = FunctionSymbolTable(node.name)
        table.is_namespace = True

        analyzer = SymbolAnalyzer()
        table = analyzer.visit_and_make_symbol_table(
            self.__source, self.__filename, node.block, table
        )
        symbol.namespace = table

    def _visit_member_access_expr(self, expr: ast.MemberAccessAST):
        left = _get_first_cell(expr)
        self._visit(left)

    def _visit_subscript_expr(self, expr: ast.SubscriptExprAST):
        left = _get_first_cell(expr)
        self._visit(left)
        self._visit(expr.expr)

    def _visit_if_stmt(self, stmt: ast.IfStmtAST):
        self._visit(stmt.test)
        self._visit(stmt.block)
        self._visit(stmt.else_block)

        for block in stmt.elif_list:
            self._visit(block)

    def _visit_while_stmt(self, stmt: ast.WhileStmtAST):
        self._visit(stmt.test)
        self._visit(stmt.block)

    def _visit_for_stmt(self, stmt: ast.ForStmtAST):
        self._visit(stmt.test)

        for expr in stmt.init_list.expr_list:
            self._visit(expr)

        for expr in stmt.update_list.expr_list:
            self._visit(expr)

        self._visit(stmt.block)

    def _visit_foreach_stmt(self, stmt: ast.ForeachStmt):
        fake_assign = ast.AssignExprAST(stmt.target, stmt.iter, 0, False)
        self._visit(fake_assign)
        self._visit(stmt.body)

    def _visit_with_stmt(self, stmt: ast.WithStmt):
        self._visit(stmt.body)
        for item in stmt.items:
            if item.optional_var:
                fake_assign = ast.AssignExprAST(item.optional_var, item.context_expr, 0)
                self._visit_assign_expr(fake_assign, ignore_nonlocal=True)
            else:
                self._visit(item.context_expr)

    def _visit_if_expr(self, expr: ast.IfExpr):
        self._visit(expr.test)
        self._visit(expr.body)
        self._visit(expr.orelse)

    def _visit_py_import_stmt(self, stmt: ast.PyImportStmt):
        for item in stmt.names:
            if item.alias is None:
                name = item.name
            else:
                name = item.alias
            s = self._analyze_and_fill_symbol(Symbol(name), CTX_STORE, True)
            self.__add_store_symbol(s)

    def _visit_py_import_from_stmt(self, stmt: ast.PyImportFromStmt):
        for item in stmt.names:
            if item.alias is None:
                name = item.name
            else:
                name = item.alias
            s = self._analyze_and_fill_symbol(Symbol(name), CTX_STORE, True)
            self.__add_store_symboll(s)

    def _visit_import_stmt(self, stmt: ast.ImportStmtAST):
        if not stmt.members:
            s = self._analyze_and_fill_symbol(Symbol(stmt.name), CTX_STORE, True)
            self.__add_store_symbol(s)
            return

        for m in stmt.members:
            s = self._analyze_and_fill_symbol(Symbol(m), CTX_STORE, True)
            self.__add_store_symbol(s)
            return

    def _visit_try_stmt(self, stmt: ast.TryCatchStmtAST):
        self._visit(stmt.try_block)
        self._visit(stmt.finally_block)

        for case in stmt.catch_cases:
            self._visit(case.block)
            self._visit(case.exc_expr)
            self.__add_store_symbol(
                self._analyze_and_fill_symbol(Symbol(case.alias), CTX_STORE, True)
            )

    def _visit_match_expr(self, expr: ast.MatchExpr):
        self._visit(expr.target)

        for case in expr.cases:
            if case.when_test is not None:
                self._visit(case.when_test)
            else:
                for pattern in case.patterns:
                    self._visit(pattern)
            self._visit(case.expr)

    def _visit_obj_pattern_expr(self, expr: ast.ObjectPatternExpr):
        self._visit(expr.left)
        for val in expr.values:
            self._visit(val)

    def _visit(self, node: ast.AST):
        if node is None:
            return

        if isinstance(node, ast.BlockAST):
            self._visit_block(node)

        elif isinstance(node, ast.AssignExprAST):
            self._visit_assign_expr(node)

        elif isinstance(node, ast.CellAST):
            self._visit_cell(node)

        elif isinstance(node, ast.CallExprAST):
            self._visit_call_expr(node)

        elif isinstance(node, ast.SubscriptExprAST):
            self._visit_subscript_expr(node)

        elif isinstance(node, ast.MemberAccessAST):
            self._visit_member_access_expr(node)

        elif isinstance(node, ast.UnaryExprAST):
            self._visit(node.expr)

        elif isinstance(node, ast.TestExprAST):
            self._visit(node.test)

        elif isinstance(node, ast.ReturnStmtAST):
            self._visit(node.expr)

        elif isinstance(node, ast.ArrayAST):
            for elt in node.items.item_list:
                self._visit(elt)

        elif isinstance(node, ast.DictAST):
            for elt in node.keys:
                self._visit(elt)
            for elt in node.values:
                self._visit(elt)

        elif isinstance(node, ast.TupleAST):
            for elt in node.items:
                self._visit(elt)

        elif isinstance(node, ast.IfStmtAST):
            self._visit_if_stmt(node)

        elif isinstance(node, ast.WhileStmtAST):
            self._visit_while_stmt(node)

        elif isinstance(node, ast.ForStmtAST):
            self._visit_for_stmt(node)

        elif isinstance(node, ast.ForeachStmt):
            self._visit_foreach_stmt(node)

        elif isinstance(node, ast.SliceExpr):
            self._visit(node.start)
            self._visit(node.step)
            self._visit(node.stop)

        elif isinstance(node, ast.StarredExpr):
            self._visit(node.value)

        elif isinstance(node, ast.WithStmt):
            self._visit_with_stmt(node)

        elif isinstance(node, ast.IfExpr):
            self._visit_if_expr(node)

        elif isinstance(node, ast.YieldExpr):
            self._visit(node.value)

        elif isinstance(node, ast.YieldFromExpr):
            self._visit(node.value)

        elif isinstance(node, ast.PyImportStmt):
            self._visit_py_import_stmt(node)

        elif isinstance(node, ast.PyImportFromStmt):
            self._visit_py_import_from_stmt(node)

        elif isinstance(node, ast.ImportStmtAST):
            self._visit_import_stmt(node)

        elif isinstance(node, ast.PrintStmtAST):
            for val in node.value_list:
                self._visit(val)

        elif isinstance(node, ast.InputStmtAST):
            self._visit(node.msg)
            for val in node.value_list.value_list:
                val: ast.CellAST
                s = self._analyze_and_fill_symbol(Symbol(val.value), CTX_LOAD, True)
                self.__add_symbol(s)

        elif isinstance(node, ast.DoLoopStmtAST):
            self._visit(node.test)
            self._visit(node.block)

        elif isinstance(node, ast.GlobalStmtAST):
            if node.name in self.__symbol_table.nonlocal_directives:
                self.__syntax_error(
                    'name \'%s\' is nonlocal and global' % node.name, node.ln)
            self.__symbol_table.global_directives.add(node.name)

        elif isinstance(node, ast.NonlocalStmtAST):
            if node.name in self.__symbol_table.global_directives:
                self.__syntax_error(
                    'name \'%s\' is nonlocal and global' % node.name, node.ln)
            self.__symbol_table.nonlocal_directives.add(node.name)

        elif isinstance(node, ast.StructDefineAST):
            s = self._analyze_and_fill_symbol(Symbol(node.name), CTX_STORE, True)
            self.__add_store_symbol(s)

        elif isinstance(node, ast.AssignExprListAST):
            for expr in node.expr_list:
                self._visit(expr)

        elif isinstance(node, ast.BinaryExprListAST):
            for expr in node.expr_list:
                self._visit(expr)

        elif isinstance(node, ast.ThrowStmtAST):
            self._visit(node.expr)

        elif isinstance(node, ast.AssertStmtAST):
            self._visit(node.expr)
            self._visit(node.msg)

        elif isinstance(node, ast.TryCatchStmtAST):
            self._visit_try_stmt(node)

        elif isinstance(node, ast.MatchExpr):
            self._visit_match_expr(node)

        elif isinstance(node, ast.ObjectPatternExpr):
            self._visit_obj_pattern_expr(node)

        elif isinstance(node, ast.TestExprAST):
            self._visit(node.test)

        elif isinstance(node, ast.NamespaceStmt):
            s = self._analyze_and_fill_symbol(Symbol(node.name), CTX_STORE)
            self.__add_store_symbol(s)
            self.__block_queue.append((s, node))
            node.symbol = s

        elif isinstance(node, ast.FunctionDefineAST):
            if node.is_lambda:
                node.block = ast.BlockAST(
                    [ast.ReturnStmtAST(node.lambda_return, node.lambda_return.ln)],
                    node.ln)

            if node.bindto is not None:
                bandto_symbol = self._analyze_and_fill_symbol(
                        Symbol(node.bindto), CTX_LOAD)
                self.__add_symbol(bandto_symbol)

            s = self._analyze_and_fill_symbol(Symbol(node.name), CTX_STORE)
            if node.scope_effect:
                self.__add_store_symbol(s)
            self.__block_queue.append((s, node))
            node.symbol = s

        elif isinstance(node, ast.ClassDefineAST):
            if node.meta is not None:
                self._visit(node.meta)
            if node.bases:
                for base in node.bases:
                    self._visit(base)
            s = self._analyze_and_fill_symbol(Symbol(node.name), CTX_STORE)
            self.__add_store_symbol(s)
            self.__block_queue.append((s, node))
            node.symbol = s

        elif type(node) in (ast.AndTestAST, ast.OrTestAST):
            self._visit(node.left)
            for e in node.right:
                self._visit(e)

        elif type(node) in ast.UNARY_EXPR_ASTS:
            self._visit(node.expr)

        elif type(node) in ast.EXPR_AST_TYPES:
            self._visit_binary_expr(node)

    def _check_freevars(self):
        if type(self.__symbol_table) is SymbolTable:
            return

        self.__symbol_table: FunctionSymbolTable

        freevars = self.__symbol_table.freevars
        cellvars = self.__symbol_table.cellvars
        local_maybe = self.__symbol_table.local_maybe

        for symbol in self.__symbol_table.store_symbols:
            if symbol.namespace is not None:
                assert type(symbol.namespace) is not SymbolTable
                for var in symbol.namespace.freevars:
                    if var in [
                            sym.name for sym in self.__symbol_table.store_symbols]:
                        cellvars.add(var)
                    else:
                        freevars.add(var)

                    if var in local_maybe:
                        local_maybe.remove(var)

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
        self._visit_queue()
        self._check_freevars()

        self.__symbol_table.nlocals = len(self.__symbol_table.local_maybe)

        return self.__symbol_table


def symtable(source, filename) -> SymbolTable:
    from ail.core import aparser, alex

    ts = alex.Lex().lex(source)
    tree = aparser.Parser().parse(ts, source, filename)
    analyzer = SymbolAnalyzer()
    return analyzer.visit_and_make_symbol_table(
            source, filename, tree)
