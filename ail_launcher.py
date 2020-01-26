# AIL Launcher

from importlib import import_module


def launch_py_test(test_name):
    try:
        mod = import_module('obj_test.%s' % test_name)
        if hasattr(mod, 'test'):
            mod.test()
        else:
            print('Test module do not have \'test\' function!')
    except ModuleNotFoundError:
        print('No test named \'%s\'' % test_name)


if __name__ == '__main__':
    launch_py_test('test_object_system')
