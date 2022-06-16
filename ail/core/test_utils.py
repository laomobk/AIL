
from . import asts as ast


def print_pyast(tree):
    try:
        import astunparse
        dump_func = astunparse.dump
    except ModuleNotFoundError:
        import ast
        dump_func = ast.dump

    print(dump_func(tree))


def unparse_pyast(tree):
    try:
        import astunparse
        print(astunparse.unparse(tree))
    except ModuleNotFoundError:
        print('unparse_pyast: module \'astunparse\' not found.')
    

def unpack_list(l: list):
    rl = []
    for d in l:
        if isinstance(d, tuple):
            rl.append(unpack_list(d))
        else:
            rl.append(make_ast_tree(d))
    return rl


def make_ast_tree(a) -> dict:
    if isinstance(a, ast.CellAST):
        return {'Cell': {'value': a.value, 'type': a.type}}

    elif isinstance(a, ast.UnaryExprAST):
        return {'UnaryAST': {'op': a.op, 'right': make_ast_tree(a.right_expr)}}

    elif isinstance(a, ast.PowerExprAST):
        return {'PowerAST': {'left': make_ast_tree(a.left), 'right': make_ast_tree(a.right)}}

    elif isinstance(a, ast.ModExprAST):
        return {'ModAST': {'left': make_ast_tree(a.left), 'right': make_ast_tree(a.right)}}

    elif isinstance(a, ast.MultDivExprAST):
        return {'MDAST': {'left': make_ast_tree(a.left), 'right': make_ast_tree(a.right)}}

    elif isinstance(a, ast.AddSubExprAST):
        return {'BinAST': {'left': make_ast_tree(a.left), 'right': make_ast_tree(a.right)}}

    elif isinstance(a, ast.BitOpExprAST):
        return {'BitOpAST': {'left': make_ast_tree(a.left), 'right': make_ast_tree(a.right)}}

    elif isinstance(a, ast.BinXorExprAST):
        return {'XorAST': {'left': make_ast_tree(a.left), 'right': make_ast_tree(a.right)}}

    elif isinstance(a, ast.BitShiftExprAST):
        return {'BitShiftAST': {'left': make_ast_tree(a.left), 'right': make_ast_tree(a.right)}}

    elif isinstance(a, ast.CallExprAST):
        return {'CallAST': {
                    'left': make_ast_tree(a.left),
                    'arg_list': make_ast_tree(a.arg_list)}}

    elif isinstance(a, ast.PrintStmtAST):
        return {'PrintAST': {'value': unpack_list(a.value_list)}}

    elif isinstance(a, ast.InputStmtAST):
        return {'InputAST': {
            'msg': make_ast_tree(a.msg), 'list': make_ast_tree(a.value_list)}}
    
    elif isinstance(a, ast.ArgItemAST):
        return {'ArgItem': {'expr': make_ast_tree(a.expr), 
                            'star': a.star,
                            'type_comment': make_ast_tree(a.type_comment)}}

    elif isinstance(a, ast.ArgListAST):
        return {'ArgList': unpack_list(a.arg_list)}

    elif isinstance(a, ast.ValueListAST):
        return {'ValueList': unpack_list(a.value_list)}

    elif isinstance(a, ast.DefineExprAST):
        return {'DefAST': {'name': a.name, 'value': make_ast_tree(a.value)}}

    elif isinstance(a, ast.CmpTestAST):
        return {'CmpAST': {'left': make_ast_tree(a.left), 'right': unpack_list(a.right)}}

    elif isinstance(a, ast.AndTestAST):
        return {'AndAST': {'left': make_ast_tree(a.left), 'right': make_ast_tree(a.right)}}

    elif isinstance(a, ast.OrTestAST):
        return {'OrAST': {'left': make_ast_tree(a.left), 'right': make_ast_tree(a.right)}}

    elif isinstance(a, ast.TestExprAST):
        return {'TestAST': make_ast_tree(a.test)}

    elif isinstance(a, ast.BlockAST):
        return {'BlockAST': unpack_list(a.stmts)}

    elif isinstance(a, ast.IfStmtAST):
        return {'IfAST':
                    {'test': make_ast_tree(a.test),
                     'body': make_ast_tree(a.block),
                     'elif_block': make_ast_tree(a.elif_list),
                     'else_block': make_ast_tree(a.else_block)}}

    elif isinstance(a, ast.WhileStmtAST):
        return {'WhileAST':
                    {'test': make_ast_tree(a.test),
                     'body': make_ast_tree(a.block)}}

    elif isinstance(a, ast.DoLoopStmtAST):
        return {'DoLoopAST':
                    {'test': make_ast_tree(a.test),
                     'body': make_ast_tree(a.block)}}

    elif isinstance(a, ast.MatchExpr):
        return {
            'MatchExprAST':
                {
                    'target': make_ast_tree(a.target),
                    'cases': make_ast_tree(a.cases),
                }
        }

    elif isinstance(a, ast.MatchCase):
        return {
            'MatchCase': {
                'patterns': make_ast_tree(a.patterns),
                'expr': make_ast_tree(a.expr),
            }
        }

    elif isinstance(a, ast.FunctionDefineAST):
        return {
            'FunctionDefAST':
                {
                    'name': a.name,
                    'arg_list': make_ast_tree(a.param_list),
                    'block': make_ast_tree(a.block),
                    'bindto': make_ast_tree(a.bindto),
                    'decorator': make_ast_tree(a.decorator),
                    'type_comment': make_ast_tree(a.type_comment)}}

    elif isinstance(a, ast.ClassDefineAST):
        return {'ClassDefAST': 
                {
                    'name': a.name,
                    'bases': make_ast_tree(a.bases),
                    'func': make_ast_tree(a.func),
                }}

    elif isinstance(a, ast.ReturnStmtAST):
        return {'ReturnAST': {'expr': make_ast_tree(a.expr)}}

    elif isinstance(a, ast.BreakStmtAST):
        return 'BreakAST'

    elif isinstance(a, ast.ContinueStmtAST):
        return 'ContinueAST'

    elif isinstance(a, ast.GlobalStmtAST):
        return {'GlobalAST': {'name': a.name}}

    elif isinstance(a, ast.NonlocalStmtAST):
        return {'NonlocalAST': {'name': a.name}}

    elif isinstance(a, ast.ArrayAST):
        return {'ArrayAST': {'items': make_ast_tree(a.items)}}

    elif isinstance(a, ast.DictAST):
        return {'MapAST': {'keys': make_ast_tree(a.keys), 
                           'values': make_ast_tree(a.values)}}

    elif isinstance(a, ast.ItemListAST):
        return unpack_list(a.item_list)

    elif isinstance(a, ast.SubscriptExprAST):
        return {'SubscriptExprAST':
                    {'expr': make_ast_tree(a.expr),
                     'left': make_ast_tree(a.left)}}

    elif isinstance(a, ast.LoadStmtAST):
        return {'LoadAST': {'name': a.path}}

    elif isinstance(a, ast.ImportStmtAST):
        return {'ImportAST': {
            'path': a.path, 'name': a.name, 'members': a.members}}

    elif isinstance(a, ast.MemberAccessAST):
        return {'MemberAccessAST': {
            'left': make_ast_tree(a.left),
            'members': make_ast_tree(a.members)}}

    elif isinstance(a, ast.AssignExprAST):
        return {'AssignExprAST': {
            'left': make_ast_tree(a.left),
            'right': make_ast_tree(a.right),
            'type_comment': make_ast_tree(a.type_comment)}}

    elif isinstance(a, ast.StructDefineAST):
        return {'StructDefineAST': {
            'name': make_ast_tree(a.name),
            'name_list': make_ast_tree(a.name_list),
            'protected': make_ast_tree(a.protected_list)}}

    elif isinstance(a, ast.NotTestAST):
        return {'NotTestAST': {'expr': make_ast_tree(a.expr)}}

    elif isinstance(a, ast.ForStmtAST):
        return {'ForExprAST': {
            'init': make_ast_tree(a.init_list),
            'test': make_ast_tree(a.test),
            'update': make_ast_tree(a.update_list),
            'block': make_ast_tree(a.block)}}

    elif isinstance(a, ast.BinaryExprListAST):
        return {'BinExprListAST': make_ast_tree(a.expr_list)}

    elif isinstance(a, ast.AssignExprListAST):
        return {'AssignListAST': make_ast_tree(a.expr_list)}

    elif isinstance(a, ast.AssertStmtAST):
        return {'AssertExprAST': make_ast_tree(a.expr)}

    elif isinstance(a, ast.ThrowStmtAST):
        return {'ThrowExprAST': make_ast_tree(a.expr)}

    elif isinstance(a, ast.TryCatchStmtAST):
        return {'TryCatchExprAST':
                    {'try_block': make_ast_tree(a.try_block),
                     'catch_block': make_ast_tree(a.catch_block),
                     'finally_block': make_ast_tree(a.finally_block),
                     'error_name': make_ast_tree(a.name)}}

    elif isinstance(a, ast.ObjectPatternExpr):
        return {'ObjectPatternAST': 
                    {
                        'left': make_ast_tree(a.left),
                        'keys': make_ast_tree(a.keys),
                        'values': make_ast_tree(a.values)}}

    elif isinstance(a, ast.ForeachStmt):
        return {
            'ForeachStmt': {
                'target': make_ast_tree(a.target),
                'iter': make_ast_tree(a.iter),
                'body': make_ast_tree(a.body),
            }
        }

    elif isinstance(a, ast.BlankNode):
        return {'<blank node>'}

    elif isinstance(a, ast.TupleAST):
        return {
            'items': make_ast_tree(a.items),
        }

    elif isinstance(a, list):
        return unpack_list(a)

    return a
