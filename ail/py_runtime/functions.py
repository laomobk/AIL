from . import exceptions as _exceptions


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
