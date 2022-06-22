
from unittest import TestCase

from ail.core import symbol, aparser, alex


S_CELL = '''
func f() {
    x = 1
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

    def test_cellvars(self):
        tab = self.__get_table(S_CELL)
        print(tab.store_symbols[0].namespace.cellvars)