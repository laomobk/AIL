from sys import argv

from .ail_main import launch_main


# entry point
def main():
    launch_main(argv[1:])


if __name__ == '__main__':
    launch_main(argv[1:])
