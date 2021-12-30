import os
from setuptools import setup, find_packages
package_name = os.path.basename(os.path.dirname(__file__))
package_name_importable = package_name.replace('-','_')

setup(
    name     = package_name,
    version  = os.getenv('VERSION', '0.0.1'),
    url      = 'https://github.com/m-bartlett/pathpick.git',
    author   = 'M B',
    license  = '',
    packages = [ package_name_importable + package.partition('src')[2]
                 for package in find_packages() ],
    package_dir = {package_name_importable: 'src'},
    package_data = {'': ['*.ini']},
    include_package_data=True,    # include everything in source control
    exclude_package_data={"": ["README.txt"]},
    entry_points={
        'console_scripts': [
            f'{package_name}={package_name}.__main__:main',
        ],
    },
)