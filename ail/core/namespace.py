

def fill_namespace(
        ns: dict, name: str = '__main__', main: bool = True, not_copy: bool = False,
        filename=None):
    if not_copy:
        ns = ns.copy()

    ns['__name__'] = name
    ns['__main__'] = main

    if isinstance(filename, str):
        ns['__file__'] = filename

    if not_copy:
        return ns
