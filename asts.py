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

    def __init__(self, exp_list :list, ln :int):
        self.exp_list = exp_list
        self.ln = ln


class CallExprAST:
    '''
    call_expr := NAME '(' arg_list ')'
    '''

    def __init__(self, call_name :str, arg_list :ArgListAST, ln :int):
        self.name = call_name
        self.arg_list = arg_list
        self.ln = ln


class CellAST:
    '''
    cell := NUMBER | NAME | STRING | call_expr
    '''

    def __init__(self, value :object, _type :int, ln :int):
        self.value = value
        self.type = _type
        self.ln = ln

    def __str__(self):
        return '<Cell value = \'%s\'>' % self.value

    __repr__ = __str__


class PowerExprAST:
    '''
    pow_expr := cell ['^' cell]
    '''

    def __init__(self, left :CellAST, right :CellAST, ln :int):
        self.left = left
        self.right = right
        self.ln = ln


class ModExprAST:
    '''
    mod_expr := pow_expr ['MOD' pow_expr]
    '''
    def __init__(self, left :PowerExprAST, right :PowerExprAST, ln :int):
        self.left = left
        self.right = right
        self.ln = ln


class MuitDivExprAST:
    '''
    md_expr := mod_expr [('*' | '/') mod_expr]
    '''
    def __init__(self, op :str, left :ModExprAST, right :ModExprAST, ln :int):
        self.op = op
        self.left = left
        self.right = right
        self.ln = ln


class BinaryExprAST:
    '''
    real_expr := md_expr [('+' | '-') md_expr]* | '(' real_expr ')'
    '''
    def __init__(self, op :str, left :MuitDivExprAST, right :MuitDivExprAST, ln :int):
        self.op = op
        self.left = left
        self.right = right
        self.ln = ln


class ValueListAST:
    '''
    val_list := NAME [',' NAME]
    '''
    def __init__(self, v_list :list, ln :int):
        self.value_list = v_list
        self.ln = ln

    def __str__(self):
        return '<ValueList %s>' % str(self.v_list)


class DefineExprAST(ExprAST):
    '''
    def_expr := NAME '=' expr NEWLINE
    '''
    def __init__(self, name :str, value :ExprAST, ln :int):
        self.value = value
        self.name = name
        self.ln = ln


class PrintExprAST(ExprAST):
    '''
    print_expr := 'PRINT' expr [';' expr]* NEWLINE
    '''
    def __init__(self, value_list :list, ln :int):
        self.value_list = value_list
        self.ln = ln


class InputExprAST(ExprAST):
    '''
    input_expr := 'INPUT' expr ';' val_list NEWLINE
    '''
    def __init__(self, msg :ExprAST, val_list :ValueListAST, ln :int):
        self.msg = msg
        self.value_list = val_list
        self.ln = ln


class CmpTestAST:
    '''
    cmp_test := expr [cmp_op expr]*
    '''
    def __init__(self, left :ExprAST, right :list, ln :int):
        self.left = left
        self.right = right
        self.ln = ln


class AndTestAST:
    '''
    and_test := cmp_test ['and' cmp_test]
    '''
    def __init__(self, left :CmpTestAST, right :list, ln :int):
        self.left = left
        self.right = right
        self.ln = ln


class OrTestAST:
    '''
    or_test := and_test ['or' and_test]*
    '''
    def __init__(self, left :AndTestAST, right :list, ln :int):
        self.left = left
        self.right = right
        self.ln = ln


class TestExprAST:
    '''
    test := or_test
    '''
    def __init__(self, test :OrTestAST, ln :int):
        self.test = test
        self.ln = ln


class BlockExprAST:
    '''
    BLOCK := stmt*
    '''
    def __init__(self, stmts :list, ln :int):
        self.stmts = stmts
        self.ln = ln


class IfExprAST:
    '''
    if_else_expr := 'if' test 'then' NEWLINE
                BLOK
                (
                 'else' NEWLINE
                 BLOCK
                )
                'endif'
    '''

    def __init__(self, test :TestExprAST, 
            block :BlockExprAST, else_block :BlockExprAST, ln :int):
        self.test = test
        self.block = block
        self.else_block = else_block
        self.ln = ln


class WhileExprAST:
    '''
    while_expr := 'while' test 'then'
        BLOCK
        'wend' NEWLINE'
    '''

    def __init__(self, test :TestExprAST, block :BlockExprAST, ln :int):
        self.test = test
        self.block = block
        self.ln = ln


class DoLoopExprAST:
    '''
    do_loop_expr := 'do' 'NEWLINE
                BLOCK
                'loop' 'until' test NEWLINE
    '''

    def __init__(self, test :TestExprAST, block :BlockExprAST, ln :int):
        self.test = test
        self.block = block
        self.ln = ln


class FunctionDefineAST:
    '''
    func_def := 'fun' NAME '(' arg_list ')' NEWLINE
                BLOCK
            'end'
    '''

    def __init__(self, name :str, arg_list :ArgListAST, block :BlockExprAST, ln :int):
        self.name = name
        self.arg_list = arg_list
        self.block = block
        self.ln = ln


class ReturnAST:
    '''
    return_stmt := 'return' expr
    '''

    def __init__(self, expr :ExprAST, ln :int):
        self.expr = expr
        self.ln = ln


class ContinueAST:
    '''
    continue_stmt := 'continue'
    '''
    def __init__(self, ln :int):
        self.ln = ln


class BreakAST:
    '''
    break_stmt := 'break'
    '''
    def __init__(self, ln :int):
        self.ln = ln


class NullLineAST:
    '''
    null_line := NEWLINE
    '''
    def __init__(self, ln :int):
        self.ln = ln


class EOFAST:
    def __init__(self, ln :int):
        self.ln = ln



BINARY_AST_TYPES = (
        CellAST,
        PowerExprAST,
        ModExprAST,
        MuitDivExprAST,
        BinaryExprAST,
        DefineExprAST,
        CallExprAST
        )
