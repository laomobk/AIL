
from unittest import TestCase

from ail.core import symbol, aparser, alex


S_CLS = '''
class C {
  import '__os';
  __value = 0;
  func __get_info(self) {
    return 0;
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

    def test_class_def(self):
        tab = self.__get_table(S_CLS)
        print(tab.symbols[0].namespace.symbols)
