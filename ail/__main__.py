from sys import argv, exit

from . import _config

from .ail_main import launch_main


# entry point
def main_as_entry_point():
    # print('[run from entry point]')
    _config.RUN_FROM_ENTRY_POINT = True
    exit(launch_main(argv[1:]))


def main():
    exit(launch_main(argv[1:]))


if __name__ == '__main__':
    exit(launch_main(argv[1:]))

