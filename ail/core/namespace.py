

def fill_namespace(
        ns: dict, name: str = '__main__', main: bool = True, not_copy: bool = False):
    if not_copy:
        ns = ns.copy()

    ns['__name__'] = name
    ns['__main__'] = main

    if not_copy:
        return ns