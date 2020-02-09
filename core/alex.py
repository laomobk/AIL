#用于ail的词法分析器

from core.tokentype import *
from core.error import error_msg

__author__ = 'LaomoBK'
 
ALEX_VERSION_NUM = (0, 1)   #数字版本号
ALEX_VERSION_EXTRA = 'Beta' #额外版本信息
ALEX_VERSION_DATE = (10, 27, 2019)


def skip_comment_line(source :str, cursor :int):
    '''
    source : 源码文件
    cursor : 源码字符指针
    返回指针右移增量
    '''
    cur = 0  #增量
    ccur = cursor  #原始字符指针
    while ccur < len(source):
        if source[ccur] == '\n':
            break
        cur += 1
        ccur += 1
    
    return cur + 1  #跳过回车


def skip_comment_block(source :str, cursor :int,) -> tuple:
    '''
    source : 源码文件
    cursor : 源码字符指针
    返回一个元祖
 
    字符指针错误值原因：
    -1 : 注释块不完整
 
    ( 字符指针右移增量 , 行号增量)
    '''
 
    ccur = cursor
    cur = 0  #指针右移增量
    lni = 0  #行号增量
 
    try:
        while True:
            if source[ccur] == '\n':
                lni += 1
            
            if source[ccur] == '*' and source[ccur + 1] =='/':
                cur += 2 #跨过 '/'
 
                return (cur, lni)  #( 字符指针右移增量 , 行号增量)
            ccur += 1
            cur += 1
    
    except IndexError:
        #一般是到文件尾部了 */ 没有 /
        return (-1, 0)


def get_identifier(source :str, cursor :int) -> tuple:
    '''
    source : 源码文件
    cursor : 源码字符指针
    
    返回一个元祖
    ( 字符指针增量 , 标识符内容)
    '''
 
    buffer = ''   #标识符内容缓冲区
    ccur = cursor  #原始字符指针
    cur = 0  #字符指针增量
 
    while ccur < len(source):
 
        if not (source[ccur].isnumeric() or  \
          source[ccur] == '_' or  \
          source[ccur].isalpha()):
            break
        
        buffer += source[ccur]
 
        ccur += 1
        cur += 1
 
    return (cur, buffer)


def get_number(source :str, cursor :int) -> tuple:
    '''
    source : 源码文件
    cursor : 源码字符指针

    指针错误值原因：
    -1 不正确的数字 （如7.2.6, 1x7x9）
    
    返回一个元祖
    ( 字符指针增量 , 数字字符串)
    '''
    buffer = ''   #数字字符串内容缓冲区
    ccur = cursor  #原始字符指针
    cur = 0  #字符指针增量

    seen_d = False
    seen_hex = False

    e_char = 'xXABCDEFabcdef.'
 
    while ccur < len(source):
        if not (source[ccur].isnumeric() or source[ccur] in e_char):
            break

        if source[ccur] == '.':
            if seen_d or seen_hex:
                return (-1, 0)
            seen_d = True
            pass

        if source[ccur] in ('x', 'X'):
            if seen_hex:
                return (-1, 0)
            
            if len(buffer) != 1 or source[ccur - 1] != '0':
                return (-1, 0)

            seen_hex = True

        buffer += source[ccur]
        cur += 1
        ccur += 1

    if not buffer[-1].isnumeric():
        return (-1, 0)
 
    return (cur, buffer)


def get_string(source :str, cursor :int) -> tuple:
    '''
    source : 源码文件
    cursor : 源码字符指针
 
    Lap支持多行字符串
 
    字符指针错误值原因：
    -1 : 字符串没有结束就到达EOF
    
    返回一个元祖
    ( 字符指针增量, 行号增量 , 数字字符串)
    '''
    buffer = ''   #字符串内容缓冲区
    ccur = cursor   #原始字符指针，跳过引号
    cur = 0  #字符指针增量
    lni = 0  #行号增量
 
    instr = False
    hasEND = False
 
    schr = '' #开始字符串的引号

    slen = len(source)

    tcur = 0
 
    while ccur < len(source):
        if instr and source[ccur] == '\\' and slen > ccur + 1 \
                and source[ccur + 1] in ('n', 'r', 't', 'a', '\'', '"', '\\'):
            # escape character
            target = {
                'n' : '\n',
                'r' : '\r',
                't' : '\t',
                'a' : '\a',
                '\'' : '\'',
                '"' : '"',
                '\\' : '\\'
            }.get(source[ccur + 1])

            if target == '\\':
                source = source[:ccur+1] + 'N' + source[ccur+2:] 
                # 随意取一个字符，防止发生"转义"

            buffer += target

            ccur += 2
            cur += 2

        if instr and source[ccur] == schr and source[ccur - 1] != '\\':
            hasEND = True  #是否是因为while的条件而退出
            break
 
        if source[ccur] == '\n':
            lni += 1

        if instr:
            buffer += source[ccur]

        cur += 1
        ccur += 1
 
        if not instr:
            schr = source[ccur-1]
            instr = True
 
    if not hasEND:  #如果字符串没有结束就到达EOF
        return (-1, 0, 0)
 
    return (cur+1, lni, buffer)  #跳过最后一个引号


class Cursor:  #字符指针类型
    '''
    指向源码中的字符的指针
    '''
    def __init__(self, value=0):
        self.value = value
 
 
class Token:
    def __init__(self, value :str, ttype :int, ln :int):
        self.value = value
        self.ttype = ttype
        self.ln = ln
 
    def __repr__(self):
        return '<Token \'{0}\'  Type:{1}  LineNumber:{2}>'.format(
            self.value,
            self.ttype,
            self.ln
            )

    def __eq__(self, obj :object):
        if isinstance(obj, str):
            return self.value == obj and self.ttype != LAP_STRING
        elif isinstance(obj, Token):
            return self.value == obj.value
        else:
            return super().__eq__(obj)
 
    def __ne__(self, obj :object):
        if isinstance(obj, str):
            return self.value != obj and self.ttype != LAP_STRING
        elif isinstance(obj, Token):
            return self.value != obj.value
        else:
            return super().__ne__(obj)

    __str__ = __repr__ 
 
 
class TokenStream:
    '''
    单词流
    '''
    def __init__(self):
        self.__tli = []
 
    def __iter__(self):
        return iter(self.__tli)
 
    def append(self, tok :Token):
        '''
        将 tok 增加到尾部
        '''
 
        self.__tli.append(tok)
 
    def __repr__(self):
        return repr(self.__tli)
 
    __str__ = __repr__
 
    def __getitem__(self, index):
        if isinstance(index, slice):
            return self.__tli[index]
 
        return self.__tli[index] \
                if len(self.__tli) > index  \
                else None
 
    def __len__(self):
        return len(self.__tli)
 
    @property
    def token_list(self):
        return self.__tli
 
 
class Lex:
    def __init__(self, filename :str, testmode=False):
        '''
        fp : 源码路径，当以'.$str:'开头且testmode=True时，则是分析.$str:以后的内容
        '''
 
        self.__filename = filename
 
        self.__source = open(filename, 'r', encoding='UTF-8').read()     \
            if not filename.startswith('.$str:')      \
            else (filename[len('.$str:'):] if testmode else open(filename, 'r', encoding='UTF-8').read())            
            #源码文件
 
        self.__cursor = Cursor()  #源码的字符指针
        self.__stream = TokenStream()
        self.__ln = 1  #行号

        self.__blevel = 0
        
    
    @property
    def __chp(self):
        '''
        指向源码字符的指针
        '''
        return self.__cursor.value
    
    @__chp.setter
    def __chp(self, v):
        self.__cursor.value = v
 
    def __movchr(self, step=1):
        '''
        移动字符指针
        '''
 
        self.__cursor.value += step
 
    @property
    def __chnow(self):
        '''
        此时此刻的字符
        越界则报语法错误
        '''
 
        return self.__source[self.__cursor.value]   \
            if self.__cursor.value < len(self.__source)     \
            else error_msg(-1, 'Syntax error', self.__filename)
 
    def __nextch(self, ni=1):
        '''
        返回__source[self.__cursor.value + ni]
        如果越界，则报语法错误
        '''
        return self.__source[self.__cursor.value + ni]      \
            if self.__cursor.value + ni < len(self.__source)       \
            else '<EOF>'
 
    def lex(self, filename=None) -> TokenStream:
        if filename is not None:
            self.__filename = filename
            self.__source = open(filename, 'r', encoding='UTF-8').read()

            self.__cursor = Cursor()  # 源码的字符指针
            self.__stream = TokenStream()
            self.__ln = 1  # 行号

            self.__blevel = 0

        buffer = ''
        
        while self.__chp < len(self.__source):
            c = self.__chnow
            
            if ord(c) == 10:
                self.__ln += 1
                self.__movchr(1)

                if self.__blevel == 0:
                    self.__stream.append(Token(
                        '\n',
                        LAP_ENTER,
                        self.__ln
                    ))

            elif c == '-':
                if self.__nextch() == '-':
                    self.__stream.append(Token('--',
                                               LAP_SUB_SUB,
                                               self.__ln))
                    self.__movchr(2)

                elif self.__nextch().isdigit():
                    self.__movchr()

                    mov, buf = get_number(self.__source, self.__chp)
                    self.__stream.append(Token(
                        '-' + buf,
                        LAP_NUMBER,
                        self.__ln
                    ))
                    self.__movchr(mov)

                elif self.__nextch() == '=':
                    self.__stream.append(
                        Token('-=',
                              LAP_INP_SUB,
                              self.__ln
                              ))
                    self.__movchr(2)
                else:
                    self.__stream.append(Token(c,
                            LAP_SUB,
                            self.__ln))
                    self.__movchr(1)
 
            elif c in ('+', '*', '^', '%', '|', '&'):  #除法和减法有点特殊
                if self.__nextch() == '=':  #原地运算
                    self.__stream.append(Token(c+'=', 
                        {
                            '+':LAP_INP_PLUS,
                            '*':LAP_INP_MUIT,
                            '%':LAP_INP_MOD,
                            '^':LAP_INP_XOR,
                        }[c],   #根据c得到单词类型 
                    self.__ln))
                    self.__movchr(2)
 
                elif self.__nextch() == '+':  #自增自减
                    self.__stream.append(Token(c+c,
                        LAP_PLUS_PLUS if self.__nextch() == '+' else LAP_SUB_SUB,
                        self.__ln))
                    self.__movchr(2)
 
                elif c == '|' and self.__nextch() == '|':  # ||
                    self.__stream.append(Token(
                        '||',
                        LAP_OR,
                        self.__ln
                    ))
                    self.__movchr(2)
 
                elif c == '&' and self.__nextch() == '&':   # &&
                    self.__stream.append(Token(
                        '&&',
                        LAP_AND,
                        self.__ln
                    ))
                    self.__movchr(2)
 
                else:
                    self.__stream.append(Token(c,
                        {
                            '+':LAP_PLUS,
                            '*':LAP_MUIT,
                            '%':LAP_MOD,
                            '^':LAP_XOR,
                            '|':LAP_BIN_OR,
                            '&':LAP_BIN_AND
                        }[c], 
                    self.__ln))
                    self.__movchr(1)
 
            elif c in ('>', '<'):
                if self.__nextch() in ('>', '<'):   #左位移，右位移
                    if self.__nextch(2) == '=':      #<<=, >>=
                        if c+self.__nextch() not in ('<<', '>>'):
                            error_msg(self.__ln,
                                'Syntax error:{0}'.format(c + self.__nextch()+self.__nextch(2)),
 
                                self.__filename)
 
                        self.__stream.append(Token(c+c+'=',
                            {
                                '>>':LAP_INP_RSHIFT,
                                '<<':LAP_INP_LSHIFT
                            }.get(c+self.__nextch()),
                            self.__ln
                        ))
 
                        self.__movchr(3)
                    
                    else:   #普通左右位移和参数类型
                        if c+self.__nextch() not in ('<<', '>>'):
                            if c+self.__nextch() == '<>': #空参数列表
                                self.__stream.append(Token(
                                    '<',
                                    LAP_SMALER,
                                    self.__ln
                                    ))
 
                                self.__stream.append(Token(
                                    '>',
                                    LAP_LARGER,
                                    self.__ln
                                    ))
                                
                                self.__movchr(2)
                                continue  #跳过
 
                            error_msg(self.__ln, 
                                    'Syntax error:{0}'.format(c + self.__nextch()),
                                    self.__filename)
 
                        self.__stream.append(Token(
                            c+self.__nextch(),
                            {
                                '>>':LAP_INP_RSHIFT,
                                '<<':LAP_INP_LSHIFT
                            }[c+self.__nextch()],
                            self.__ln
                        ))
                        self.__movchr(2)
 
                elif self.__nextch() == '=':  #>=, <=
                    self.__stream.append(Token(
                        c+'=',
                        LAP_LARGER_EQ if c == '>' else LAP_SMALER_EQ,
                        self.__ln  
                    ))
                    self.__movchr(2)
 
                else:   #>, <
                    self.__stream.append(Token(
                        c,
                        LAP_LARGER if c == '>' else LAP_SMALER,
                        self.__ln 
                    ))
                    self.__movchr()
 
            elif c == '/':  #斜杠
                if self.__nextch() == '/':  #单行注释
                    #移动指针至下一行或EOF
                    self.__movchr(skip_comment_line(self.__source, self.__chp))
                    self.__stream.append(Token(
                        '\n', 
                        LAP_ENTER,
                        self.__ln
                        ))
                    self.__ln += 1
                
                elif self.__nextch() == '*':   #注释块
                    #指针移动到注释块尾部(不包括 '/')
                    self.__movchr(2)
                    mov, lni = skip_comment_block(self.__source, self.__chp)
 
                    if mov == -1:
                        error_msg(-1, 'EOL while scanning comment block', self.__filename)
 
                    self.__movchr(mov)  #移动指针至注释块尾部+1的位置
                    self.__ln += lni  #加上行号增量
 
                elif self.__nextch == '=':
                    self.__stream.append(Token(
                        '/=',
                        LAP_INP_DIV,
                        self.__ln
                    ))
                    self.__movchr(2)
 
                else:   #单纯除法
                    self.__stream.append(Token(
                        '/',
                        LAP_DIV,
                        self.__ln
                    ))
                    self.__movchr()
 
            elif c in ('(', ')', '[', ']', '{', '}', 
                       ',', '.', ';', '$', '@', '#', '\\',':'):
                if c in ('(', '[', '{'):
                    self.__blevel += 1
                elif c in (')', ']', '}'):
                    self.__blevel -= 1 if self.__blevel > 0 else 0
                if c == '\\' and self.__nextch(1) == '\n':
                    self.__movchr(2)
                else:
                    self.__stream.append(Token(
                        c, 
                        {
                            '(':LAP_SLBASKET, 
                            ')':LAP_SRBASKET, 
                            '[':LAP_MLBASKET, 
                            ']':LAP_MRBASKET, 
                            '{':LAP_LLBASKET, 
                            '}':LAP_LRBASKET,
                            ',':LAP_COMMA, 
                            '.':LAP_DOT, 
                            ';':LAP_SEMI, 
                            '$':LAP_MONEY, 
                            '@':LAP_AT,
                            '#':LAP_WELL,
                            '\\':LAP_ESCAPE,
                            ':':LAP_COLON
                        }[c],
                        self.__ln
                    ))
                    self.__movchr()
            
            elif c == '!':  #感叹号
                if self.__nextch() == '=':  #!=
                    self.__stream.append(Token(
                        '!=',
                        LAP_UEQ,
                        self.__ln
                    ))
                    self.__movchr(2)
                
                else:  # NOT
                    self.__stream.append(Token(
                        '!',
                        LAP_NOT,
                        self.__ln
                    ))
                    self.__movchr()
 
            elif c.isspace() or ord(c) in [x for x in range(32) if x not in (10, 13)] or ord(c) == 127:
                #忽略空白符
                self.__movchr()
 
            elif c.isalpha() or c == '_':
                #如果是标识符
                mov, buf = get_identifier(self.__source, self.__chp)
                self.__stream.append(Token(
                    buf,
                    LAP_IDENTIFIER,
                    self.__ln
                ))
                self.__movchr(mov)
 
            elif c.isnumeric():
                #如果是数字，先用一个字符串存起来，以后再分析
                mov, buf = get_number(self.__source, self.__chp)
                if mov == -1:
                    error_msg(self.__ln, 'SyntaxError', self.__filename)

                self.__stream.append(Token(
                    buf,
                    LAP_NUMBER,
                    self.__ln
                ))
                self.__movchr(mov)
 
            elif c == '=':  #等于号
                if self.__nextch() == '=':  #等于
                    self.__stream.append(Token(
                        '==',
                        LAP_EQ,
                        self.__ln
                    ))
                    self.__movchr(2)
 
                else:       #赋值
                    self.__stream.append(Token(
                        '=',
                        LAP_ASSI,
                        self.__ln
                    ))
                    self.__movchr()
 
            elif c in ('"', '\''):
                #如果是字符串
                mov, lni, buf = get_string(self.__source, self.__chp)
 
                if mov == -1:
                    error_msg(self.__ln, 'EOL while scanning string literal', self.__filename)
                
                self.__stream.append(Token(
                    buf,
                    LAP_STRING,
                    self.__ln
                ))
 
                self.__ln += lni
                self.__movchr(mov)
 
                
            else:
                error_msg(self.__ln, 'Unknown character', self.__filename)
 
        if self.__nextch(-1) != '\\n':
            self.__stream.append(Token(
                '\n',
                LAP_ENTER,
                self.__ln
            ))  #加回车是有利于语法分析行的检测
 
        self.__stream.append(Token(
                '<EOF>',
                LAP_EOF,
                self.__ln
            ))  #加回车是有利于语法分析行的检测
 
        return self.__stream


if __name__ == '__main__':
    import pprint

    ts = Lex('tests/test.ail').lex()

    pprint.pprint(ts.token_list)
