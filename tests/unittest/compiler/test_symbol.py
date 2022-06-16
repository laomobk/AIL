
from ail.core import symbol, aparser, alex


from unittest import TestCase


SOURCE = '''
x.b = 1
'''


class TestSymbol(TestCase):
    def test(self):
        ts = alex.Lex().lex(SOURCE)
        tree = aparser.Parser().parse(ts, SOURCE, '<string>')
        analyzer = symbol.SymbolAnalyzer()
        tab = analyzer.visit_and_make_symbol_table(
                SOURCE, '<string>', tree)

        print(tab.symbols)

