from os import getcwd
from os.path import realpath, dirname, join


__all__ = [
    'AIL_DIR_PATH', 'LIB_PATH', 'CORE_PATH', 'BUILTINS_MODULE_PATH', 'CURRENT_WORK_PATH'
]


AIL_DIR_PATH = dirname(__file__)

CURRENT_WORK_PATH = '.'
LIB_PATH = join(AIL_DIR_PATH, 'lib')
CORE_PATH = join(AIL_DIR_PATH, 'core')
BUILTINS_MODULE_PATH = join(AIL_DIR_PATH, 'modules')

REMOVE_PY_RUNTIME_TRACEBACK = True

