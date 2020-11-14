
from typing import Union

from ..core import aobjects as obj

from .struct import STRUCT_TYPE


class FastNumber(obj.AILObject):
    def __init__(self, pynum: Union[int, float]):
        super().__init__(
            __str__=self.__str,
            __repr__=self.__str,
            __class__=STRUCT_TYPE
        )

        self._value = pynum

    def __str(self, *_) -> str:
        return '%s' % self._value

