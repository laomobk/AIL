
from unittest import TestCase

from ail.core import symbol, aparser, alex


SOURCE_1 = '''
*(x.a), b = 1
'''

SOURCE_2 = '''
x(1, 2, a, b)
'''

SOURCE_3 = '''
func f(a) {
    x = 1;
    func inf() {
        return x;
    }
}
'''

SOURCE_FREE = '''
f = func (){
    x = 1;
    func inf() {
        a = x;
        return x;
    }
}
'''

SOURCE_BIN = '''
b = 1
func f() {
    c = 1
    d = 1
    a = b + c * d
}
'''

SOURCE_CALL = '''
a.b.c[x](e)
'''

SOURCE_LAMBDA = '''
f = (x) -> x
'''

SOURCE_PARAM = '''
func f(a, b, *c) {}
'''


class TestSymbol(TestCase):
    def __get_table(self, source: str):
        ts = alex.Lex().lex(source)
        tree = aparser.Parser().parse(ts, source, '<string>')
        analyzer = symbol.SymbolAnalyzer()
        return analyzer.visit_and_make_symbol_table(
                source, '<string>', tree)

    def test_global_assign(self):
        tab = self.__get_table(SOURCE_1)
        print(tab.symbols)

    def _test_arg(self):
        tab = self.__get_table(SOURCE_2)
        print(tab.symbols)

    def test_local(self):
        tab = self.__get_table(SOURCE_3)
        print(tab.symbols)
        print(tab.symbols[0].namespace.symbols[2].namespace.symbols)

    def _test_free(self):
        tab = self.__get_table(SOURCE_FREE)
        print(tab.symbols)
        print(tab.symbols[0].namespace.symbols[1].namespace.symbols)

    def _test_binary_expr(self):
        tab = self.__get_table(SOURCE_BIN)
        print(tab.symbols)
        print(tab.symbols[1].namespace.symbols)

    def _test_call(self):
        tab = self.__get_table(SOURCE_CALL)
        print(tab.symbols)

    def _test_lambda(self):
        tab = self.__get_table(SOURCE_LAMBDA)
        print(tab.symbols)

    def _test_lambda(self):
        tab = self.__get_table(SOURCE_PARAM)
        print(tab.symbols[0].namespace.symbols)
