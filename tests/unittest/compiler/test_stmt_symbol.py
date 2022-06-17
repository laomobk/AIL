
from ail.core import symbol, aparser, alex

from unittest import TestCase


S_WITH = '''
func m() {
  f = 1
  func inf() {
    with f = x {}
  }
}
'''

S_IF = '''
if x {}
'''

S_IMPORT = '''
import 'os'
import 'a/b'
'''


class TestSymbol(TestCase):
    def __get_table(self, source: str):
        ts = alex.Lex().lex(source)
        tree = aparser.Parser().parse(ts, source, '<string>')
        analyzer = symbol.SymbolAnalyzer()
        return analyzer.visit_and_make_symbol_table(
                source, '<string>', tree)

    def _test_with(self):
        tab = self.__get_table(S_WITH)
        print(tab.symbols[0].namespace.symbols[1].namespace.symbols)

    def _test_if(self):
        tab = self.__get_table(S_IF)
        print(tab.symbols)

    def test_import(self):
        tab = self.__get_table(S_IMPORT)
        print(tab.symbols)
