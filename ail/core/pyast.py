import _ast

from typing import List, TypeVar


aug_load_ctx = _ast.AugLoad
aug_store_ctx = _ast.AugStore
del_ctx = _ast.Del
load_ctx = _ast.Load
param_ctx = _ast.Param
store_ctx = _ast.Store

add_op = _ast.Add
bit_and_op = _ast.BitAnd
bit_or_op = _ast.BitOr
bit_xor_op = _ast.BitXor
div_op = _ast.Div
floor_div_op = _ast.FloorDiv
lshift_op = _ast.LShift
mod_op = _ast.Mod
mult_op = _ast.Mult
pow_op = _ast.Pow
rshift_op = _ast.RShift
sub_op = _ast.Sub

invert_uop = _ast.Invert
not_uop = _ast.Not
uadd_uop = _ast.UAdd
usub_uop = _ast.USub

break_stmt = _ast.Break
continue_stmt = _ast.Continue

eq_cmp = _ast.Eq
gt_cmp = _ast.Gt
gte_cmp = _ast.GtE
in_cmp = _ast.In
is_cmp = _ast.Is
is_not_cmp = _ast.IsNot
lt_cmp = _ast.Lt
lte_cmp = _ast.LtE
not_eq_cmp = _ast.NotEq
not_in_cmp = _ast.NotIn


def import_alias(name: str, asname: str) -> _ast.alias:
    return _ast.alias(name=name, asname=asname)


def arguments(args: List[_ast.arg],
              vararg: _ast.arg, kwarg: _ast.arg,
              defaults: List[_ast.expr] = None) -> _ast.arguments:
    if defaults is None:
        defaults = []

    return _ast.arguments(
        args=args, 
        posonlyargs=[], 
        vararg=vararg, 
        kwonlyargs=[],
        kw_defaults=[],
        kwarg=kwarg,
        defaults=defaults,
    )


def argument(arg: str) -> _ast.arg:
    return _ast.arg(arg=arg, annotation=None, type_comment=None)


def assert_stmt(test: _ast.expr, msg: _ast.expr) -> _ast.Assert:
    return _ast.Assert(test=test, msg=msg)


def assign_stmt(targets: List[_ast.AST], value: _ast.expr) -> _ast.Assign:
    return _ast.Assign(targets=targets, value=value, type_comment=None)


def attribute_expr(value: _ast.expr, attr: str, ctx: _ast.expr_context) -> _ast.Attribute:
    return _ast.Attribute(value=value, attr=attr, ctx=ctx)


def aug_assign_stmt(
        target: _ast.expr, op: _ast.operator, value: _ast.expr) -> _ast.AugAssign:
    return _ast.AugAssign(target=target, op=op, value=value)


def bin_op_expr(left: _ast.expr, op: _ast.operator, right: _ast.expr) -> _ast.BinOp:
    return _ast.BinOp(left=left, op=op, right=right)


def bool_op_expr(op: _ast.boolop, values: List[_ast.expr]) -> _ast.BoolOp:
    return _ast.BoolOp(op=op, values=values)


def call_expr(func: _ast.expr, args: List[_ast.expr], 
              keywords: List[_ast.expr] = None) -> _ast.Call:
    if keywords is None:
        keywords = list()
    return _ast.Call(func=func, args=args, keywords=keywords)


def class_def_stmt(
        name: str, bases: List[_ast.expr], keywords: List[_ast.keyword],
        body: List[_ast.stmt], decorator_list: List[_ast.expr]) -> _ast.ClassDef:
    return _ast.ClassDef(
        name=name, bases=bases, keywords=keywords, body=body, decorator_list=decorator_list)


def compare_expr(
        left: _ast.expr, ops: List[_ast.cmpop],
        comparators: List[_ast.expr]) -> _ast.Compare:
    return _ast.Compare(left=left, ops=ops, comparators=comparators)


def constant_expr(value: object) -> _ast.Constant:
    return _ast.Constant(value=value, kind=None, n=value)


def dict_expr(keys: List[_ast.expr], values: List[_ast.expr]) -> _ast.Dict:
    return _ast.Dict(keys=keys, values=values)


def except_handler(
        type: _ast.expr, name: str, body: List[_ast.stmt]) -> _ast.ExceptHandler:
    return _ast.ExceptHandler(type=type, name=name, body=body)


def expr_stmt(value: _ast.expr) -> _ast.Expr:
    return _ast.Expr(value=value)


def function_def_stmt(
        name: str, args: _ast.arguments, body: List[_ast.stmt],
        decorator_list: List[_ast.expr]) -> _ast.FunctionDef:
    return _ast.FunctionDef(
        name=name, args=args, body=body, decorator_list=decorator_list,
        returns=None, type_comment=None)


def global_stmt(names: List[str]) -> _ast.Global:
    return _ast.Global(names=names)


def keyword_expr(arg: str, value: _ast.expr) -> _ast.keyword:
    return _ast.keyword(arg=arg, value=value)


def if_stmt(
        test: _ast.expr, body: List[_ast.stmt], 
        orelse: List[_ast.If]) -> _ast.If:
    return _ast.If(test=test, body=body, orelse=orelse)


def import_from_stmt(
        module: str, names: List[_ast.alias], level: int) -> _ast.ImportFrom:
    return _ast.ImportFrom(module=module, names=names, level=level)


def index_slice(value: _ast.expr) -> _ast.Index:
    return _ast.Index(value=value)


def interactive(body: List[_ast.stmt]) -> _ast.Interactive:
    return _ast.Interactive(body=body)


def lambda_expr(args: List[_ast.expr], body: _ast.stmt) -> _ast.Lambda:
    return _ast.Lambda(args=args, body=body)


def list_expr(elts: List[_ast.expr], ctx: _ast.expr_context) -> _ast.List:
    return _ast.List(elts=elts, ctx=ctx)


def module(body: List[_ast.stmt]) -> _ast.Module:
    return _ast.Module(body=body, type_ignores=[])


def name_expr(id: str, ctx: _ast.expr_context) -> _ast.Name:
    return _ast.Name(id=id, ctx=ctx)


def nonlocal_stmt(names: List[str]) -> _ast.Nonlocal:
    return _ast.Nonlocal(names=names)


def pass_stmt() -> _ast.Pass:
    return _ast.Pass()


def raise_stmt(exc: _ast.expr) -> _ast.Raise:
    return _ast.Raise(exc=exc, cause=None)


def return_stmt(value: _ast.expr) -> _ast.Return:
    return _ast.Return(value=value)


def starred_expr(value: _ast.expr, ctx: _ast.expr_context) -> _ast.Starred:
    return _ast.Starred(value=value, ctx=ctx)


def subscript_expr(
        value: _ast.expr, slice: _ast.slice, ctx: _ast.expr_context) -> _ast.Subscript:
    return _ast.Subscript(value=value, slice=slice, ctx=ctx)


def try_stmt(
        body: List[_ast.stmt], handlers: List[_ast.ExceptHandler],
        finalbody: List[_ast.stmt]) -> _ast.Try:
    return _ast.Try(body=body, handlers=handlers, 
                    orelse=[], finalbody=finalbody)


def tuple_expr(elts: List[_ast.expr], ctx: _ast.expr_context) -> _ast.Tuple:
    return _ast.Tuple(elts=elts, ctx=ctx)


def unary_op_expr(op: _ast.operator, operand: _ast.expr) -> _ast.UnaryOp:
    return _ast.UnaryOp(op=op, operand=operand)


def while_stmt(test: _ast.expr, body: List[_ast.stmt]) -> _ast.While:
    return _ast.While(test=test, body=body, orelse=[])

