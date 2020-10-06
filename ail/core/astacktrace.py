from typing import List

from .aframe import Frame


class StackTrace:
    __slots__ = ('frame_stack', 'lineno', 'filename', 'name')

    def __init__(self, frame_stack: List[Frame], lineno, filename, name):
        self.frame_stack = frame_stack
        self.lineno = lineno
        self.filename = filename

