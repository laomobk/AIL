# AST

class ExprAST:
    '''
    这是所有 表达式AST 的父类
    '''
    pass


class ArgListAST:
    '''
    arg_list := expr [',' expr]*
    '''

    def __init__(self, exp_list :list):
        self.exp_list = exp_list


class CallExprAST:
    '''
    call_expr := NAME '(' arg_list ')'
    '''

    def __init__(self, call_name :str, arg_list :ArgListAST):
        self.name = call_name
        self.arg_list = arg_list


class CellAST:
    '''
    cell := NUMBER | NAME | STRING | call_expr
    '''

    def __init__(self, value :object):
        self.value = value


class PowerExprAST:
    '''
    pow_expr := cell ['^' cell]
    '''

    def __init__(self, left :CellAST, right :CellAST):
        self.left = left
        self.right = right


class ModExprAST:
    '''
    mod_expr := pow_expr ['MOD' pow_expr]
    '''
    def __init__(self, left :PowerExprAST, right :PowerExprAST):
        self.left = left
        self.right = right


class MuitDivExprAST:
    '''
    md_expr := mod_expr [('*' | '/') mod_expr]
    '''
    def __init__(self, op :str, left :ModExprAST, right :ModExprAST):
        self.op = op
        self.left = left
        self.right = right


class BinaryExprAST:
    '''
    real_expr := md_expr [('+' | '-') md_expr]* | '(' real_expr ')'
    '''
    def __init__(self, op :str, left :MuitDivExprAST, right :MuitDivExprAST):
        self.op = op
        self.left = left
        self.right = right


class ValueListAST:
    '''
    val_list := NAME [',' NAME]
    '''
    def __init__(self, v_list :list):
        self.v_list = v_list


class DefineExprAST(ExprAST):
    '''
    def_expr := NAME '=' expr NEWLINE
    '''
    def __init__(self, name :str, value :ExprAST):
        self.value = value
        self.name = name


class PrintExprAST(ExprAST):
    '''
    print_expr := 'PRINT' expr [';' expr]* NEWLINE
    '''
    def __init__(self, value_list :list):
        self.v_list = value_list


class InputExprAST(ExprAST):
    '''
    input_expr := 'INPUT' expr ';' val_list NEWLINE
    '''
    def __init__(self, msg :ExprAST, val_list :ValueListAST):
        self.msg = msg
        self.v_list = val_list



