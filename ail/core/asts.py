# AST
from typing import List, Tuple


class ExprAST:
    """
    这是所有 表达式AST 的父类
    """
    pass


class ArgItemAST:
    def __init__(self, expr: 'ExprAST', star: bool, ln: int):
        self.expr = expr
        self.star = star
        self.kw_star = False
        self.default = None
        self.ln = ln


class ArgListAST:
    """
    arg_list := expr [',' expr]*
    """

    def __init__(self, item_list: List[ArgItemAST], ln: int):
        self.arg_list = item_list  # TODO: refactor exp_list -> item_list
        self.ln = ln


class CellAST:
    """
    cell := NUMBER | NAME | STRING | call_expr
    """

    def __init__(self, value: object, _type: int, ln: int):
        self.value = value
        self.type = _type
        self.ln = ln

    def __str__(self):
        return '<Cell value = \'%s\'>' % self.value

    __repr__ = __str__


class MemberAccessAST:
    def __init__(self, left: CellAST, members: CellAST, ln: int):
        self.left = left
        self.members = members
        self.ln = ln


class UnaryExprAST:
    """
    unary_expr := [unary_op] member_expr
    """

    def __init__(self, op: str, right_expr: MemberAccessAST, ln: int):
        self.op = op
        self.right_expr = right_expr
        self.ln = ln


class PowerExprAST:
    """
    pow_expr := unary_expr ['^' unary_expr]
    """

    def __init__(self, left: UnaryExprAST, right: List[UnaryExprAST], ln: int):
        self.left = left
        self.right = right
        self.ln = ln


class ModExprAST:
    """
    mod_expr := pow_expr ['mod' pow_expr]
    """

    def __init__(self, left: PowerExprAST, right: List[PowerExprAST], ln: int):
        self.left = left
        self.right = right
        self.ln = ln


class MuitDivExprAST:
    """
    md_expr := mod_expr [('*' | '/') mod_expr]
    """

    def __init__(self, op: str, left: ModExprAST, right: List[ModExprAST], ln: int):
        self.op = op
        self.left = left
        self.right = right
        self.ln = ln


class AddSubExprAST:
    """
    real_expr := md_expr [('+' | '-') md_expr]* | '(' real_expr ')'
    """

    def __init__(self, op: str,
                 left: MuitDivExprAST,
                 right: List[Tuple[str, MuitDivExprAST]], ln: int):
        self.op = op
        self.left = left
        self.right = right
        self.ln = ln


class GenericBinaryExprAST:
    def __init__(self, left, right: list, ln: int):
        self.left = left
        self.right = right
        self.ln = ln


class BitShiftExprAST:
    def __init__(self, op: str,
                 left: AddSubExprAST,
                 right: List[Tuple[str, AddSubExprAST]], ln: int):
        self.op = op
        self.left = left
        self.right = right
        self.ln = ln


class BinXorExprAST:
    def __init__(self,
                 left: BitShiftExprAST,
                 right: List[Tuple[str, BitShiftExprAST]], ln: int):
        self.left = left
        self.right = right
        self.ln = ln


class BitOpExprAST:
    def __init__(self, op: str,
                 left: BinXorExprAST,
                 right: List[Tuple[str, BinXorExprAST]], ln: int):
        self.op = op
        self.left = left
        self.right = right
        self.ln = ln


class CallExprAST:
    """
    call_expr := NAME '(' arg_list ')'
    """

    def __init__(self, left: AddSubExprAST, arg_list: ArgListAST, ln: int):
        self.left = left
        self.arg_list = arg_list
        self.ln = ln


class ValueListAST:
    """
    val_list := NAME [',' NAME]
    """

    def __init__(self, v_list: list, ln: int):
        self.value_list = v_list
        self.ln = ln

    def __str__(self):
        return '<ValueList %s>' % str(self.value_list)


class AssignExprAST(ExprAST):
    """
    assi_expr := cell ['=' expr]* NEWLINE
    """

    def __init__(self, left: BitOpExprAST, right: BitOpExprAST, ln: int,
                 aug_assign: bool = False):
        self.right = right
        self.left = left
        self.aug_assign = aug_assign
        self.ln = ln


class DefineExprAST(ExprAST):
    """
    def_expr := NAME '=' expr NEWLINE
    """

    def __init__(self, name: str, value: ExprAST, ln: int):
        self.value = value
        self.name = name
        self.ln = ln


class PrintStmtAST(ExprAST):
    """
    print_expr := 'PRINT' expr [';' expr]* NEWLINE
    """

    def __init__(self, value_list: list, ln: int):
        self.value_list = value_list
        self.ln = ln


class InputStmtAST(ExprAST):
    """
    input_expr := 'INPUT' expr ';' val_list NEWLINE
    """

    def __init__(self, msg: ExprAST, val_list: ValueListAST, ln: int):
        self.msg = msg
        self.value_list = val_list
        self.ln = ln


class CmpTestAST:
    """
    cmp_test := expr [cmp_op expr]*
    """

    def __init__(self, left: ExprAST, right: list, ln: int):
        self.left = left
        self.right = right
        self.ln = ln


class AndTestAST:
    """
    and_test := cmp_test ['and' cmp_test]
    """

    def __init__(self, left: CmpTestAST, right: list, ln: int):
        self.left = left
        self.right = right
        self.ln = ln


class OrTestAST:
    """
    or_test := and_test ['or' and_test]*
    """

    def __init__(self, left: AndTestAST, right: list, ln: int):
        self.left = left
        self.right = right
        self.ln = ln


class TestExprAST:
    """
    test := or_test
    """

    def __init__(self, test: OrTestAST, ln: int):
        self.test = test
        self.ln = ln


class BlockAST:
    """
    BLOCK := stmt*
    """

    def __init__(self, stmts: list, ln: int, new: bool = False):
        self.stmts = stmts
        self.ln = ln
        self.new = new


class IfStmtAST:
    """
    if_else_expr := 'if' test 'then' NEWLINE
                BLOK
                (
                 'else' NEWLINE
                 BLOCK
                )
                'endif'
    """

    def __init__(self, test: TestExprAST,
                 block: BlockAST, elif_list: list, else_block: BlockAST, ln: int):
        self.test = test
        self.block = block
        self.elif_list = elif_list
        self.else_block = else_block
        self.ln = ln


class WhileStmtAST:
    """
    while_expr := 'while' test 'then'
        BLOCK
        'wend' NEWLINE'
    """

    def __init__(self, test: TestExprAST, block: BlockAST, ln: int):
        self.test = test
        self.block = block
        self.ln = ln


class DoLoopStmtAST:
    """
    do_loop_expr := 'do' 'NEWLINE
                BLOCK
                'loop' 'until' test NEWLINE
    """

    def __init__(self, test: TestExprAST, block: BlockAST, ln: int):
        self.test = test
        self.block = block
        self.ln = ln


class FunctionDefineAST:
    """
    func_def := 'fun' ['(' NAME ')'] NAME '(' arg_list ')' NEWLINE
                BLOCK
            'end'
    """

    def __init__(self, name: str, arg_list: ArgListAST,
                 block: BlockAST, bindto: str, ln: int,
                 doc_str=''):
        self.name = name
        self.arg_list = arg_list
        self.block = block
        self.bindto = bindto
        self.decorator = list()
        self.ln = ln
        self.doc_str=  doc_str
        self.is_lambda = False
        self.lambda_return = None


class ClassDefineAST:
    def __init__(self, 
                 name: str, func: FunctionDefineAST,
                 bases: List[ExprAST], meta: ExprAST, ln: int,
                 doc_str=''):
        self.name = name
        self.func = func
        self.bases = bases
        self.meta = meta
        self.doc_str = doc_str
        self.ln = ln


class ReturnStmtAST:
    """
    return_stmt := 'return' expr
    """

    def __init__(self, expr: ExprAST, ln: int):
        self.expr = expr
        self.ln = ln


class GlobalStmtAST:
    def __init__(self, name: str, ln: int):
        self.name = name
        self.ln = ln


class NonlocalStmtAST:
    def __init__(self, name: str, ln: int):
        self.name = name
        self.ln = ln


class ContinueStmtAST:
    """
    continue_stmt := 'continue'
    """

    def __init__(self, ln: int):
        self.ln = ln


class BreakStmtAST:
    """
    break_stmt := 'break'
    """

    def __init__(self, ln: int):
        self.ln = ln


class NullLineAST:
    """
    null_line := NEWLINE
    """

    def __init__(self, ln: int):
        self.ln = ln


class EOFAST:
    def __init__(self, ln: int):
        self.ln = ln


class ItemListAST:
    def __init__(self, item_list: list, ln: int):
        self.item_list = item_list
        self.ln = ln


class ArrayAST:
    def __init__(self, items: ItemListAST, ln: int):
        self.items = items
        self.ln = ln


class TupleAST:
    def __init__(self, items: list, store: bool, ln: int):
        self.items = items
        self.ln = ln
        self.store = store


class MapAST:
    def __init__(self, keys: list, values: list, ln :int):
        self.keys = keys
        self.values = values
        self.ln = ln


class SubscriptExprAST:
    def __init__(self, left: AddSubExprAST, expr: AddSubExprAST, ln: int):
        self.expr = expr
        self.left = left
        self.ln = ln


class LoadStmtAST:
    def __init__(self, path: str, ln: int):
        self.path = path
        self.ln = ln


class ImportStmtAST:
    def __init__(self, path: str, name: str, ln: int, members: List[str] = None):
        self.path = path
        self.name = name
        self.ln = ln
        self.members = members if members is not None else list()


class StructDefineAST:
    def __init__(self, name: str, name_list: list, protected_list: list, ln: int):
        self.name = name
        self.name_list = name_list
        self.protected_list = protected_list
        self.ln = ln


class NotTestAST:
    def __init__(self, expr: CmpTestAST, ln):
        self.expr = expr
        self.ln = ln


class AssignExprListAST:
    def __init__(self, expr_list: list, ln):
        self.expr_list = expr_list
        self.ln = ln


class BinaryExprListAST:
    def __init__(self, expr_list: list, ln):
        self.expr_list = expr_list
        self.ln = ln


class ForStmtAST:
    def __init__(self, init_list: AssignExprListAST,
                 test: TestExprAST, update_list: BinaryExprListAST,
                 block: BlockAST, ln):
        self.init_list = init_list
        self.test = test
        self.update_list = update_list
        self.block = block
        self.ln = ln


class ThrowStmtAST:
    def __init__(self, expr: AddSubExprAST, ln: int):
        self.expr = expr
        self.ln = ln


class AssertStmtAST:
    def __init__(self, expr: TestExprAST, ln: int):
        self.expr = expr
        self.ln = ln


class TryCatchStmtAST:
    def __init__(self, try_block: BlockAST,
                 catch_block: BlockAST,
                 finally_block: BlockAST,
                 name: str, ln: int):
        self.try_block = try_block
        self.catch_block = catch_block
        self.finally_block = finally_block
        self.name = name
        self.ln = ln


class PyCodeBlock:
    def __init__(self, code: str, ln: int):
        self.code = code
        self.ln = ln


class StaticAssign:
    def __init__(self, assign: AssignExprAST, ln: int):
        self.assign = assign
        self.ln = ln


class AssignModifier:
    def __init__(self, assign: AssignExprAST, static: bool, context: str, ln: int):
        self.assign = assign
        self.context = context
        self.static = static
        self.ln = ln


class PropertyDefine:
    def __init__(self, func: FunctionDefineAST, action: str, ln: int):
        self.func = func
        self.action = action
        self.ln = ln


class InstanceProperty:
    def __init__(self, assign: AssignExprAST, ln: int):
        self.assign = assign
        self.ln = ln


BINARY_AST_TYPES = (
    CellAST,
    PowerExprAST,
    ModExprAST,
    MuitDivExprAST,
    AddSubExprAST,
    DefineExprAST,
    CallExprAST,
    ArrayAST,
    MapAST,
    SubscriptExprAST,
    MemberAccessAST,
    AssignExprAST,
    UnaryExprAST,
    BinXorExprAST,
    BitShiftExprAST,
    BitOpExprAST,
    TestExprAST,
)

BIN_OP_AST = (
    PowerExprAST,
    ModExprAST,
    MuitDivExprAST,
    AddSubExprAST,
    BitShiftExprAST,
    BitOpExprAST,
    BinXorExprAST,
    GenericBinaryExprAST,
    CmpTestAST,
)

