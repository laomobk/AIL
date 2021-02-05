from ail.core.aobjects import (
    AILObject, compare_type, unpack_ailobj
)

from ail.core.error import AILRuntimeError

from ail.objects.class_object import CLASS_TYPE, OBJECT_TYPE
from ail.objects.function import FUNCTION_TYPE, PY_FUNCTION_TYPE
from ail.objects.module import MODULE_TYPE
from ail.objects.struct import STRUCT_OBJ_TYPE, STRUCT_TYPE


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
        if unpack_ailobj(x['__type__']) is not None:
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

    elif compare_type(x, CLASS_TYPE):
        print('[name]')
        print('  %s' % x['__name__'])

        print('[bases]')
        print('  %s' % x['__bases__'])

        print('[mro]')
        print('  %s' % x['__mro__'])
        
        class_dict = x['__dict__']
        class_var = []
        class_methods = []
        doc_string = x['__doc__']

        for k, v in class_dict.items():
            if compare_type(v, PY_FUNCTION_TYPE, FUNCTION_TYPE):
                if k[:1] == '_' and not k[:2] == k[-2:] == '__':
                    class_methods.append(k)
            else:
                class_var.append(k)

        if class_var:
            print('[class var]')
            print('\n  '.join(class_var))

        if class_methods:
            print('[methods]')
            print('\n  '.join(class_methods))

        if doc_string:
            print('\n[doc]')
            print(doc_string)

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

    elif compare_type(x, FUNCTION_TYPE):
        print('[signature]')
        print('  %s' % x['__signature__'])

        doc_string = x['__doc__']
        if doc_string:
            print('\n[doc]')
            print(doc_string)

    elif compare_type(x, PY_FUNCTION_TYPE):
        doc_string = x['__doc__']
        if doc_string:
            print('\n[doc]')
            print(doc_string)

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

