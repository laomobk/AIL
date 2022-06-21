
from unittest import TestCase
from ail.core.acompile import CodeObjectBuffer


class TestLnoTab(TestCase):
    def test(self):
        buf = CodeObjectBuffer()
        buf.add_bytecode(1, 0, 1)
        buf.add_bytecode(1, 0, 1)
        buf.add_bytecode(1, 0, 1)
        buf.add_bytecode(1, 0, 1)
        buf.add_bytecode(1, 0, 1)

        buf.add_bytecode(1, 0, 3)
        buf.add_bytecode(1, 0, 3)
        buf.add_bytecode(1, 0, 3)
        buf.add_bytecode(1, 0, 3)

        buf.add_bytecode(1, 0, 4)
        buf.add_bytecode(1, 0, 4)

        self.assertListEqual(buf.lnotab, [10, 2, 8, 1])
