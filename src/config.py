from configparser import ConfigParser
from pathlib      import Path
from importlib.resources import read_text
import os
import re

default_config = {
  'default': { 'ascii':       True,
               'dirs_first':  False,
               'json':        False,
               'relative':    False,
               'show_hidden': False,
               'verbose':     False },
 'style': { 'active':          {'bold': True, 'prefix': '> ', 'reset': False},
            'inactive':        {'prefix': ' '},
            'unselected':      {'prefix': ''},
            'selected':        {'bold': True, 'foreground': 4, 'prefix': '+'},
            'nested_selected': {'bold': True, 'foreground': 6, 'prefix': '~'},
            'truncated':       {'prefix': '...', 'suffix': '...'},
            'header':          {'reverse': True},
            'file':            {},
            'directory':       {'foreground': 3, 'suffix': '/'},
            'symlink':         {'suffix': '@'},
            'blockdevice':     {},
            'chardevice':      {},
            'fifo':            {'suffix': '|'},
            'socket':          {'suffix': '='} }
}

package_directory = Path(__file__).resolve().parent
package_name = __name__.partition('.')[0]
config_file_name = 'config.ini'
default_config_path = package_directory / config_file_name
home = Path.home()
config_parser = ConfigParser()
nested_option_regex = re.compile(r'[.:/]')

if (xdg_config_home := os.getenv('XDG_CONFIG_HOME', False)):
  config_home = Path(xdg_config_home).expanduser()
else:
  config_home = home / '.config'
config_home /= package_name

user_config_file_paths = [
  home / f'.{package_name}/{config_file_name}',
  home / f'.{package_name}',
  config_home/config_file_name,
  default_config_path,
]


def _get_typed(section, option):
  for cast in [ section.getint, section.getfloat, section.getboolean ]:
    try:
      return cast(option)
    except ValueError:
      continue
  option = section.get(option).strip("'").strip('"').split('\n')
  if len(option) > 1:
    return [o for o in option if o != ""]
  else:
    return option[0]


def _read_config():
  config = {}
  for section_name in config_parser.sections():
    section = config_parser[section_name]
    _config = {
      option.replace('-','_'): _get_typed(section,option)
      for option in section.keys()
    }

    subsections = nested_option_regex.split(section_name)
    nested = config
    for sub in subsections[:-1]:
      nested[sub] = nested.get(sub, {})
      nested = nested[sub]
    nested[subsections[-1]] = _config

  return config


def read_user_config_file(extra_config_file_path=None):
  config_path_iter = map(str, [extra_config_file_path] + user_config_file_paths)
  config_file_path = config_parser.read(config_path_iter)
  if config_file_path:                                                     # module exists as directory
    return (config_file_path[0], _read_config())
  elif (default_config_text := read_text(package_name, config_file_name)): # module is a zipapp
    config_parser.read_string(default_config_text)
    return (default_config_path, _read_config())
  else:                                                                    # failsafe
      return (None, default_config)


__all__ = [
  read_user_config_file,
  package_directory,
  package_name,
  default_config_path,
  user_config_file_paths,
  default_config
]