import os, glob
from setuptools import setup, find_packages
package_name = os.path.basename(os.path.dirname(__file__))
package_name_importable = package_name.replace('-','_')
with open(glob.glob('README*')[0]) as f:
    long_description = f.read()

setup(
    author               = 'M B',
    description          = "interactive filesystem path selector TUI",
    entry_points         = {'console_scripts': [f'{package_name}={package_name}.__main__:main']},
    include_package_data = True,    # include everything in source control
    license              = 'GPLv3',
    long_description     = long_description,
    name                 = package_name,
    package_data         = { '': ['*.ini'] },
    package_dir          = { package_name_importable: 'src' },
    packages             = [ package_name_importable + package.partition('src')[2]
                             for package in find_packages() ],
    url                  = 'https://github.com/m-bartlett/pathpick.git',
    version              = os.getenv('PATHPICK_VERSION', '0.0.1'),
)