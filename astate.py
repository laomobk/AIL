import aobjects as objs
import agc
import threading


class InterpreterState:
    def __init__(self):
        self.now_codeobj :objs.AILCodeObject = None
        self.frame_stack :list = []
        self.gc :agc.GC = None

        self.gc_thread :threading.Thread = None
        self.main_thread :threading.Thread = None
        self.thread_pool :list = []
