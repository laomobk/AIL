
from ail.core import symbol, aparser, alex


from unittest import TestCase


SOURCE_1 = '''
x.y[3] = 1
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


class TestSymbol(TestCase):
    def __get_table(self, source: str):
        ts = alex.Lex().lex(source)
        tree = aparser.Parser().parse(ts, source, '<string>')
        analyzer = symbol.SymbolAnalyzer()
        return analyzer.visit_and_make_symbol_table(
                source, '<string>', tree)

    def _test_global_assign(self):
        tab = self.__get_table(SOURCE_1)
        print(tab.symbols)

    def _test_param(self):
        tab = self.__get_table(SOURCE_2)
        print(tab.symbols)

    def test_local(self):
        tab = self.__get_table(SOURCE_3)
        print(tab.symbols)
        print(tab.symbols[0].namespace.symbols[2].namespace)

