import sys

from .alex import Lex
from .aparser import Parser, ASTConverter
from .version import (
    AIL_VERSION, AIL_COPYRIGHT, AIL_VERSION_NUMBER,
    AIL_VERSION_NAME, AIL_VERSION_FULL_STRING
)

from ail.core.namespace import fill_namespace
from ail.core.exceptions import print_py_traceback

from . import error, tokentype as tokent

from ..modules import shcompleter

_readline_availble = True
try:
    import readline
except ImportError:
    _readline_availble = False

error.ERR_NOT_EXIT = True
error.THROW_ERROR_TO_PYTHON = True

DISABLE_WORD_BLOCK = True

_MORE_KEYWORD = ('is', 'then', 'do', 'try', 'finally')
_END_KEYWORD = ('loop', 'end', 'endif', 'wend', 'catch')

_VER_STR = '%s [%s]' % (
    AIL_VERSION_FULL_STRING,
    AIL_VERSION_NUMBER,
)
_WELCOME_STR = \
'''AIL %s (Python %s)
Type 'help(...)', '$help', 'copyright()', 'python_copyright()' to get more information, 'exit()' to exit.
''' % (
        _VER_STR,
        sys.version,
    )

_SH_HELP_STR = \
    '''AIL shell commands:
    $help   get commands help
    $exit   exit shell forcibly
    $break  break more mode forcibly
    $edit   editor mode
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

        self.__lexer = Lex()
        self.__parser = Parser()
        self.__converter = ASTConverter()

        self.__pyc_globals = {}
        self.__pyc_globals.update(_SHELL_PYC_NAMESPACE)

        self.__setup_readline_completer()

    def __setup_readline_completer(self):
        if _readline_availble:
            completer = shcompleter.Completer(self.__pyc_globals)
            readline.set_completer(completer.complete)
            readline.parse_and_bind('tab: complete')

    def __get_more_line_state(self, line: str) -> int:
        """
        :return : -1 end more | 0 normal | 1 start more
        """

        ts = Lex().lex(line)

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
            t = self.__lexer.lex(line, '<shell>')
            t = self.__parser.parse(t, line, '<shell>', True)
            n = self.__converter.convert_single(t)
            c = compile(n, '<shell>', 'single')

            exec(c, self.__pyc_globals)
        except Exception:
            print_py_traceback()

    __run_single_line = __run_single_line_pyc

    def __run_block(self):
        self.__run_single_line('\n'.join(self.__buffer), True)

        self.__buffer = []

    def run_shell(self):
        self.__run_shell()

    def __run_shell(self):
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

                if not in_edit:
                    more = self.__get_more_line_state(line)

                if line == '$exit':
                    break

                elif line == '$break':
                    self.__buffer.clear()
                    self.__more_level = 0
                    in_more = False
                    ps = self.ps1
                    continue

                elif line == '$edit':
                    self.__buffer.clear()
                    self.__more_level = 0
                    in_edit = True
                    in_more = True
                    ps = self.ps3
                    print('(editor mode, ^C - cancel, ^D - run code.)')

                elif line == '$help':
                    print(_SH_HELP_STR)
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
