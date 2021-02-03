
from typing import List

from ..core.aobjects import (
    AILObject, call_object,
)

from ..core.aframe import Frame


def class_init(self, 
        name: str, meta: AILObject, bases: List[AILObject], dict_: dict):
    self['__name__'] = name
    self['__meta__'] = meta
    self['__base__'] = bases
    self['__dict__'] = dict_


def build_class(class_func, class_name, meta, bases) -> AILObject:
    func_frame = Frame()
    if not call_object(class_func, frame=func_frame):
        return None

    class_dict = func_frame.variable

