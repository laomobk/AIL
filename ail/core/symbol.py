
from dataclasses import dataclass
from typing import List, Dict


@dataclass
class Symbol:
    name: str


class SymbolTable:
    def __init__(self):
        self.scopes: List[Dict[str, Symbol]] = []

    def new_scope(self) -> int:
        """
        :return: scope index
        """
        self.scopes.append({})
        return len(self.scopes) - 1

    def has_symbol(self, name: str, scope_index: int):
        return name in self.scopes[scope_index]
