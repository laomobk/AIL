import sys

from core.alex import Lex
from core.aparser import Parser
from core.acompiler import Compiler
from core.avm import Interpreter, Frame, _BUILTINS

from objects import function
from objects import string

from core import aobjects as objs, error, tokentype as tokent

import os

try:
    import readline
except ImportError:
    pass

error.ERR_NOT_EXIT = True
error.THROW_ERROR_TO_PYTHON = True

_MORE_KEYWORD = ('is', 'then', 'do')
_END_KEYWORD = ('loop', 'end', 'endif', 'wend')


def _sh_exit():
    sys.exit(0)

_SHELL_NAMESPACE = {
        'exit' : objs.ObjectCreater.new_object(function.PY_FUNCTION_TYPE, _sh_exit),
        }

_SHELL_NAMESPACE.update(_BUILTINS)


class Shell:
    def __init__(self):
        self.__buffer = []

        self.ps1 = '>> '
        self.ps2 = '.. '

        self.__more_level = 0

        self.__temp_name = '.temp.tmp'
        self.__fbuffer = open(self.__temp_name,'w')

        self.__program = 'begin\n%s\nend\n'

        self.__main_frame = Frame()
        self.__main_frame.variable = _SHELL_NAMESPACE

        self.__lexer = Lex(self.__temp_name)
        self.__parser = Parser(self.__temp_name)
        self.__compiler = Compiler(filename='<shell>')
        self.__inter = Interpreter()

    def __write(self, line :str):
        if self.__fbuffer.closed:
            self.__fbuffer = open(self.__temp_name, 'w')

        self.__fbuffer.write(line + '\n')

        self.__fbuffer.close()

    def __read(self) -> str:
        if self.__fbuffer.closed:
            self.__fbuffer = open(self.__temp_name, 'r', encoding='UTF-8')

        s = self.__fbuffer.read()

        self.__fbuffer.close()

        return s

    def __get_more_line_state(self, line :str) -> int:
        '''
        :return : -1 end more | 0 normal | 1 start more
        '''
        self.__write(line)

        ts = Lex(self.__temp_name).lex()

        for tok in ts.token_list[::-1]:
            if tok.ttype == tokent.LAP_IDENTIFIER:
                if tok.value in _MORE_KEYWORD:
                    return 1
                if tok.value in _END_KEYWORD:
                    return -1

        return 0

    def __print_welcome_text(self):
        v = ''

        try:
            v = _BUILTINS['__version__']
        except KeyError:
            pass
        
        print('AIL shell %s' % ('(AIL version = %s)' % v) if v else '')
        print('Type \'exit()\' to exit.\n')

    def __run_single_line(self, line :str, block=False):
        single_line = not block

        self.__write(self.__program % line)

        t = self.__lexer.lex(self.__temp_name)
        t = self.__parser.parse(t)
        cobj = self.__compiler.compile(t, single_line=single_line).code_object

        self.__main_frame.code = cobj
        self.__main_frame.varnames = cobj.varnames
        self.__main_frame.consts = cobj.consts

        self.__inter.exec(cobj, self.__main_frame)

        if self.__main_frame.stack:
            print(repr(self.__main_frame.stack.pop()))
    
    def __run_block(self):
        self.__run_single_line('\n'.join(self.__buffer), True)

        self.__buffer = []

    def __read_temp_file(self):
        return open(self.__temp_name).read()

    def run_shell(self):
        try:
            self.__run_shell()
        finally:
            os.remove(self.__temp_name)

    def __run_shell(self):
        self.__print_welcome_text()

        ps = self.ps1
        
        in_more = False
        
        while True:
            try:
                line = input(ps)

                more = self.__get_more_line_state(line)

                if more == 1:
                    self.__more_level += 1
                    in_more = True
                    ps = self.ps2
                    self.__buffer.append(line)

                elif more == -1:
                    self.__more_level -= 1 if self.__more_level > 0 else 0
                    self.__buffer.append(line)

                    if self.__more_level == 0:
                        in_more = False
                        ps = self.ps1
                        self.__run_block()

                elif self.__more_level >= 0:
                    if in_more:
                        self.__buffer.append(line)
                    else:
                        self.__run_single_line(line)

            except error._AILRuntimeError as e:
                in_more = False
                print(str(e))
                self.__main_frame.stack = []
                self.__buffer = []

            except EOFError as e:
                print()
                break

            except KeyboardInterrupt as e:
                in_more = False
                print('\n%s' % str(type(e).__name__))
                self.__buffer = []

            self.__main_frame.variable['__temp__'] = \
                    string.convert_to_string(self.__read_temp_file())

            open(self.__temp_name, 'w').close()  # reset temp


if __name__ == '__main__':
    Shell().run_shell()
