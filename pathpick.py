#!/usr/bin/env python
from interactive_terminal_application import *
import pathlib

from time import sleep


@singleton
class InteractiveFilesystemPathSelector(InteractiveTerminalApplication):
  HEIGHT_1 = 1
  UNSELECTED_FILE_PREFIX = ' '
  SELECTED_FILE_PREFIX = '+'
  CHILDREN_SELECTED_DIRECTORY_PREFIX = '-'
  ACTIVE_ROW_INDICATOR = '>'

  selection = {}
  subselection = selection
  path_list = []
  path_list_last = 0
  index = 0
  page = 0
  row = 0
  pages = 1
  page_start = 0
  page_end = 0
  page1 = 1
  pages1 = 1

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
      27:        lambda e: self.escape_control_character_action_map[e](), # escaped '['
      10:        lambda e: True, # enter key
    }

    self.escape_control_character_action_map = {
      # ord("M"): lambda: puts("mouse"),
      # ord("I"): lambda: puts("focus"),
      # ord("O"): lambda: puts("unfocus"),
      ord("A"): self.row_up,          # up
      ord("B"): self.row_down,        # down
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


  def constrain_width(self, s):
    return s[:self.WIDTH-3]+'...' if len(s) > self.WIDTH else s
    
    
  def update_pagination(self):
    self.page, self.row = divmod(self.index, self.HEIGHT_1)
    self.page_start = self.index - self.row
    # self.page_start = self.page * self.HEIGHT_1
    self.row += 2
    self.pages = self.path_list_len // self.HEIGHT_1
    self.page_end = min(self.page_start + self.HEIGHT_1, self.path_list_len)
    self.page1 = self.page + 1
    self.pages1 = self.pages + 1


  def draw_header(self):
    header = f"   {self.page1}/{self.pages1} ({self.index*100//max(1,self.path_list_len)}%)"
    path_width = self.WIDTH - len(header)
    path = str(self.cwd)
    if len(path) > path_width:  path = '...' + path[-(path_width-3):]
    gap = ' ' * (path_width - len(path))
    self.save_cursor_xy()
    self.cursor_home()
    self.clear_line()
    self.puts(self.color(f"{path}{gap}{header}", bold=True, fg=7, bg=0))
    self.restore_cursor_xy()


  def draw_row(self, index=None):
    if index is None:  index = self.index
    item = self.path_list[index]
    selection_symbol = self.SELECTED_FILE_PREFIX
    if item.endswith('/'):
      selected = self.subselection.get(item[:-1], {})
      selected = True in selected.values()
      selection_symbol = self.CHILDREN_SELECTED_DIRECTORY_PREFIX
    else:
      selected = self.subselection.get(item, False)
    item = self.constrain_width('  ' + item)
    self.clear_line()
    if selected:
      item = f' {selection_symbol}{item[2:]}'
      item = self.color(item, fg=6)
    else:
      item = f' {self.UNSELECTED_FILE_PREFIX}{item[2:]}'
    self.puts(item)


  def draw_cursor(self, row=None):
    if row is None:
      row =(self.index % self.HEIGHT_1) + 2
    self.cursor_xy(0,row)
    self.puts(self.ACTIVE_ROW_INDICATOR)
    self.cursor_x(0)
      

  def draw_page(self):
    self.cursor_home()
    self.clear_screen()
    self.draw_header()
    self.cursor_home()
    for i in range(self.page_start, self.page_end):
      self.puts('\n')
      self.draw_row(i)
    self.draw_cursor(self.row)


  def row_up(self):
    self.index -= 1
    if self.index < self.page_start:
      if self.index < 0:
        self.index = self.path_list_last
      self.update_pagination()
      self.draw_page()
    else:
      self.puts(' ')
      self.draw_header()
      self.draw_cursor()


  def row_down(self):
    self.index += 1
    if self.index >= self.page_end:
      if self.index > self.path_list_last:
        self.index = 0
      self.update_pagination()
      self.draw_page()
    else:
      self.puts(' ')
      self.draw_header()
      self.draw_cursor()


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
    if path.endswith('/'): path = path[:-1]
    self.subselection[path] = not self.subselection.get(path, False)
    self.draw_row()
    self.cursor_x(0)
    self.puts(self.ACTIVE_ROW_INDICATOR)
    self.cursor_x(0)


  def ls(self):
    self.path_list = self.sort_path_list(  self.glob2paths( self.cwd.glob('*') )  )
    self.path_list_len = max(len(self.path_list), 0)
    self.path_list_last = max(self.path_list_len - 1, 0)
    self.update_pagination()


  def ascend(self):
    cwd = self.cwd.parent
    cwd_str = str(cwd)
    
    if cwd_str.startswith(str(self.root)):
      key_hierarchy = cwd_str.partition(str(self.root))[2].split('/')[1:]
      subselection = self.selection
      for key in key_hierarchy:   # recurse from root to nesting n-1 to go up 1
        subselection = subselection[key]  
      self.subselection = subselection
      pwd = self.cwd.name + '/'
      self.cwd = cwd
      self.ls()
      self.index = self.path_list.index(pwd)
      self.draw_page()


  def descend(self):
    path = self.path_list[self.index]
    key  = path[:-1] # strip trailing /
    self.cwd /= path
    self.ls()
    self.index = 0
    subselection = self.subselection.get(key, None)
    if type(subselection) is not dict:
      self.subselection[key] = {}
      subselection = self.subselection[key]
    self.subselection = subselection
    self.draw_page()


  def select_or_descend(self):
    path = self.path_list[self.index]
    if path.endswith('/'): self.descend()
    else: self.toggle_selected()
    
    
  def get_selection(self):
    ...




if __name__ == "__main__":

  import argparse, json
  parser = argparse.ArgumentParser()
  parser.add_argument("root", type=str, nargs='?', default=None, help="Directory to explore. Default is $PWD")
  parser.add_argument("--hidden", '-a', action="store_true", help="Show files and directories that start with '.'")
  parser.add_argument("--absolute", '-b', action="store_true", help="Use absolute paths for selection display and output")
  parser.add_argument("--dirs-first", '-d', action="store_true", help="")
  parser.add_argument("--json", '-j', action="store_true", help="Output selection as JSON string hiearchy")
  args = parser.parse_args()

  output = ''
  
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
      except e:
        print(e)
    fsp.end(throw=False)
    output = json.dumps(fsp.selection)
    
  print(output)

