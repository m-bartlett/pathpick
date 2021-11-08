#!/usr/bin/env python
from interactive_filesystem_path_selector import *
import argparse, json

parser = argparse.ArgumentParser()

parser.add_argument(
  "root", type=str, nargs='?', default=None,
  help="Directory to explore. Default is $PWD"
)

parser.add_argument(
  "--hidden", '-a', action="store_true",
  help="Show files and directories that start with '.'"
)

parser.add_argument(
  "--absolute", '-b', action="store_true",
  help="Use absolute paths for selection display and output"
)

parser.add_argument(
  "--dirs-first", '-d', action="store_true",
  help="List directories at the top of the page instead of sorted with file names"
)

parser.add_argument(
  "--json", '-j', action="store_true",
  help="Output as JSON string hiearchy instead of list of paths"
)

args = parser.parse_args()

selected_paths = []
with InteractiveFilesystemPathSelector( root       = args.root,
                                        absolute   = args.absolute,
                                        hidden     = args.hidden,
                                        dirs_first = args.dirs_first ) as fsp:
  fsp.draw_page()
  try:
    while not fsp.read_key():
      ...
  except KeyboardInterrupt:
    sys.exit(0)
      
  fsp.end(throw=False)

  selected_paths = fsp.get_selection_paths()


for path in selected_paths:
  print(path)