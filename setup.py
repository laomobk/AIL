from setuptools import setup, find_packages
from ail.core.version import AIL_MAIN_VERSION, AIL_SUB_VERSION

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
        'ail': ['lib/*.ail']
    }
)
