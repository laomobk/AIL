from os.path import exists
from time import time

from setuptools import setup, find_packages
from ail.core.version import AIL_MAIN_VERSION, AIL_SUB_VERSION


INSTALL_TIME_PATH = './ail/core/INSTALL_TIME'

try:
    with open(INSTALL_TIME_PATH, 'w') as f:
        install_time = time()
        print('[INFO] Install time: %s' % install_time)
        f.write(str(int(install_time * 1000)))
except:
    pass


setup(
    name='ail',
    packages=find_packages(),
    version='%s.%s' % (AIL_MAIN_VERSION,
                       '.'.join([str(sv) for sv in AIL_SUB_VERSION])),

    entry_points={
        'console_scripts': [
            'ail = ail.__main__:main',
        ]
    },

    package_data={
        'ail': ['lib/*.ail', 'core/INSTALL_TIME']
    }
)