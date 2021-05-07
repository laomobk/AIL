# python compatible


def test_run():
    from .alex import Lex
    from .aparser import ASTConverter, Parser

    source = open('./tests/test.ail').read()
    l = Lex()
    ts = l.lex(source)

    p = Parser()
    t = p.parse(ts, source, '<test>')

    converter = ASTConverter()
    code = compile(converter.convert_module(t), './tests/test.ail', 'exec')
    exec(code)


if __name__ == '__main__':
    test_run()

