from dis import opname, cmp_op
from typing import List

from . import asts as ast
from . import acompile
from . import pyopcode as pyop

from .version import AIL_VERSION


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
        return {'Cell': {
            'value': a.value, 'type': a.type,
            'symbol': a.symbol,
        }
        }

    elif isinstance(a, ast.UnaryExprAST):
        return {'UnaryAST': {'op': a.op, 'right': make_ast_tree(a.expr)}}

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
                'when': make_ast_tree(a.when_test)
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
                    'type_comment': make_ast_tree(a.type_comment),
                    'symbol': a.symbol
                }
        }

    elif isinstance(a, ast.ClassDefineAST):
        return {'ClassDefAST':
            {
                'name': a.name,
                'bases': make_ast_tree(a.bases),
                'func': make_ast_tree(a.func),
                'symbol': a.symbol,
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
                     'catch_case': make_ast_tree(a.catch_cases),
                     'finally_block': make_ast_tree(a.finally_block),
                     }}

    elif isinstance(a, ast.CatchCase):
        return {
            'CatchCase': {
                'exc_expr': make_ast_tree(a.exc_expr),
                'alias': make_ast_tree(a.alias),
                'block': make_ast_tree(a.block),
            }
        }

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
        return {'<blank node>': '<none>'}

    elif isinstance(a, ast.TupleAST):
        return {'TupleExpr': {
            'items': make_ast_tree(a.items),
        }}

    elif isinstance(a, ast.StarredExpr):
        return {
            'StarredExpr': {
                'value': make_ast_tree(a.value),
                'store': a.store,
            }
        }

    elif isinstance(a, ast.WithStmt):
        return {
            'WithStmt': {
                'items': make_ast_tree(a.items),
                'body': make_ast_tree(a.body),
            }
        }

    elif isinstance(a, ast.WithItem):
        return {
            'WithItem': {
                'context_expr': make_ast_tree(a.context_expr),
                'optional_var': make_ast_tree(a.optional_var),
            }
        }

    elif isinstance(a, ast.PyImportStmt):
        return {
            'PyImportStmt': {
                'names': make_ast_tree(a.names),
            }
        }

    elif isinstance(a, ast.PyImportAlias):
        return {
            'PyImportAlias': {
                'name': a.name,
                'alias': a.alias,
            }
        }

    elif isinstance(a, ast.PyImportFromStmt):
        return {
            'PyImportFrom': {
                'module': a.module,
                'names': make_ast_tree(a.names),
                'level': a.level,
            }
        }

    elif isinstance(a, list):
        return unpack_list(a)

    return a


class CFGDisassembler:
    _OP_VARNAME = (
        pyop.LOAD_NAME,
        pyop.LOAD_FAST,
        pyop.LOAD_GLOBAL
    )

    _OP_CONST = (
        pyop.LOAD_CONST,
    )

    _OP_JMP = (
        pyop.JUMP_FORWARD,
        pyop.JUMP_IF_FALSE_OR_POP,
        pyop.JUMP_IF_TRUE_OR_POP,
        pyop.JUMP_ABSOLUTE,
        pyop.POP_JUMP_IF_FALSE,
        pyop.POP_JUMP_IF_TRUE,
    )

    def __init__(self):
        self._unit: acompile.CompileUnit = None
        self._counter = 0

    def _get_description(self, instr: acompile.Instruction) -> str:
        opcode, arg = instr.opcode, instr.arg

        if self._unit is None:
            return ''

        unit = self._unit

        if opcode in self._OP_VARNAME:
            return unit.varnames[arg]
        elif opcode in self._OP_CONST:
            c = unit.consts[arg]
            return repr(c)
        elif opcode in self._OP_JMP:
            target = instr.target
            return 'to %s' % target
        elif opcode == pyop.COMPARE_OP:
            return cmp_op[arg]

        return ''

    def print_instructions_sequence(
            self, instr_seq: List[acompile.Instruction]):

        for instr in instr_seq:
            opcode = instr.opcode
            text = opname[opcode]
            desc = self._get_description(instr)

            line = '%03d %s\t\t%s %s' % (
                self._counter, text, instr.arg, ('(%s)' % desc) if desc else ''
            )

            print('\t' + line)
            self._counter += 2
        print()

    def _disassemble(self, block: acompile.BasicBlock):
        instr = block.instructions

        print('disassemble %s' % block)
        self.print_instructions_sequence(instr)

        if block.next_block is not None:
            self._disassemble(block.next_block)

    def disassemble(
            self, block: acompile.BasicBlock, unit: acompile.CompileUnit=None):
        print('CFG disassemble')
        print('AIL version: %s' % AIL_VERSION)

        self._counter = 0
        self._unit = unit
        self._disassemble(block)

        print()
