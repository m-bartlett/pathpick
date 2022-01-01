#!/usr/bin/env python
import argparse, sys, os
from .interactive_path_selector import InteractivePathSelector
from .config import read_user_config_file

def printerr(*args, **kwargs):
  kwargs['file'] = sys.stderr
  print(*args, **kwargs)


def main():
  parser = argparse.ArgumentParser()

  parser.add_argument(
    "root", type=str, nargs='?', default=None,
    help="Directory to explore. Default is $PWD"
  )

  parser.add_argument(
    "--show-hidden", '-a', action="store_true",
    help="Show files and directories that start with '.'"
  )

  parser.add_argument(                          # TODO: implement
    "--relative", '-r', action="store_true",
    help="Instead of absolute paths, format output as relative paths from the current working directory"
  )

  parser.add_argument(
    "--dirs-first", '-d', action="store_true",
    help="List directories at the top of the page instead of sorted with file names"
  )

  parser.add_argument(
    "--json", '-j', action="store_true",
    help="Return output as JSON string hiearchy instead of a newline-separated list of paths"
  )

  parser.add_argument(                          # TODO: implement
    "--load-json", '-J', type=str, default=None, metavar="<JSON FILE OR STRING>",
    help=f"""
      Load JSON selection (possibly the output of a previous session with --json) as the initial selection in an interactive session, as opposed to nothing selected initially.
      This option used with --json is intended to serve as a selection caching feature, so the user can preserve a filesystem selection to reuse later or serve as a template for common selections.
      If this option is used in conjunction with piping selection output in through STDIN, the data read from STDIN and the data read via this argument will be unioned. E.g.
    """
  )

  parser.add_argument(
    "--ascii", action="store_true",
    help="Use plain ASCII characters instead of unicode characters for symbols indicating selection states in an interactive session"
  )

  parser.add_argument(
    "--verbose", "-v", action="store_true",
    help="print extra information during process execution for debugging"
  )

  parser.add_argument(
    "--version", action="store_true",
    help="print version and exit"
  )

  parser.add_argument(
    "--config", type=str,
    help="path to style configuration file"
  )

  args = parser.parse_args()

  user_config_file, config = read_user_config_file()

  if not os.isatty(sys.stdin.fileno()):
    user_stdin = sys.stdin.read().strip()

  if args.verbose:
    if user_stdin:
      printerr(f"Data from stdin:\n{user_stdin}\n")
    if user_config_file is None:
      message = "Loaded default config"
    else:
      message = f"Loaded config from {user_config_file}"
    printerr(message)
    printerr(config)

  selection_output = ''
  with InteractivePathSelector( root = args.root,
                                show_hidden = args.show_hidden,
                                dirs_first  = args.dirs_first,
                                styles      = config['style']  ) as fsp:
    fsp.draw_page()

    try:
      while fsp.read_key(): continue
    except KeyboardInterrupt:
      sys.exit(1)

    if args.json:
      import json
      selection_output = json.dumps(fsp.get_selection_json(), separators=(',', ':'))
    else:
      selection_output = '\n'.join(fsp.get_selection_paths())

  print(selection_output)


if __name__ == '__main__':
  main()