from typing import List

from . import agc


class InterpreterState:
    def __init__(self):
        self.frame_stack: list = []
        self.gc: agc.GC = None

        self.handling_err_stack = []
        self.err_stack = []

        self.global_interpreter = None

        self.prog_argv: List[str] = list()


MAIN_INTERPRETER_STATE = InterpreterState()
