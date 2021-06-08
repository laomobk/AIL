
from .abytecode import (
    ByteCodeFileBuffer,
    LineNumberTableGenerator
)
from . import aobjects as obj, asts as ast, aopcode as opcs


def print_pyast(tree):
    dump_func = None
    
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

    elif isinstance(a, ast.MuitDivExprAST):
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
                            'star': a.star}}

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

    elif isinstance(a, ast.FunctionDefineAST):
        return {
            'FunctionDefAST':
                {
                    'name': a.name,
                    'arg_list': make_ast_tree(a.arg_list),
                    'block': make_ast_tree(a.block),
                    'bindto': make_ast_tree(a.bindto),
                    'decorator': make_ast_tree(a.decorator)}}

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

    elif isinstance(a, ast.MapAST):
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
            'right': make_ast_tree(a.right)}}

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

    elif isinstance(a, list):
        return unpack_list(a)

    return a


class ByteCodeDisassembler:
    __SHOW_VARNAME = (
        opcs.store_var,
        opcs.load_global,
        opcs.load_local,
        opcs.load_variable,
        opcs.store_function,
        opcs.load_varname,
        opcs.load_module,
        opcs.load_attr,
        opcs.store_attr,
        opcs.setup_catch,
        opcs.bind_function,
        opcs.import_from,
    )

    __SHOW_CONST = (
        opcs.load_const,
        opcs.import_name,
        opcs.load_module,
    )

    __SHOW_COMPARE_OP = (
        opcs.compare_op,
    )

    __SHOW_JUMPPOINT = (
        opcs.jump_if_false_or_pop,
        opcs.jump_if_true_or_pop,
        opcs.jump_absolute,
        opcs.jump_if_false
    )

    def __init__(self):
        self.__now_buffer: ByteCodeFileBuffer = None

        self.__lnotab_cursor = 0
        self.__offset_counter = 0

        self.__jump_point_table = []

        self.__dis_task = []

    @property
    def __lnotab(self) -> LineNumberTableGenerator:
        return self.__now_buffer.lnotab

    @property
    def __varnames(self) -> list:
        return self.__now_buffer.varnames

    @property
    def __consts(self) -> list:
        return self.__now_buffer.consts

    @property
    def __bytecodes(self) -> list:
        return self.__now_buffer.bytecodes.blist \
            if not isinstance(self.__now_buffer, obj.AILCodeObject) \
            else self.__now_buffer.bytecodes

    def __check_lno(self) -> bool:
        if self.__lnotab.table[self.__lnotab_cursor] == self.__offset_counter:
            self.__offset_counter = 0
            self.__move_lnotab_cursor()
            return True
        return False

    def __move_lnotab_cursor(self):
        self.__lnotab_cursor += 2

    def __get_opname(self, opcode: int) -> str:
        for k, v in opcs.__dict__.items():
            if opcode == v:
                return k

    def __get_opcode_comment(self, opcode: int, argv: int) -> str:
        cmt = '( %s )'

        if opcode in self.__SHOW_CONST:
            c = self.__consts[argv]

            if isinstance(c, obj.AILCodeObject) and c not in self.__dis_task:
                self.__dis_task.append(c)

            return cmt % repr(c)

        elif opcode in self.__SHOW_VARNAME:
            return cmt % self.__varnames[argv]

        elif opcode in self.__SHOW_COMPARE_OP:
            return cmt % repr(opcs.COMPARE_OPERATORS[argv])

        return ''

    def __check_jump_point(self, opcode: int, argv: int):
        if opcode not in self.__SHOW_JUMPPOINT:
            return

        if argv not in self.__jump_point_table:
            self.__jump_point_table.append(argv)

    def __get_jump_point_commit(self) -> str:
        if self.__offset_counter in self.__jump_point_table:
            self.__jump_point_table.remove(self.__offset_counter)
            return '<<'
        return ''

    def disassemble(self, buffer_: ByteCodeFileBuffer):
        self.__dis_task.append(buffer_)

        while self.__dis_task:
            now_tsk = self.__dis_task.pop(0)

            print('Disassembly of %s:\n' % (now_tsk
                                            if isinstance(now_tsk, obj.AILCodeObject)
                                            else now_tsk.code_object))

            self.disassemble_single(now_tsk)

    def disassemble_single(self, buffer_: ByteCodeFileBuffer):
        self.__now_buffer = buffer_

        # print('lnotab :', self.__now_buffer.lnotab.table)

        self.__move_lnotab_cursor()  # 跳过第一对

        for bi in range(0, len(self.__bytecodes), 2):
            bc = self.__bytecodes[bi]
            argv = self.__bytecodes[bi + 1]

            try:
                comment = self.__get_opcode_comment(bc, argv)
            except Exception as e:
                comment = '!(bad argv: %s  exception: %s)' % (argv, e)

            self.__check_jump_point(bc, argv)

            lni = int(bi / 2)

            if 0 <= lni < len(self.__now_buffer.lineno_list):
                ln = self.__now_buffer.lineno_list[lni]
            else:
                ln = -1

            print('\t', ln if ln >= 0 else '', bi, self.__get_opname(bc), argv,
                  comment, self.__get_jump_point_commit(),
                  sep='\t')

            self.__offset_counter += 2

            # if self.__check_lno():
            #     print()

        print()


def show_bytecode(bf: ByteCodeFileBuffer):
    diser = ByteCodeDisassembler()

    diser.disassemble(bf)


def get_opname(op: int):
    for k, v in opcs.__dict__.items():
        if v == op:
            return k
