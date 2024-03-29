import dis
import sys
import os

from os.path import exists, join
from pprint import pprint

from .pyexec import ail_compile, CP_PY_AST, CP_PY_CODE
from .alex import Lex
from .aparser import Parser, ASTConverter
from .version import (
    AIL_VERSION, AIL_COPYRIGHT, AIL_VERSION_NUMBER,
    AIL_VERSION_NAME, AIL_VERSION_FULL_STRING
)

from ail.core.test_utils import make_ast_tree
from ail.core.namespace import fill_namespace
from ail.core.exceptions import print_py_traceback

from . import error, tokentype as tokent
from .. import _config

from ..modules import shcompleter

_readline_availble = True
try:
    import readline
except ImportError:
    _readline_availble = False


def try_get_commit_id():
    try:
        if os.name == 'nt':
            return
        if _config.RUN_FROM_ENTRY_POINT or not exists('AIL_REPO_ROOT'):
            return open(
                join(_config.AIL_DIR_PATH, 'COMMIT_ID')) \
                .read().replace('\n', '')

        import subprocess

        if not (exists('AIL_REPO_ROOT') and exists('.git')):
            return

        commit_id = subprocess.Popen(
            ['git rev-parse --short HEAD'],
            shell=True, stdout=subprocess.PIPE).communicate()[0] \
            .decode().replace('\n', '')
        branch_name = subprocess.Popen(
            ['git symbolic-ref --short -q HEAD'],
            shell=True, stdout=subprocess.PIPE).communicate()[0] \
            .decode().replace('\n', '')
        return '%s/%s' % (branch_name, commit_id)

    except Exception:
        return


commit_id = try_get_commit_id()
commit_id = None if not commit_id or len(commit_id) > 50 else commit_id

error.ERR_NOT_EXIT = True
error.THROW_ERROR_TO_PYTHON = True

DISABLE_WORD_BLOCK = True

AIL_HISTORY_FILE = '~/.ail_history'

_MORE_KEYWORD = ('is', 'then', 'do', 'try', 'finally')
_END_KEYWORD = ('loop', 'end', 'endif', 'wend', 'catch')

_VER_STR = '%s [%s]' % (
    AIL_VERSION_FULL_STRING,
    AIL_VERSION_NUMBER,
)

_WELCOME_STR = \
    '''AIL %s %s(Python %s)
Type 'help(...)', '$help', 'copyright()', 'python_copyright()' to get more information, 'exit()' or '.exit' to exit.
''' % (
        _VER_STR,
        ('(%s) ' % commit_id) if commit_id else '',
        sys.version,
    )

_SH_HELP_STR = \
    '''AIL shell commands:
    $help   get commands help
    $exit   exit shell forcibly
    $break  break more mode forcibly
'''


def _sh_exit():
    sys.exit(0)


def _sh_copyright():
    return AIL_COPYRIGHT


def _py_copyright():
    return copyright()


_SHELL_PYC_NAMESPACE = {
    'copyright': _sh_copyright,
    'python_copyright': copyright,
}

fill_namespace(_SHELL_PYC_NAMESPACE)


class Shell:
    def __init__(self):
        self.__buffer = []

        self.ps1 = '>> '
        self.ps2 = '.. '
        self.ps3 = '> '

        self.__more_level = 0
        self.__ast_inspect_mode = 0
        self.__native_compile = False

        self.__pyc_globals = {}
        self.__pyc_globals.update(_SHELL_PYC_NAMESPACE)
        
        self.__try_read_history_file()
        self.__setup_readline_completer()

    def __try_read_history_file(self):
        try:
            if _readline_availble:
                readline.read_history_file()
        except Exception as _:
            pass

    def __try_write_history_file(self):
        try:
            if _readline_availble:
                readline.write_history_file()
        except Exception as _:
            pass

    def __setup_readline_completer(self):
        if _readline_availble:
            completer = shcompleter.Completer(self.__pyc_globals)
            readline.set_completer(completer.complete)
            readline.parse_and_bind('tab: complete')

    def __get_more_line_state(self, line: str) -> int:
        """
        :return : -1 end more | 0 normal | 1 start more
        """

        try:
            ts = Lex().lex(line)
        except SyntaxError:
            return False

        for index, tok in enumerate(ts.token_list):
            if DISABLE_WORD_BLOCK:
                if tok.ttype in (
                        tokent.AIL_LLBASKET, tokent.AIL_MLBASKET, tokent.AIL_SLBASKET):
                    self.__more_level += 1
                elif tok.ttype in (
                        tokent.AIL_LRBASKET, tokent.AIL_MRBASKET, tokent.AIL_SRBASKET):
                    self.__more_level -= 1
            else:
                if tok.ttype == tokent.AIL_IDENTIFIER:
                    if tok.value in _MORE_KEYWORD:
                        self.__more_level += 1
                    if tok.value in _END_KEYWORD:
                        self.__more_level -= 1

        return self.__more_level > 0

    @staticmethod
    def __print_welcome_text():
        print(_WELCOME_STR)

    def __run_single_line_pyc(self, line: str, block: bool = False):
        try:
            c = ail_compile(
                line, '<shell>', 'single',
                compiler=CP_PY_CODE if self.__native_compile else CP_PY_AST)

            exec(c, self.__pyc_globals)
        except Exception:
            print_py_traceback()

    __run_single_line = __run_single_line_pyc

    def __run_block(self):
        self.__run_single_line('\n'.join(self.__buffer), True)

        self.__buffer = []

    def run_shell(self, native_compile_mode=False):
        self.__run_shell(native_compile_mode)

    def __run_shell(self, native_compile_mode=False):
        self.__native_compile = native_compile_mode

        if native_compile_mode:
            print('(native compile mode)')
            self.ps1 = '(n) >> '
            self.ps2 = '(n) .. '
            self.ps3 = '(n) > '

        self.__print_welcome_text()

        ps = self.ps1

        in_more = False
        in_edit = False
        run_buf = False

        more = False

        while True:
            try:
                if run_buf:
                    run_buf = False
                    self.__run_block()
                    continue

                line = input(ps)
                self.__try_write_history_file()

                if not in_edit:
                    more = self.__get_more_line_state(line)

                if line in ('$exit', '.exit'):
                    break

                elif line == ('$break', '.break'):
                    self.__buffer.clear()
                    self.__more_level = 0
                    in_more = False
                    ps = self.ps1
                    continue

                elif line == '$help':
                    print(_SH_HELP_STR)
                    continue

                elif line == '$ast_inspect':
                    self.__ast_inspect_mode = not self.__ast_inspect_mode
                    print('$ ast_inspect mode: %s' % self.__ast_inspect_mode)
                    continue

                if more:
                    in_more = True
                    ps = self.ps2
                    self.__buffer.append(line)
                else:
                    if in_more:
                        self.__buffer.append(line)
                        in_more = False
                        run_buf = True
                        ps = self.ps1
                    else:
                        self.__run_single_line(line)

            except error.BuiltinAILRuntimeError as e:
                in_more = False
                print(str(e), end='')
                self.__buffer = []

            except EOFError as e:
                if not in_edit:
                    print()
                    break
                in_edit = False
                in_more = False
                ps = self.ps1
                self.__more_level = 0
                run_buf = True
                print()

            except KeyboardInterrupt as e:
                in_more = False
                self.__more_level = 0
                ps = self.ps1
                self.__buffer.clear()

                if in_edit:
                    in_edit = False
                    ps = self.ps1

                print('\n%s' % str(type(e).__name__))
                self.__buffer = []


if __name__ == '__main__':
    Shell().run_shell()
