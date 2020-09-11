
from setuptools import setup, find_packages


setup(
    name='ail',
    packages=find_packages(),

    entry_points={
        'console_scripts': [
            'ail = ail.__main__:main',
        ]
    }
)

