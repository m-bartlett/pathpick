#!/usr/bin/env python
from interactive_terminal_application import *
import pathlib


@singleton
class InteractiveFilesystemPathSelector(InteractiveTerminalApplication):
  HEIGHT_1 = 0
  FILE_PREFIX = '  '

  selection = {}
  subselection = selection
  path_list = []
  path_list_last = 0
  index = 0

  @staticmethod
  def _glob2paths_with_hidden(glob):
    return [
      ( p.name + '/' if p.is_dir() else p.name )
      for p in glob
    ]

  @classmethod
  def _glob2paths_no_hidden(cls, glob):
    return [
      p for p in cls._glob2paths_with_hidden(glob)
      if not p.startswith('.')
    ]

  @staticmethod
  def _sort_path_list(glob):
    return sorted(glob)

  @staticmethod
  def _sort_path_list_directories_first(glob):
      dirs = [i for i in glob if i.endswith('/')]
      files = [i for i in glob if not i.endswith('/')]
      return sorted(dirs) + sorted(files)


  def __init__( self,
                root       = None,
                absolute   = False,
                hidden     = False,
                dirs_first = False  ):
    super().__init__()

    if root and root != '.':

      root = pathlib.Path(root).expanduser()
      if not root.exists(): raise FileNotFoundError(f"Path '{root}' does not exist")
      if not root.is_dir(): raise NotADirectoryError(f"Path '{root}' is not a directory")
    else:
      root = pathlib.Path().absolute() # defaults to process $PWD

    if absolute:
      root = root.absolute()

    if hidden:
      self.glob2paths = self._glob2paths_with_hidden
    else:
      self.glob2paths = self._glob2paths_no_hidden

    if dirs_first:
      self.sort_path_list = self._sort_path_list_directories_first
    else:
      self.sort_path_list = self._sort_path_list

    self.index = 0
    self.root = root
    self.cwd = root
    self.ls()

    self.character_action_map = {
      ord("Q"):  lambda e: self.end(return_code=1, throw=True),
      ord("q"):  lambda e: self.end(return_code=1, throw=True),
      ord(" "):  lambda e: self.toggle_selected(),
      ord("\t"): lambda e: self.toggle_selected(),
      27:        lambda e: self.control_character_action_map[e](), # escape character \e
      ord('\n')  lambda e: True, # enter key
    }

    self.control_character_action_map = {
      # ord("M"): lambda: puts("mouse"),
      # ord("I"): lambda: puts("focus"),
      # ord("O"): lambda: puts("unfocus"),
      ord("A"): self.cursor_up,          # up
      ord("B"): self.cursor_down,        # down
      ord("5"): self.page_up,            # PageUp
      ord("6"): self.page_down,          # PageDown
      ord("C"): self.select_or_descend,  # right
      ord("D"): self.ascend,             # left

      # TO-DO ctrl-A is select-all in current dir

      ord(' '): lambda: self.end(return_code=1, throw=True)  # escape
    }


  def resize(self, *args):
    self.WIDTH, self.HEIGHT = os.get_terminal_size()
    self.HEIGHT_1 = self.HEIGHT - 1
    self.draw_page()


  def read_key(self):
    char, escape, event  = os.read(self.fd, 3).ljust(3)
    try:
      return self.character_action_map[char](event)
    except KeyError:
      return False


  def draw_header(self, page, pages, page_start, page_end, row):
    header = f"  -  {page+1}/{pages+1} ({self.index*100//max(1,self.path_list_last)}%)"
    path_width = self.WIDTH - len(header)
    path = str(self.cwd)
    if len(path) > path_width:
      path = '...' + path[-(path_width-3):]
    self.puts(f"\033[37;1m{path}{header}\033[0m")


  def constrain_width(self, s):
    return s[:self.WIDTH-3]+'...' if len(s) > self.WIDTH else s


  def draw_page(self):
    self.puts(
      "\033[0;0H" # Move cursor to position 0,0 (top left)
      "\033[2J"   # Clear entire screen
    )
    page, row = divmod(self.index, self.HEIGHT_1)
    pages = self.path_list_len // self.HEIGHT_1
    row += 2
    page_start = page * self.HEIGHT_1
    page_end = page_start + self.HEIGHT_1
    self.draw_header(page, pages, page_start, page_end, row)
    for p in self.path_list[page_start:page_end]:
      self.puts('\n')
      if self.subselection.get(p, False):
        item = f" \033[36m*{p}\033[0m"
      else:
        item = self.FILE_PREFIX+p
      item = self.constrain_width(item)
      self.puts(item)
      # TO-DO highlight selection items
      # \033[1m
    self.puts(f"\033[{row};0H>")
    sys.stdout.flush()


  def cursor_up(self):
    self.index -= 1
    if self.index < 0:
      self.index = self.path_list_last
    self.draw_page()


  def cursor_down(self):
    self.index += 1
    if self.index > self.path_list_last:
      self.index = 0
    self.draw_page()


  def page_up(self):
    self.index -= self.HEIGHT_1
    self.index = max(self.index, 0)
    self.draw_page()


  def page_down(self):
    self.index += self.HEIGHT_1
    self.index = min(self.index, self.path_list_last)
    self.draw_page()


  def toggle_selected(self):
    path = self.path_list[self.index]
    self.subselection[path] = not self.subselection.get(path, False)


  def ls(self):
    self.path_list = self.sort_path_list(  self.glob2paths( self.cwd.glob('*') )  )
    self.path_list_len = len(self.path_list)
    self.path_list_last = max(self.path_list_len - 1, 0)


  def ascend(self):
    cwd = self.cwd.parent
    if str(cwd).startswith(str(self.root)):
      pwd = self.cwd.name + '/'
      self.cwd = cwd
      self.ls()
      self.index = self.path_list.index(pwd)
      self.draw_page()


  def descend(self):
    path = self.path_list[self.index]
    self.cwd /= path
    self.ls()
    self.index = 0
    self.draw_page()


  def select_or_descend(self):
    path = self.path_list[self.index]
    if path.endswith('/'): self.descend()
    else: self.toggle_selected()




if __name__ == "__main__":

  import argparse
  parser = argparse.ArgumentParser()
  parser.add_argument("root", type=str, nargs='?', default=None, help="Directory to explore. Default is $PWD")
  parser.add_argument("--hidden", '-a', action="store_true", help="Show files and directories that start with '.'")
  parser.add_argument("--absolute", '-b', action="store_true", help="Use absolute paths for selection display and output")
  parser.add_argument("--dirs-first", '-d', action="store_true", help="")
  args = parser.parse_args()

  with InteractiveFilesystemPathSelector( root         = args.root,
                                          absolute     = args.absolute,
                                          hidden       = args.hidden,
                                          dirs_first = args.dirs_first ) as fsp:
    fsp.draw_page()
    while not fsp.read_key():
      try:
        ...
      except KeyboardInterrupt:
        break
    fsp.end(throw=False)

    print(fsp.selection)
    print(fsp.subselection)

