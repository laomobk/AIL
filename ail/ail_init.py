
from .core.astate import MAIN_INTERPRETER_STATE

_ail_inited = False


def ail_init_interpreter():
    from .core.avm import Interpreter

    MAIN_INTERPRETER_STATE.global_interpreter = Interpreter()
