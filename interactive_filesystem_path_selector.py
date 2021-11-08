from interactive_terminal_application import *
import pathlib

from time import sleep

@singleton
class InteractiveFilesystemPathSelector(InteractiveTerminalApplication):
  HEIGHT_1 = 1
  UNSELECTED_PREFIX       = '  '
  SELECTED_PREFIX         = '  '
  PARTIAL_SELECTED_PREFIX = '  '
  SELECTED_COLOR          = 4
  PARTIAL_SELECTED_COLOR  = 6
  ACTIVE_ROW_INDICATOR    = '>'
  # ACTIVE_ROW_COLOR        = '7;30;1'
  ACTIVE_ROW_COLOR        = '0;1'
  INACTIVE_ROW_INDICATOR = ''

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
    return [( p.name + '/' if p.is_dir() else p.name ) for p in glob ]

  @classmethod
  def _glob2paths_no_hidden(cls, glob):
    return [p for p in cls._glob2paths_with_hidden(glob) if not p.startswith('.') ]

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

    self.input_action_map = {
         'Q  ': lambda: self.end(return_code=1, throw=True),
         'q  ': lambda: self.end(return_code=1, throw=True),
         '   ': self.toggle_selected,
        '\t  ': self.toggle_selected,
        '\n  ': lambda: True,           # enter key
      '\033  ': lambda: self.end(return_code=1, throw=True),  # escape
      '\033[A': self.row_up,            # up
      '\033[B': self.row_down,          # down
      '\033[5': self.page_up,           # PageUp
      '\033[6': self.page_down,         # PageDown
      '\033[C': self.select_or_descend, # right
      '\033[D': self.ascend,            # left
      # b'\x01  ': self.select_all       # TO-DO ctrl-A is select-all in current dir
    }


  def resize(self, *args):
    self.WIDTH, self.HEIGHT = self.get_terminal_size()
    self.HEIGHT_1 = self.HEIGHT - 1
    self.draw_page()


  def read_key(self):
    event  = os.read(self.fd, 3).ljust(3).decode()
    try:
      return self.input_action_map[event]()
    except KeyError:
      return False


  def truncate_to_width(self, s):
    return s[:self.WIDTH-3]+'...' if len(s) > self.WIDTH else s


  def path_list_get(self, index=None):
    if index is None:  index = self.index
    try:               return self.path_list[index]
    except IndexError:
      return None


  def is_dir(self, s):
    return (self.cwd / s).resolve().is_dir()


  def paginate(self):
    if self.index > self.path_list_last:
      self.index = 0
    elif self.index < 0:
      self.index = self.path_list_last
    self.page, self.row = divmod(self.index, self.HEIGHT_1)
    self.page_start = self.index - self.row
    # self.page_start = self.page * self.HEIGHT_1
    self.row += 2
    self.pages = self.path_list_len // self.HEIGHT_1
    self.page_end = min(self.page_start + self.HEIGHT_1, self.path_list_len)
    self.page1 = self.page + 1
    self.pages1 = self.pages + 1


  def draw_header(self):
    header = f"   {self.page1}/{self.pages1} ({(self.index+1)*100//max(1,self.path_list_len)}%)"
    path_width = self.WIDTH - len(header)
    path = str(self.cwd)
    if len(path) > path_width:  path = '...' + path[-(path_width-3):]
    gap = ' ' * (path_width - len(path))
    self.save_cursor_xy()
    self.cursor_home()
    self.clear_line()
    self.puts(self.color(f"{path}{gap}{header}", bold=True, fg=7, bg=0))
    self.restore_cursor_xy()


  def draw_row(self, index=None, active=False):
    if index is None:
      index = self.index
    item = self.path_list_get(index)
    if item is None:
      return

    selection_symbol = self.SELECTED_PREFIX
    selection_color_fg = self.SELECTED_COLOR
    selection_color_bg = None
    row_activity_indicator = self.INACTIVE_ROW_INDICATOR

    if active:
      row_activity_indicator = self.ACTIVE_ROW_INDICATOR
      selection_color_bg = self.ACTIVE_ROW_COLOR

    # if item.endswith('/'):
    if self.is_dir(item):
      selected = self.subselection.get(item[:-1], {})
      if isinstance(selected, dict):
        selected = True in selected.values()
        selection_symbol = self.PARTIAL_SELECTED_PREFIX
        selection_color_fg = self.PARTIAL_SELECTED_COLOR
    else:
      selected = self.subselection.get(item, False)

    if selected:
      prefix = f"{row_activity_indicator}{selection_symbol}"
    else:
      selection_color_fg = None
      prefix = f"{row_activity_indicator}{self.UNSELECTED_PREFIX}"

    item = self.truncate_to_width(f'{prefix}{item}')
    item = item.ljust(self.WIDTH)
    item = self.color(item, fg=selection_color_fg, bg=selection_color_bg)

    self.clear_line()
    self.puts(item)


  def draw_cursor(self):
    self.cursor_xy(0, self.row)
    self.clear_line()
    self.draw_row(active=True)
    self.cursor_x(0)


  def draw_page(self):
    self.paginate()
    self.cursor_home()
    self.clear_screen()
    self.draw_header()
    self.cursor_home()
    for i in range(self.page_start, self.page_end):
      self.puts('\n')
      self.draw_row(i)
    self.draw_cursor()


  def row_up(self):
    self.draw_row()
    self.index -= 1
    self.row -= 1
    if self.index < self.page_start:
      self.draw_page()
    else:
      self.draw_header()
      self.draw_cursor()


  def row_down(self):
    self.draw_row()
    self.index += 1
    self.row += 1
    if self.index >= self.page_end:
      self.draw_page()
    else:
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
    path = self.path_list_get(self.index)
    if path is None: return
    if path.endswith('/'): path = path[:-1]
    self.subselection[path] = not self.subselection.get(path, False)
    self.draw_cursor()


  def ls(self):
    self.path_list = ['../'] + self.sort_path_list(  self.glob2paths( self.cwd.glob('*') )  )
    # self.path_list = self.sort_path_list(  self.glob2paths( self.cwd.glob('*') )  )
    self.path_list_len = max(len(self.path_list), 0)
    self.path_list_last = max(self.path_list_len - 1, 0)


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
    path = self.path_list_get(self.index)
    key  = path[:-1] # strip trailing /
    cwd = self.cwd
    cwd = (self.cwd/path).resolve()

    # if self.path_list_len:

    if str(cwd).startswith(str(self.root)):

      self.cwd = cwd
      self.ls()
      self.index = 0
      subselection = self.subselection.get(key, None)
      if not isinstance(subselection, dict):
        self.subselection[key] = {}
        subselection = self.subselection[key]
      self.subselection = subselection
      self.draw_page()


    # else:
    #   self.cwd = cwd
    #   self.ls()
    #   self.clear_line()
    #   message = f"{self.path_list[self.index]} is empty"
    #   message = self.truncate_to_width(message)
    #   message = message.ljust(self.WIDTH)
    #   self.puts( self.color(message,fg=0,bg=1, bold=True) )
    #   self.cursor_x(0)


  def select_or_descend(self):
    path = self.path_list_get(self.index)
    if path is None: return
    if path.endswith('/'): self.descend()
    else: self.toggle_selected()


  @classmethod
  def _nested_dict_to_path_strings(cls, dir, j):
    paths = []
    for k,v in j.items():
      if v is True:
        paths.append(f"{dir}/{k}")
      elif isinstance(v, dict):
        paths += cls._nested_dict_to_path_strings(f"{dir}/{k}", v)
    return paths


  def get_selection_paths(self):
    return self._nested_dict_to_path_strings(str(self.root), self.selection)