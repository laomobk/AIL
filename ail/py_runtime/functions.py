
from typing import List

from .objects import AILImporter as _AILImporter

from . import exceptions as _exceptions


_IMPORTER = _AILImporter()


def ail_input(prompt: str, value_count: int):
    m = input(prompt)
    if value_count == 1:
        return m
    if value_count == 0:
        return None

    vals = m.split(maxsplit=value_count)
    if len(vals) < value_count:
        raise _exceptions.AILInputException('')

    return vals


def ail_import(
        mode: int, name: str, namespace: dict, alias: str=None, members: List[str]=[]):
    if alias is None:
        alias = name
    return _IMPORTER.import_module(mode, name, namespace, alias, members)

