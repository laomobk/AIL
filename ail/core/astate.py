from typing import List

from .anamespace import Namespace
from .aframe import Frame


class NamespaceState:
    def __init__(self, ns_global: Namespace, ns_builtins: Namespace = None):
        self.ns_global = ns_global
        self.ns_builtins = ns_builtins


class InterpreterState:
    __slots__ = (
        'frame_stack', 'gc', 'handling_err_stack',
        'err_stack', 'global_interpreter', 'prog_argv',
        'namespace_state'
    )

    def __init__(self):
        self.frame_stack: List[Frame] = []

        self.handling_err_stack = []
        self.err_stack = []

        self.global_interpreter = None

        self.prog_argv: List[str] = list()
        self.namespace_state: NamespaceState = NamespaceState(
                Namespace('global', dict()), Namespace('builtins', dict()))


MAIN_INTERPRETER_STATE = InterpreterState()
