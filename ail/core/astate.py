from typing import List

from .atraceback import Traceback
from . import agc


class InterpreterState:
    def __init__(self):
        self.frame_stack: list = []
        self.gc: agc.GC = None

        self.handling_err_stack = []
        self.err_stack = []
        self._trackback_stack: List[Traceback] = []

        self.global_interpreters = []  # global interpreter reference

        self.prog_argv: List[str] = list()
    
    def add_traceback(self, tb: Traceback):
        self._trackback_stack.append(tb)

    def add_traceback_by_frame(self, frame):
        self.add_traceback(Traceback(frame))

    def get_traceback(self, tb: Traceback):
        return self._trackback_stack.pop() if self._trackback_stack else None


MAIN_INTERPRETER_STATE = InterpreterState()
