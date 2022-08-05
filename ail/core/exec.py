
from ail.core.namespace import fill_namespace


class Executer:
    def exec(self, source: str, filename: str,
             globals_: dict = None, locals_ : dict = None):
        """
        :return: code: 0 -> ok | 1 -> exception occurred | 2 -> system exit
        """

        l = Lex()
        ts = l.lex(source, filename)

        p = Parser()
        node = p.parse(ts, source, filename, True)

        converter = ASTConverter()
        code = compile(converter.convert_module(node), filename, 'exec')

        name = '__main__'

        if not main:
            name = filename

        fill_namespace(globals, name, main, filename=filename)

        exec(code, globals)
        return 0
