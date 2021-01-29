# 用于ail的词法分析器

from string import hexdigits, octdigits

from .tokentype import *
from .error import error_msg

__author__ = 'LaomoBK'

ALEX_VERSION_NUM = (0, 1)  # 数字版本号
ALEX_VERSION_EXTRA = 'Beta'  # 额外版本信息
ALEX_VERSION_DATE = (10, 27, 2019)

__all__ = ['Token', 'TokenStream', 'Lex']

_hex_num_chars = ('0123456789ABCDEFabcdef', 16)
_ord_num_chars_with_sci = ('0123456789.eE', 10)
_ord_num_chars = ('0123456789', 10)
_oct_num_chars = ('01234567', 8)
_bin_num_chars = ('01', 2)
_sci_num_chars = ('0123456789+-', 12)


def get_source_char(source: str, index: int) -> str:
    if 0 <= index < len(source):
        return source[index]
    return ''


def skip_comment_line(source: str, cursor: int):
    """
    source : 源码文件
    cursor : 源码字符指针
    返回指针右移增量
    """
    cur = 0  # 增量
    ccur = cursor  # 原始字符指针
    while ccur < len(source):
        if source[ccur] == '\n':
            break
        cur += 1
        ccur += 1
    return cur + 1  # 跳过回车


def skip_comment_block(source: str, cursor: int, ) -> tuple:
    """
    source : 源码文件
    cursor : 源码字符指针
    返回一个元祖
 
    字符指针错误值原因：
    -1 : 注释块不完整
 
    ( 字符指针右移增量 , 行号增量)
    """

    ccur = cursor
    cur = 0  # 指针右移增量
    lni = 0  # 行号增量

    try:
        while True:
            if source[ccur] == '\n':
                lni += 1

            if source[ccur] == '*' and source[ccur + 1] == '/':
                cur += 2  # 跨过 '/'

                return cur, lni  # ( 字符指针右移增量 , 行号增量)
            ccur += 1
            cur += 1

    except IndexError:
        # 一般是到文件尾部了 */ 没有 /
        return -1, 0


def get_identifier(source: str, cursor: int) -> tuple:
    """
    source : 源码文件
    cursor : 源码字符指针
    
    返回一个元祖
    ( 字符指针增量 , 标识符内容)
    """

    buffer = ''  # 标识符内容缓冲区
    ccur = cursor  # 原始字符指针
    cur = 0  # 字符指针增量

    while ccur < len(source):

        if not (source[ccur].isnumeric() or \
                source[ccur] == '_' or \
                source[ccur].isalpha()):
            break

        buffer += source[ccur]

        ccur += 1
        cur += 1

    return cur, buffer


def get_number(source: str, cursor: int) -> tuple:
    """
    :return: when 'char offset' = -1, that means it was a invalid number.
    :returns: (char offset, string value of this number)
    """
    buffer = ''
    char_cur = cursor

    num_chars, base = _ord_num_chars_with_sci

    if cursor >= len(source):
        return -1, None

    if source[char_cur] == '0':  # special
        char_cur += 1
        now_char = get_source_char(source, char_cur)

        num_chars, base = {
            'x': _hex_num_chars,
            'X': _hex_num_chars,
            'o': _oct_num_chars,
            'O': _oct_num_chars,
            'b': _bin_num_chars,
            'B': _bin_num_chars,
            'e': _sci_num_chars,
            'E': _sci_num_chars,
            '.': (num_chars[:-1], 10),  # like ord, but no '.'
        }.get(now_char, (0, -1))

        if base == -1:
            return 1, '0'  # just '0'
        elif base != 12:
            char_cur += 1
            buffer += '0' + now_char

        if base == 12:
            num_chars = _ord_num_chars_with_sci[0]
            base = 10
            char_cur -= 1  # back to 0
        else:
            now_char = get_source_char(source, char_cur)
            if now_char not in num_chars or now_char == '':
                return -1, None

    while char_cur < len(source):
        ch = get_source_char(source, char_cur)

        if ch not in num_chars:
            break

        if ch == '.' and '.' in num_chars and base == 10:
            num_chars = _ord_num_chars[0] + 'Ee'  # drop '.'

        elif (ch == 'e' or ch == 'E') and \
             ('e' in num_chars or 'E' in num_chars) and \
             base == 10:

            num_chars = _ord_num_chars[0]

            now_char = get_source_char(source, char_cur + 1)

            if now_char == '+' or now_char == '-':
                buffer += 'e' + now_char
                char_cur += 2
                continue

            elif now_char not in num_chars or now_char == '':
                return -1, None

        elif ch in ('+', '-') and \
             ('+' in num_chars or '-' in num_chars) and \
             base == 10:
            
            num_chars = _ord_num_chars[0]

        buffer += ch
        char_cur += 1

    return char_cur - cursor, buffer


def get_number_old(source: str, cursor: int) -> tuple:
    """
    source : 源码文件
    cursor : 源码字符指针

    指针错误值原因：
    -1 不正确的数字 （如7.2.6, 1x7x9）
    
    返回一个元祖
    ( 字符指针增量 , 数字字符串)
    """
    buffer = ''  # 数字字符串内容缓冲区
    ccur = cursor  # 原始字符指针
    cur = 0  # 字符指针增量

    seen_d = False
    seen_hex = False

    e_char = 'xXABCDEFabcdef.'
    e_char2 = 'ABCDEFabcdef'

    while ccur < len(source):
        if not (source[ccur].isnumeric() or source[ccur] in e_char):
            break

        if source[ccur] == '.':
            if seen_d or seen_hex:
                return -1, 0
            seen_d = True
            pass

        if source[ccur] in ('x', 'X'):
            if seen_hex:
                return -1, 0

            if len(buffer) != 1 or source[ccur - 1] != '0':
                return -1, 0

            seen_hex = True

        buffer += source[ccur]
        cur += 1
        ccur += 1

    if not (buffer[-1].isnumeric() or buffer[-1] in e_char2):
        return -1, 0

    return cur, buffer


def parse_complex_escape_character(
        start_char: str, source: str, index: int) -> tuple:
    """
    :return: real_char:
             -1: invalid escape character
    :returns: (real_char, offset)
    """
    ofs = 0
    if start_char == 'x':  # type  \x...
        hex_buf = ''
        for inc in range(2):
            next_char = get_source_char(source, index + 1 + inc)
            if next_char not in hexdigits:
                return -1, 0
            hex_buf += next_char
        return chr(int(hex_buf, 16)), 4

    elif start_char == '0':  # type \0...
        if get_source_char(source, index+1) not in octdigits:
            return '\0', 2

        oct_buf = ''
        for inc in range(3):
            next_char = get_source_char(source, index + inc)
            if next_char not in octdigits:
                return -1, 0
            oct_buf += next_char
        return chr(int(oct_buf, 8)), 4


def get_string(source: str, cursor: int) -> tuple:
    """
    source : 源码文件
    cursor : 源码字符指针
 
    Lap支持多行字符串
 
    字符指针错误值原因：
    -1: 字符串没有结束就到达EOF
    -2: 字符串中出现无法解析的转义字符
    
    返回一个元祖
    ( 字符指针增量, 行号增量 , 数字字符串)
    """
    buffer = ''  # 字符串内容缓冲区
    ccur = cursor  # 原始字符指针，跳过引号
    cur = 0  # 字符指针增量
    lni = 0  # 行号增量

    instr = False
    hasEND = False

    schr = ''  # 开始字符串的引号

    slen = len(source)

    tcur = 0

    while ccur < len(source):
        if instr and source[ccur] == '\\' and slen > ccur + 1 \
                and source[ccur + 1] in (
                'a', 'b', 'f', 'n', 'r', 't', 'v', '0', 'x', '\'', '"', '\\'):
            # escape character
            target = {
                'a': '\a',
                'b': '\b',
                'f': '\f',
                'n': '\n',
                'r': '\r',
                't': '\t',
                'v': '\v',
                '0': '0',
                'x': 'x',
                '\'': '\'',
                '"': '"',
                '\\': '\\'
            }.get(source[ccur + 1])

            if target in ('0', 'x'):
                char, offset = parse_complex_escape_character(target, source, ccur+1)
                if char == -1:
                    return -2, 0, 0
                ccur += offset
                cur += offset
                buffer += char
            else:
                buffer += target

                ccur += 2
                cur += 2

        if instr and source[ccur] == schr:
            hasEND = True  # 是否是因为while的条件而退出
            break

        if source[ccur] == '\n':
            lni += 1

        if instr:
            buffer += source[ccur]

        cur += 1
        ccur += 1

        if not instr:
            schr = source[ccur - 1]
            instr = True

    if not hasEND:  # 如果字符串没有结束就到达EOF
        return -1, 0, 0

    return cur + 1, lni, buffer  # 跳过最后一个引号


class Cursor:  # 字符指针类型
    """
    指向源码中的字符的指针
    """

    def __init__(self, value=0):
        self.value = value


class Token:
    def __init__(self, value: str, ttype: int, ln: int):
        self.value = value
        self.ttype = ttype
        self.ln = ln

    def __repr__(self):
        return '<Token \'{0}\'  Type:{1}  LineNumber:{2}>'.format(
            self.value,
            self.ttype,
            self.ln
        )

    def __eq__(self, obj: object):
        if isinstance(obj, str):
            return self.value == obj and self.ttype != AIL_STRING
        elif isinstance(obj, Token):
            return self.value == obj.value
        else:
            return super().__eq__(obj)

    def __ne__(self, obj: object):
        if isinstance(obj, str):
            return self.value != obj and self.ttype != AIL_STRING
        elif isinstance(obj, Token):
            return self.value != obj.value
        else:
            return super().__ne__(obj)

    __str__ = __repr__


class TokenStream:
    """
    单词流
    """

    def __init__(self):
        self.__tli = []

    def __iter__(self):
        return iter(self.__tli)

    def append(self, tok: Token):
        """
        将 tok 增加到尾部
        """

        self.__tli.append(tok)

    def __repr__(self):
        return repr(self.__tli)

    __str__ = __repr__

    def __getitem__(self, index):
        if isinstance(index, slice):
            return self.__tli[index]

        return self.__tli[index] \
            if len(self.__tli) > index \
            else self.__tli[-1]  # EOF

    def __len__(self):
        return len(self.__tli)

    @property
    def token_list(self):
        return self.__tli


class Lex:
    def __init__(self):
        """
        fp : 源码路径，当以'.$str:'开头且testmode=True时，则是分析.$str:以后的内容
        """

        self.__filename = '<NO FILE>'
        self.__ln = 1  # 行号
        
        self.__source = '\n'
        # 源码文件

        self.__cursor = Cursor()  # 源码的字符指针
        self.__stream = TokenStream()

        self.__blevel = 0

    def __get_source(self, filename: str) -> str:
        try:
            return open(filename, encoding='utf-8').read()
        except (UnicodeDecodeError, OSError) as e:
            return self.__error_msg(str(e))

    @property
    def __chp(self):
        """
        指向源码字符的指针
        """
        return self.__cursor.value

    @__chp.setter
    def __chp(self, v):
        self.__cursor.value = v

    def __movchr(self, step=1):
        """
        移动字符指针
        """

        self.__cursor.value += step

    @property
    def __chnow(self):
        """
        此时此刻的字符
        越界则报语法错误
        """

        return self.__source[self.__cursor.value] \
            if self.__cursor.value < len(self.__source) \
            else self.__error_msg('Syntax error')

    def __nextch(self, ni=1):
        """
        返回__source[self.__cursor.value + ni]
        如果越界，则报语法错误
        """
        return self.__source[self.__cursor.value + ni] \
            if self.__cursor.value + ni < len(self.__source) \
            else '<EOF>'

    def __error_msg(self, msg):
        error_msg(self.__ln, msg, self.__filename)

    def lex(self, source: str, filename: str = '<string>') -> TokenStream:
        if filename is not None:
            self.__filename = filename
            self.__source = source

            self.__cursor = Cursor()  # 源码的字符指针
            self.__stream = TokenStream()
            self.__ln = 1  # 行号

            self.__blevel = 0

        if len(self.__source) == 0:
            return self.__stream

        while self.__chp < len(self.__source):
            c = self.__chnow

            if ord(c) == 10:
                self.__ln += 1
                self.__movchr(1)

                if self.__blevel == 0:
                    self.__stream.append(Token(
                        '\n',
                        AIL_ENTER,
                        self.__ln
                    ))

            elif c in ('+', '*', '^', '%', '|', '&', '-'):  # 除法有点特殊
                if self.__nextch() == '=':  # 原地运算
                    self.__stream.append(Token(c + '=',
                                               {
                                                   '+': AIL_INP_PLUS,
                                                   '*': AIL_INP_MUIT,
                                                   '%': AIL_INP_MOD,
                                                   '^': AIL_INP_XOR,
                                                   '-': AIL_INP_SUB
                                               }[c],  # 根据c得到单词类型
                                               self.__ln))
                    self.__movchr(2)

                elif self.__nextch() in ('+', '-'):  # 自增自减
                    self.__stream.append(Token(c + c,
                                               AIL_PLUS_PLUS if self.__nextch() == '+' else AIL_SUB_SUB,
                                               self.__ln))
                    self.__movchr(2)

                elif c == '|' and self.__nextch() == '|':  # ||
                    self.__stream.append(Token(
                        '||',
                        AIL_OR,
                        self.__ln
                    ))
                    self.__movchr(2)

                elif c == '&' and self.__nextch() == '&':  # &&
                    self.__stream.append(Token(
                        '&&',
                        AIL_AND,
                        self.__ln
                    ))
                    self.__movchr(2)

                else:
                    self.__stream.append(Token(c,
                                               {
                                                   '+': AIL_PLUS,
                                                   '*': AIL_MUIT,
                                                   '%': AIL_MOD,
                                                   '^': AIL_XOR,
                                                   '|': AIL_BIN_OR,
                                                   '&': AIL_BIN_AND,
                                                   '-': AIL_SUB
                                               }[c],
                                               self.__ln))
                    self.__movchr(1)

            elif c in ('>', '<'):
                if self.__nextch() in ('>', '<'):  # 左位移，右位移
                    if self.__nextch(2) == '=':  # <<=, >>=
                        if c + self.__nextch() not in ('<<', '>>'):
                            self.__error_msg(
                                      'Syntax error:{0}'.format(
                                          c + self.__nextch() + self.__nextch(2)),)

                        self.__stream.append(Token(c + c + '=',
                                                   {
                                                       '>>': AIL_INP_RSHIFT,
                                                       '<<': AIL_INP_LSHIFT
                                                   }.get(c + self.__nextch()),
                                                   self.__ln
                                                   ))

                        self.__movchr(3)

                    else:  # 普通左右位移和参数类型
                        if c + self.__nextch() not in ('<<', '>>'):
                            if c + self.__nextch() == '<>':  # 空参数列表
                                self.__stream.append(Token(
                                    '<',
                                    AIL_SMALER,
                                    self.__ln
                                ))

                                self.__stream.append(Token(
                                    '>',
                                    AIL_LARGER,
                                    self.__ln
                                ))

                                self.__movchr(2)
                                continue  # 跳过

                            self.__error_msg(
                                      'Syntax error:{0}'.format(c + self.__nextch()))

                        self.__stream.append(Token(
                            c + self.__nextch(),
                            {
                                '>>': AIL_RSHIFT,
                                '<<': AIL_LSHIFT
                            }[c + self.__nextch()],
                            self.__ln
                        ))
                        self.__movchr(2)

                elif self.__nextch() == '=':  # >=, <=
                    self.__stream.append(Token(
                        c + '=',
                        AIL_LARGER_EQ if c == '>' else AIL_SMALER_EQ,
                        self.__ln
                    ))
                    self.__movchr(2)

                else:  # >, <
                    self.__stream.append(Token(
                        c,
                        AIL_LARGER if c == '>' else AIL_SMALER,
                        self.__ln
                    ))
                    self.__movchr()

            elif c == '/':  # 斜杠
                if self.__nextch() == '/':  # 单行注释
                    # 移动指针至下一行或EOF
                    self.__movchr(skip_comment_line(self.__source, self.__chp))
                    self.__stream.append(Token(
                        '\n',
                        AIL_ENTER,
                        self.__ln
                    ))
                    self.__ln += 1

                elif self.__nextch() == '*':  # 注释块
                    # 指针移动到注释块尾部(不包括 '/')
                    self.__movchr(2)
                    mov, lni = skip_comment_block(self.__source, self.__chp)

                    if mov == -1:
                        self.__error_msg('EOL while scanning comment block')

                    self.__movchr(mov)  # 移动指针至注释块尾部+1的位置
                    self.__ln += lni  # 加上行号增量

                elif self.__nextch == '=':
                    self.__stream.append(Token(
                        '/=',
                        AIL_INP_DIV,
                        self.__ln
                    ))
                    self.__movchr(2)

                else:  # 单纯除法
                    self.__stream.append(Token(
                        '/',
                        AIL_DIV,
                        self.__ln
                    ))
                    self.__movchr()

            elif c in ('(', ')', '[', ']', '{', '}',
                       ',', '.', ';', '$', '@', '#', '\\', ':', '~'):
                if c in ('(', '['):
                    self.__blevel += 1
                elif c in (')', ']'):
                    self.__blevel -= 1 if self.__blevel > 0 else 0
                if c == '\\' and self.__nextch(1) == '\n':
                    self.__movchr(2)
                    self.__ln += 1
                else:
                    self.__stream.append(Token(
                        c,
                        {
                            '(': AIL_SLBASKET,
                            ')': AIL_SRBASKET,
                            '[': AIL_MLBASKET,
                            ']': AIL_MRBASKET,
                            '{': AIL_LLBASKET,
                            '}': AIL_LRBASKET,
                            ',': AIL_COMMA,
                            '.': AIL_DOT,
                            ';': AIL_SEMI,
                            '$': AIL_MONEY,
                            '@': AIL_AT,
                            '#': AIL_WELL,
                            '\\': AIL_ESCAPE,
                            ':': AIL_COLON,
                            '~': AIL_WAVE,
                        }[c],
                        self.__ln
                    ))
                    self.__movchr()

            elif c == '!':  # 感叹号
                if self.__nextch() == '=':  # !=
                    self.__stream.append(Token(
                        '!=',
                        AIL_UEQ,
                        self.__ln
                    ))
                    self.__movchr(2)

                else:  # NOT
                    self.__stream.append(Token(
                        '!',
                        AIL_NOT,
                        self.__ln
                    ))
                    self.__movchr()

            elif c.isspace() or ord(c) in [
                    x for x in range(32) if x not in (10, 13)] or ord(c) == 127:

                # 忽略空白符
                self.__movchr()

            elif c.isalpha() or c == '_':
                # 如果是标识符
                mov, buf = get_identifier(self.__source, self.__chp)
                self.__stream.append(Token(
                    buf,
                    AIL_IDENTIFIER,
                    self.__ln
                ))
                self.__movchr(mov)

            elif c.isnumeric():
                # 如果是数字，先用一个字符串存起来，以后再分析
                mov, buf = get_number(self.__source, self.__chp)
                if mov == -1:
                    self.__error_msg('SyntaxError')

                self.__stream.append(Token(
                    buf,
                    AIL_NUMBER,
                    self.__ln
                ))
                self.__movchr(mov)

            elif c == '=':  # 等于号
                if self.__nextch() == '=':  # 等于
                    self.__stream.append(Token(
                        '==',
                        AIL_EQ,
                        self.__ln
                    ))
                    self.__movchr(2)

                else:  # 赋值
                    self.__stream.append(Token(
                        '=',
                        AIL_ASSI,
                        self.__ln
                    ))
                    self.__movchr()

            elif c in ('"', '\''):
                # 如果是字符串
                mov, lni, buf = get_string(self.__source, self.__chp)

                if mov == -1:
                    self.__error_msg('EOL while scanning string literal')
                elif mov == -2:
                    self.__error_msg('Cannot decode an escape character')

                self.__stream.append(Token(
                    buf,
                    AIL_STRING,
                    self.__ln
                ))

                self.__ln += lni
                self.__movchr(mov)

            elif c == '\\':
                if self.__nextch() == '\n':
                    self.__ln += 1
                    self.__movchr(2)

            else:
                self.__error_msg('Unknown character')

        if self.__nextch(-1) != '\\n':
            self.__stream.append(Token(
                '\n',
                AIL_ENTER,
                self.__ln
            ))  # 加回车是有利于语法分析行的检测

        self.__stream.append(Token(
            '<EOF>',
            AIL_EOF,
            self.__ln
        ))  # 加回车是有利于语法分析行的检测

        return self.__stream


def test_lex():
    import pprint

    ts = Lex().lex(open('./tests/test.ail').read())

    pprint.pprint(ts.token_list)


if __name__ == '__main__':
    test_lex()
