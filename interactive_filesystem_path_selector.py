import pathlib
import re
import style
from filetype import filetype
from interactive_terminal_application import *


@singleton
class InteractiveFilesystemPathSelector(InteractiveTerminalApplication):
  header_message = None
  selection      = {}
  subselection   = selection
  path_list      = []
  path_list_last = 0
  path_list_len  = 0
  index      = 0
  row        = 0
  page       = 0
  page1      = 1
  pages      = 1
  pages1     = 1
  page_start = 0
  page_end   = 0
  styles     = {}


  @staticmethod
  def _iter2paths_with_hidden(it):
    return list(it)


  @staticmethod
  def _iter2paths_no_hidden(it):
    return [p for p in it if not p.name.startswith('.')]


  @staticmethod
  def _sort_path_list(path_list):
    return sorted(path_list)


  @staticmethod
  def _sort_path_list_directories_first(path_list):
    dirs  = [ d for d in path_list if d.is_dir() ]
    files = [ f for f in path_list if not f.is_dir() ]
    return sorted(dirs) + sorted(files)


  def __init__( self,
                root        = None,
                show_hidden = False,
                dirs_first  = False,
                styles      = {} ):
    super().__init__()

    for k, v in styles.items():
      self.styles[k] = style.Style(**v)

    if root and root != '.':
      root = pathlib.Path(root).expanduser().resolve()
      if not root.exists(): raise FileNotFoundError( f"Path '{root}' does not exist")
      if not root.is_dir(): raise NotADirectoryError(f"Path '{root}' is not a directory")
    else:
      root = pathlib.Path() # defaults to process $PWD

    root = root.absolute()

    if show_hidden:
      self.iter2paths = self._iter2paths_with_hidden
    else:
      self.iter2paths = self._iter2paths_no_hidden

    if dirs_first:
      self.sort_path_list = self._sort_path_list_directories_first
    else:
      self.sort_path_list = self._sort_path_list

    self.index = 0
    self.root = root
    self.cwd = root
    self.ls()

    self.input_action_map = {
         'Q  ': lambda: self.end(throw=True),
         'q  ': lambda: self.end(throw=True),
         'k  ': self.row_up,
         'j  ': self.row_down,
         'l  ': self.select_or_descend,
         'h  ': self.ascend,
         '   ': self.toggle_selected,
        '\t  ': self.toggle_selected,
        '\n  ': lambda: False,                 # enter key
      '\033  ': lambda: self.end(throw=True),  # escape
      '\033[A': self.row_up,                   # up
      '\033[B': self.row_down,                 # down
      '\033[C': self.select_or_descend,        # right
      '\033[D': self.ascend,                   # left
      '\033[5': self.page_up,                  # pageup
      '\033[6': self.page_down,                # pagedown
      '\x01  ': self.toggle_all_selected,      # ctrl-a
      '\x04  ': self.toggle_list_dirs_first,   # ctrl-d
      '\x08  ': self.toggle_list_hidden,       # ctrl-h
      '\x12  ': self.refresh,                  # ctrl-r
    }


  def read_key(self):
    event  = os.read(self.fd, 3).ljust(3).decode()
    try:
      ret = self.input_action_map[event]()
      if ret is not None: return ret
    except KeyError: pass
    return True


  def resize(self, *args):
    super().resize()
    self.draw_page()


  def truncate_right_to_width(self, s, width):
    if len(s) > width:
      truncated = self.styles['truncated']
      return s[:width-truncated.suffix_length] + truncated.suffix
    else:
      return s


  def truncate_left_to_width(self, s, width):
    if len(s) > width:
      truncated = self.styles['truncated']
      return truncated.prefix + s[-width+truncated.prefix_length:]
    else:
      return s


  def path_list_get(self, index=None):
    if index is None:  index = self.index
    try:               return self.path_list[index]
    except IndexError: return None


  def ls(self):
    self.path_list = self.sort_path_list(  self.iter2paths( self.cwd.iterdir() )  )
    self.path_list_len = max(len(self.path_list), 0)
    self.path_list_last = max(self.path_list_len - 1, 0)


  def paginate(self):
    if self.index > self.path_list_last:
      self.index = 0
    elif self.index < 0:
      self.index = self.path_list_last
    self.page, self.row = divmod(self.index, self.HEIGHT_1)
    self.page_start = self.index - self.row
    self.row += 2
    self.pages = self.path_list_len // self.HEIGHT_1
    self.page_end = min(self.page_start + self.HEIGHT_1, self.path_list_len)
    self.page1 = self.page + 1
    self.pages1 = self.pages + 1


  def draw_header(self, message):
    self.save_cursor_xy()
    self.cursor_home()
    self.clear_line()
    self.puts(message)
    self.restore_cursor_xy()


  def draw_header_info(self):
    _style    = self.styles['header']
    page_info = f' : {self.page1}/{self.pages1} ' if self.pages else ''  # TO-DO: only render this tring on page-change
    row_info  = f"   {self.index + (self.path_list_len>0)}/{self.path_list_len}{page_info}"
    width     = self.WIDTH - len(row_info) - _style.length
    path      = self.truncate_left_to_width(str(self.cwd), width)
    gap       = ' ' * (width - len(path))
    self.draw_header(_style.format(f"{path}{gap}{row_info}"))


  def draw_header_alert(self, message):
    _style  = self.styles['header']
    width   = self.WIDTH - _style.length
    message = self.truncate_left_to_width(message, width).center(width)
    self.draw_header(_style.format(message))
    
    
  def draw_row(self, index=None, active=False):
    if index is None: index = self.index
    path = self.path_list_get(index)
    if path is None: return
    path_name = path.name

    selected = self.subselection.get(path_name, False)
    this_style = style.Style()
    this_style.apply(self.styles[filetype(path)])
      
    if isinstance(selected, dict) and True in selected.values():
      this_style.apply(self.styles['children_selected'])
    elif selected is True:
      this_style.apply(self.styles['selected'])
    else:
      this_style.apply(self.styles['unselected'])
      
    if active:
      this_style.apply(self.styles['active'])
    else:
      this_style.apply(self.styles['inactive'])
    
    width = self.WIDTH - this_style.length
    text = self.truncate_right_to_width(path_name, width)
    text = this_style.format(text)

    self.clear_line()
    self.puts(text)


  def draw_cursor(self):
    self.cursor_xy(0, self.row)
    self.clear_line()
    self.draw_row(active=True)
    self.cursor_x(0)


  def draw_page(self):
    self.paginate()
    self.cursor_home()
    self.clear_screen()
    self.draw_header_info()
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
      self.draw_header_info()
      self.draw_cursor()


  def row_down(self):
    self.draw_row()
    self.index += 1
    self.row += 1
    if self.index >= self.page_end:
      self.draw_page()
    else:
      self.draw_header_info()
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
    path = self.path_list_get(self.index).name
    if path is None: return
    self.subselection[path] = not self.subselection.get(path, False)
    self.draw_cursor()


  def toggle_all_selected(self): # TO-DO: implement
    self.draw_header_alert("Selection toggled")


  def toggle_list_hidden(self): # TO-DO: implement
    self.draw_header_alert("Showing hidden files toggled")


  def toggle_list_dirs_first(self):
    self.draw_header_alert("Showing directories first toggled")


  def refresh(self):
    self.ls()
    self.draw_page()


  def ascend(self):
    cwd = self.cwd.parent
    cwd_str = str(cwd)

    if cwd_str.startswith(str(self.root)):
      key_hierarchy = cwd_str.partition(str(self.root))[2].split('/')[1:]
      subselection = self.selection
      for key in key_hierarchy:   # recurse from root to nesting n-1 to go up 1
        subselection = subselection[key]
      self.subselection = subselection
      _cwd = self.cwd
      self.cwd = cwd
      self.ls()
      self.index = self.path_list.index(_cwd)
      self.draw_page()


  def descend(self):
    newdir = self.path_list_get(self.index)
    newdirname = newdir.name
    cwd = self.cwd
    self.cwd = newdir.resolve()
    self.ls()
    if not str(cwd).startswith(str(self.root)):  return
    self.index = 0
    subselection = self.subselection.get(newdirname, None)
    if not isinstance(subselection, dict):
      self.subselection[newdirname] = {}
      subselection = self.subselection[newdirname]
    self.subselection = subselection
    self.draw_page()
    if self.path_list_len == 0:
      self.draw_header_alert(f"{newdirname} is an empty directory")



  def select_or_descend(self):
    path = self.path_list_get(self.index)
    if path is None: return
    if path.is_dir(): self.descend()
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