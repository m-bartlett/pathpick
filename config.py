# TO-DO: cache suffix/prefix length within config object, use for length calculations
# TO-DO: "compile" ansi style formattable string within config object


import configparser
from types   import SimpleNamespace
from os      import getenv
from pathlib import Path


class DefaultNamespace(SimpleNamespace):
  def __init__(self, default=None, **kwargs):
    super().__init__(**kwargs)
    self.default = default

  def __getattr__(self, key):
    try:    return super().__getattr__(self, key)
    except: return self.default

  @classmethod
  def from_dict(_class, dictionary):  # recursively cast nested dict(s) to namespace(s)
    for k, v in dictionary.items():
      if isinstance(v, dict):
        dictionary[k] = _class.from_dict(v)
    return _class(**dictionary)



EXECUTABLE_DIRECTORY = Path(__file__).resolve(strict=True).parent
EXECUTABLE_NAME = EXECUTABLE_DIRECTORY.name

config_parser = configparser.ConfigParser()

home = Path.home()
if (XDG_CONFIG_HOME := getenv('XDG_CONFIG_HOME', False)):
  config_home = Path(XDG_CONFIG_HOME).expanduser()
else:
  config_home = home / '.config'
config_home /= EXECUTABLE_NAME

default_config_path = EXECUTABLE_DIRECTORY / 'style.ini'

user_config_file_paths = [
  config_home/'style.ini',
  home / f'.{EXECUTABLE_NAME}',
  home / f'.{EXECUTABLE_NAME}/style.ini',
]


def read_config_file(config_file_path: Path):
  _config = {}
  config_parser.read(config_file_path.resolve())
  for section in config_parser.sections():

    _section = {}
    for option, value in config_parser[section].items():
      option = option.replace('-','_')
      for cast in [int, float]:
        try:
          value = cast(value)
          break
        except ValueError:
          continue
      _section[option] = value

    _config[section] = _section

  return _config


def read_user_config_file():
  user_config_file = default_config_path
  _config = read_config_file(default_config_path)

  for config_file_path in user_config_file_paths:
    if config_file_path.exists():
      user_config_file = config_file_path
      _config |= read_config_file(user_config_file)

  return (user_config_file, DefaultNamespace.from_dict(_config))
