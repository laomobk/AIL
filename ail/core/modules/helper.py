from ail.core.aobjects import (
    AILObject, compare_type
)

from ail.core.error import AILRuntimeError

from ail.objects.struct import STRUCT_OBJ_TYPE, STRUCT_TYPE
from ail.objects.module import MODULE_TYPE


class _AILHelper:
    def __init__(self):
        pass

    def list_methods(self, obj: AILObject) -> dict:
        props = obj['__class__']
        if props is None:
            return dict()

        return props.methods

    def list_meta(self, obj: AILObject) -> dict:
        props = obj['__class__']
        if props is None:
            return dict()
        return props.required


_DEFAULT_HELPER = _AILHelper()


def print_help(x: AILObject = None):
    if compare_type(x, STRUCT_TYPE):
        print('[name]')
        print('  %s' % x['__name__'])

        print('[functions]')
        for m in x['__bind_functions__']:
            print('  %s' % m)
 
        print('[protected]')
        for m in x.protected:
            if not m.startswith('_'):
                print('  %s' % m)

        print('[member]')
        for m in x.members.keys():
            if not m.startswith('_'):
                print('  %s' % m)

    elif compare_type(x, STRUCT_OBJ_TYPE):
        if x['__type__'] is not None:
            print('[type]')
            print('  %s' % x['__type__']['__name__'])

        print('[name]')
        print('  %s' % x['__name__'])

        print('[protected]')
        for m in x.protected:
            if not m.startswith('_'):
                print('  %s' % m)

        print('[member]')
        for m in x.members.keys():
            if not m.startswith('_'):
                print('  %s' % m)

    elif compare_type(x, MODULE_TYPE):
        print('[type]')
        print('  module')

        print('[name]')
        print('  %s' % x['__name__'])

        print('[path]')
        print('  %s' % x['__path__'])
        
        print('[namespace]')
        for m in x['__namespace__'].keys():
            if not m.startswith('_'):
                print('  %s' % m)

    elif isinstance(x, AILObject):
        methods = _DEFAULT_HELPER.list_methods(x)
        meta = _DEFAULT_HELPER.list_meta(x)

        print('[type]')
        print('  %s  (AIL Built-in type)' % x['__class__'].name)
        
        if methods:
            print('[methods]')
            for m in methods.keys():
                print('  %s' % m)
        
        if meta:
            print('[meta]')
            for m in meta.keys():
                print('  %s' % m)
    else:
        print('no help info provided.')


_IS_AIL_MODULE_ = True
_AIL_NAMESPACE_ = {'help': print_help}

