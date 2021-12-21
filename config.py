from configparser import ConfigParser
from types        import SimpleNamespace
from os           import getenv
from pathlib      import Path

EXECUTABLE_DIRECTORY = Path(__file__).resolve(strict=True).parent
EXECUTABLE_NAME = EXECUTABLE_DIRECTORY.name
CONFIG_FILE_NAME = 'config.ini'

home = Path.home()
if (XDG_CONFIG_HOME := getenv('XDG_CONFIG_HOME', False)):
  config_home = Path(XDG_CONFIG_HOME).expanduser()
else:
  config_home = home / '.config'
config_home /= EXECUTABLE_NAME

user_config_file_paths = [
  config_home/CONFIG_FILE_NAME,
  home / f'.{EXECUTABLE_NAME}',
  home / f'.{EXECUTABLE_NAME}/{CONFIG_FILE_NAME}',
]

config_parser = ConfigParser()

default_config_path = EXECUTABLE_DIRECTORY / CONFIG_FILE_NAME


def try_type_cast(config_section, option):
  for cast in [ config_section.getint,
                config_section.getfloat,
                config_section.getboolean ]:
    try:  return cast(option)
    except ValueError:  continue
  return config_section.get(option).strip("'").strip('"')


def read_config_file(config_file_path: Path):
  config_parser.read(config_file_path.resolve())
  return {  section : { option.replace('-','_') : try_type_cast( config_parser[section],
                                                                 option )
                        for option, value in config_parser[section].items() }
            for section in config_parser.sections() }


def read_user_config_file():
  for config_file_path in user_config_file_paths:
    if config_file_path.exists(): break
  else: config_file_path = default_config_path
  return (config_file_path, read_config_file(config_file_path))