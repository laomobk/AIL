from . import agc


class InterpreterState:
    def __init__(self):
        self.frame_stack :list = []
        self.gc : agc.GC = None

        self.handling_err_stack = []
        self.err_stack = []
        self.global_interpreters = []  # global interpreter reference


MAIN_INTERPRETER_STATE = InterpreterState()
