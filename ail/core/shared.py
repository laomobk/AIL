
from typing import List as _List


# this file is for share the data between AIL RT 
# and AIL core


class _ShardData:
    find_path: list = None
    max_recursion_depth: int = None
    cwd: str = None
    base_dir: str = None
    ail_path: str = None
    boot_dir: str = None
    file_dir: str = None
    prog_argv: _List[str] = list()


GLOBAL_SHARED_DATA = _ShardData()

