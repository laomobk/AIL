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

    def __init__(self, value :object, _type :int):
        self.value = value
        self.type = _type

    def __str__(self):
        return '<Cell value = \'%s\'>' % self.value

    __repr__ = __str__


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
        self.value_list = v_list

    def __str__(self):
        return '<ValueList %s>' % str(self.v_list)


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
        self.value_list = value_list


class InputExprAST(ExprAST):
    '''
    input_expr := 'INPUT' expr ';' val_list NEWLINE
    '''
    def __init__(self, msg :ExprAST, val_list :ValueListAST):
        self.msg = msg
        self.value_list = val_list


class CmpTestAST:
    '''
    cmp_test := expr [cmp_op expr]*
    '''
    def __init__(self, left :ExprAST, right :list):
        self.left = left
        self.right = right


class AndTestAST:
    '''
    and_test := cmp_test ['and' cmp_test]
    '''
    def __init__(self, left :CmpTestAST, right :list):
        self.left = left
        self.right = right


class OrTestAST:
    '''
    or_test := and_test ['or' and_test]*
    '''
    def __init__(self, left :AndTestAST, right :list):
        self.left = left
        self.right = right


class TestExprAST:
    '''
    test := or_test
    '''
    def __init__(self, test :OrTestAST):
        self.test = test


class BlockExprAST:
    '''
    BLOCK := stmt*
    '''
    def __init__(self, stmts :list):
        self.stmts = stmts


class IfExprAST:
    '''
    if_else_expr := 'if' test 'then' NEWLINE
                BLOCK
                'endif'
                'else' NEWLINE
                BLOCK
                'endif' NEWLINE
    '''

    def __init__(self, test :TestExprAST, block :BlockExprAST, else_block :BlockExprAST):
        self.test = test
        self.block = block
        self.else_block = else_block


class WhileExprAST:
    '''
    while_expr := 'while' test 'then'
        BLOCK
        'wend' NEWLINE'
    '''

    def __init__(self, test :TestExprAST, block :BlockExprAST):
        self.test = test
        self.block = block


class DoLoopExprAST:
    '''
    do_loop_expr := 'do' 'NEWLINE
                BLOCK
                'loop' 'until' test NEWLINE
    '''

    def __init__(self, test :TestExprAST, block :BlockExprAST):
        self.test = test
        self.block = block


class FunctionDefineAST:
    '''
    func_def := 'fun' NAME '(' arg_list ')' NEWLINE
                BLOCK
            'end'
    '''

    def __init__(self, name :str, arg_list :ArgListAST, block :BlockExprAST):
        self.name = name
        self.arg_list = arg_list
        self.block = block


class ContinueAST:
    '''
    continue_stmt := 'continue'
    '''
    pass


class BreakAST:
    '''
    break_stmt := 'break'
    '''
    pass


class NullLineAST:
    '''
    null_line := NEWLINE
    '''
    pass


class EOFAST:
    pass
