from json import dumps

from os.path import split

from .core.alex import Lex
from .core.aparser import Parser
from .core.test_utils import make_ast_tree


def parse_main(argv):
    if not argv:
        return 1

    filename, *_ = argv

    source = open(filename, encoding='UTF-8').read()

    ts = Lex().lex(source, filename)
    tree = Parser().parse(ts, source, filename)
    
    print(dumps(make_ast_tree(tree)))

    return 0


if __name__ == '__main__':
    import sys

    sys.exit(parse_main(sys.argv[1:]))

