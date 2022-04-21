from os.path import exists
from time import time

from setuptools import setup, find_packages
from ail.core.version import AIL_MAIN_VERSION, AIL_SUB_VERSION


_WELCOME_BANNER = \
'''******************************
**                          **
** AIL Programming Language **
**     Powered by Python    **
**                          **
******************************
'''


print(_WELCOME_BANNER)


INSTALL_TIME_PATH = './ail/core/INSTALL_TIME'

try:
    with open(INSTALL_TIME_PATH, 'w') as f:
        install_time = time()
        print('[INFO] Install time: %s' % install_time)
        f.write(str(int(install_time * 1000)))
except:
    pass


def try_write_commit_id():
    try:
        import subprocess

        if not (exists('AIL_REPO_ROOT') and exists('.git')):
            return
        commit_id = subprocess.Popen(
                ['git rev-parse --short HEAD'], 
                shell=True, stdout=subprocess.PIPE)  \
                        .communicate()[0].decode().replace('\n', '')
        branch_name = subprocess.Popen(
                ['git symbolic-ref --short -q HEAD'], 
                shell=True, stdout=subprocess.PIPE)  \
                        .communicate()[0].decode().replace('\n', '')
        print('[INFO] commit id = %s/%s' % (branch_name, commit_id))
        open('./ail/COMMIT_ID', 'w').write('%s/%s' % (branch_name, commit_id))
    except Exception:
        print('[W]: failed to get commit id')


try_write_commit_id()

setup(
    name='ail',
    packages=find_packages(),
    version='%s.%s' % (AIL_MAIN_VERSION,
                       '.'.join([str(sv) for sv in AIL_SUB_VERSION])),

    entry_points={
        'console_scripts': [
            'ail = ail.__main__:main_as_entry_point',
        ]
    },

    package_data={
        'ail': ['lib/*.ail', 'core/INSTALL_TIME', 'COMMIT_ID']
    }
)
