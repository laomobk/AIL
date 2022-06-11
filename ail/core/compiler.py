
from dataclasses import dataclass


@dataclass
class CompilerState:
    ctrl_stack = []
    real_time_stack_size = 0


class GenericPyCodeCompiler:
    pass
