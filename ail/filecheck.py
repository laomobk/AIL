from os.path import (
    isfile, exists
)


class CheckResult(bool):
    def __init__(self, ok: bool, message: str = ''):
        self.ok = ok
        self.message = message

        super().__init__(ok)


class FileNotFound(CheckResult):
    pass


class IsNotFile(CheckResult):
    pass


class InvalidEncoding(CheckResult):
    pass


def check_is_file(filename: str) -> bool:
    return CheckResult(isfile(filename))


def check_exists(filename: str) -> bool:
    return CheckResult(exists(filename))


def check_encode(filename: str) -> bool:
    try:
        open(filename, 'r', encoding='UTF-8').close()
        return CheckResult
    except UnicodeDecodeError:
        return False
