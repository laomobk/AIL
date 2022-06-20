
from unittest import TestCase

from ail.core.acompiler import CodeObjectBuffer
from ail.core.pyopcode import EXTENDED_ARG


class TestExtendedArg(TestCase):
    def test(self):
        buf = CodeObjectBuffer()
        buf.add_bytecode(7, 280, 0)
        self.assertListEqual(buf.code, [EXTENDED_ARG, 280 >> 8, 7, 280 & 0xff])
