#!/usr/bin/env python
from interactive_filesystem_path_selector import *
import argparse, json

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

parser.add_argument(                          # TODO: implement
  "--json", '-j', action="store_true",
  help="Return output as JSON string hiearchy instead of a newline-separated list of paths"
)


parser.add_argument(                          # TODO: implement
  "--load-json", '-J', type=str, default=None, metavar="<JSON FILE OR STRING>",
  help="""
    Load JSON selection (the output of a session with --json) as the active selection in an interactive session.
    This option used with --json is intended to serve as a selection caching feature, so the user can preserve a filesystem selection to reuse later or serve as a template for common selections.
  """
)


parser.add_argument(
  "--ascii", action="store_true",
  help="Use plain ASCII characters instead of unicode characters for symbols indicating selection states in an interactive session"
)

args = parser.parse_args()

selection_output = ''

with InteractiveFilesystemPathSelector( root        = args.root,
                                        show_hidden = args.show_hidden,
                                        dirs_first  = args.dirs_first  ) as fsp:
  if args.ascii:
    fsp.ACTIVE_ROW_INDICATOR = '> '
    fsp.UNSELECTED_PREFIX    = ' '
    fsp.SELECTED_PREFIX      = '+ '
    fsp.PARTIAL_PREFIX       = '~ '

  fsp.draw_page()
  
  try:
    while fsp.read_key():
      ...
  except KeyboardInterrupt:
    sys.exit(1)
      
  if args.json:
    selection_output = json.dumps(fsp.selection) # TO-DO JSON-output only output True leaves
  else:
    selection_output = '\n'.join(fsp.get_selection_paths())


print(selection_output)