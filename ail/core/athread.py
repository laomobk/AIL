from random import randint

from threading import Thread, Lock
from typing import Dict, List

from .aconfig import _BYTE_CODE_SIZE
from .aframe import Frame
from .aobjects import get_state

from .avmsig import VMInterrupt, MII_DO_JUMP


class ThreadState:
    """
    the AIL Thread State
    """
    def __init__(self,
                 frame_stack: List[Frame], py_thread: Thread, lock: Lock = None):
        self.frame_stack = frame_stack
        self.op_counter: int = -_BYTE_CODE_SIZE
        self.py_thread = py_thread
        self.lock = Lock() if lock is None else lock

    def release_lock(self):
        if self.lock.locked():
            self.lock.release()

    def __repr__(self):
        return '<Thread State of %s>' % repr(self.py_thread)

    @property
    def thread_id(self):
        return self.py_thread.native_id


class ThreadScheduler:
    def __init__(self):
        self.__threads: Dict[int, ThreadState] = dict()
        self.now_running_thread = None  # type: ThreadState

        self.__counter = 0
        self.__main_op_counter = 0

    @property
    def __now_running_op_counter(self) -> int:
        if self.now_running_thread is None:
            return get_state().global_interpreter.op_counter
        return self.now_running_thread.op_counter

    @__now_running_op_counter.setter
    def __now_running_op_counter(self, value: int):
        if self.now_running_thread is None:
            self.__main_op_counter = value
        else:
            self.now_running_thread.op_counter = value

    def add_thread(self, t_state: ThreadState) -> int:
        self.__threads[self.__counter] = t_state
        c = self.__counter
        self.__counter += 1
        return c

    def del_thread(self, t_count: int):
        del self.__threads[t_count]

    def __select_a_thread(self) -> ThreadState:
        return self.__threads[randint(0, len(self.__threads.keys()) - 1)]

    def schedule(self):
        m_state = get_state()
        now_counter = m_state.global_interpreter.op_counter
        self.__now_running_op_counter = now_counter
        self.now_running_thread.lock.acquire()

        winner = self.__select_a_thread()
        winner.release_lock()

        m_state.global_interpreter.op_counter = \
            winner.op_counter + _BYTE_CODE_SIZE  # next opcode

        m_state.frame_stack = winner.frame_stack

        self.now_running_thread = winner

        raise VMInterrupt(MII_DO_JUMP)


THREAD_SCHEDULER = ThreadScheduler()