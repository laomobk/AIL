import asts as ast
import opcodes as opcs

def unpack_list(l :list):
    rl = []
    for d in l:
        if isinstance(d, tuple):
            rl.append(unpack_list(d))
        else:
            rl.append(make_ast_tree(d))
    return rl

def make_ast_tree(a) -> dict:
    if isinstance(a, ast.CellAST):
        return {'Cell' : {'value' : a.value, 'type' : a.type}}

    elif isinstance(a, ast.PowerExprAST):
        return {'PowerAST' : {'left' : make_ast_tree(a.left), 'right' : make_ast_tree(a.right)}}
    
    elif isinstance(a, ast.ModExprAST):
        return {'ModAST' : {'left' : make_ast_tree(a.left), 'right' : make_ast_tree(a.right)}}

    elif isinstance(a, ast.MuitDivExprAST):
        return {'MDAST' : {'left' : make_ast_tree(a.left), 'right' : make_ast_tree(a.right)}}

    elif isinstance(a, ast.BinaryExprAST):
        return {'BinAST' : {'left' : make_ast_tree(a.left), 'right' : make_ast_tree(a.right)}}

    elif isinstance(a, ast.CallExprAST):
        return {'CallAST' : {'name' : a.name, 'arg_list' : make_ast_tree(a.arg_list)}}

    elif isinstance(a, ast.PrintExprAST):
        return {'PrintAST' : {'value' : unpack_list(a.value_list)}}

    elif isinstance(a, ast.InputExprAST):
        return {'InputAST' : {'msg' : make_ast_tree(a.msg), 'list' : make_ast_tree(a.value_list)}}
    
    elif isinstance(a, ast.ArgListAST):
        return {'ArgList' : unpack_list(a.exp_list)}

    elif isinstance(a, ast.ValueListAST):
        return {'ValueList' : unpack_list(a.value_list)}

    elif isinstance(a, ast.DefineExprAST):
        return {'DefAST' : {'name' : a.name, 'value' : make_ast_tree(a.value)}}

    elif isinstance(a, ast.CmpTestAST):
        return {'CmpAST' : {'left' : make_ast_tree(a.left), 'right' : unpack_list(a.right)}}

    elif isinstance(a, ast.AndTestAST):
        return {'AndAST' : {'left' : make_ast_tree(a.left), 'right' : make_ast_tree(a.right)}}

    elif isinstance(a, ast.OrTestAST):
        return {'OrAST' : {'left' : make_ast_tree(a.left), 'right' : make_ast_tree(a.right)}}

    elif isinstance(a, ast.TestExprAST):
        return {'TestAST' : make_ast_tree(a.test)}

    elif isinstance(a, ast.BlockExprAST):
        return {'BlockAST' : unpack_list(a.stmts)}

    elif isinstance(a, ast.IfExprAST):
        return {'IfAST' : 
                {'test' : make_ast_tree(a.test), 
                 'body' : make_ast_tree(a.block), 
                 'else_block' : make_ast_tree(a.else_block)}}

    elif isinstance(a, ast.WhileExprAST):
        return {'WhileAST' : 
                {'test' : make_ast_tree(a.test), 
                 'body' : make_ast_tree(a.block)}}

    elif isinstance(a, ast.DoLoopExprAST):
        return {'DoLoopAST' : 
                {'test' : make_ast_tree(a.test), 
                 'body' : make_ast_tree(a.block)}}

    elif isinstance(a, ast.FunctionDefineAST):
        return {
                'FunctionDefAST' :
                {
                    'name' : a.name,
                    'arg_list' : make_ast_tree(a.arg_list),
                    'block' : make_ast_tree(a.block)}}

    elif isinstance(a, ast.ReturnAST):
        return {'ReturnAST' : {'expr' : make_ast_tree(a.expr)}}

    elif isinstance(a, ast.BreakAST):
        return 'BreakAST'
    
    elif isinstance(a, ast.ContinueAST):
        return 'ContinueAST'
 
    elif isinstance(a, list):
        return unpack_list(a)

    return a


def show_bytecode(bc):
    bl = bc.blist

    print(bl)

    for bi in range(0, len(bl), 2):
        b = bl[bi]
        # find opname
        for k, v in opcs.__dict__.items():
            if b == v:
                print(k, bl[bi + 1], sep='\t')
