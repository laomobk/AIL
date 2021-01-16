from sys import argv, exit

from .ail_main import launch_main


# entry point
def main():
    exit(launch_main(argv[1:]))


if __name__ == '__main__':
    exit(launch_main(argv[1:]))
