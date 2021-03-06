import pathlib
from .style import Style
from .filetype import filetype
from .interactive_terminal_application import *


@singleton
class InteractivePathSelector(InteractiveTerminalApplication):
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
  page_info  = ''
  style      = {}


  @staticmethod
  def _noop(): return


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
                style       = {} ):
    super().__init__()

    if not style:
      from .config import default_config
      style = default_config['style']

    for k, v in style.items():
      self.style[k] = Style(**v)

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
        '\n  ': lambda: False,                # enter key
      '\033  ': lambda: self.end(throw=True), # escape
      '\033[A': self.row_up,                  # up
      '\033[B': self.row_down,                # down
      '\033[C': self.select_or_descend,       # right
      '\033[D': self.ascend,                  # left
      '\033[5': self.page_up,                 # pageup
      '\033[6': self.page_down,               # pagedown
      '\x01  ': self.toggle_all_selected,    # ctrl-a
      '\x04  ': self.toggle_show_dirs_first,  # ctrl-d
      '\x08  ': self.toggle_show_hidden,      # ctrl-h
      '\x12  ': self.refresh_manual,          # ctrl-r
    }


  def read_key(self):
    event  = os.read(self.fd, 3).ljust(3).decode()
    return_value = self.input_action_map.get(event, self._noop)()
    if return_value is not None:
      return return_value
    return True


  def resize(self, *args):
    super().resize()
    self.draw_page()


  def truncate_right_to_width(self, s, width):
    if len(s) > width:
      truncated = self.style['truncated']
      return s[:width-truncated.suffix_length] + truncated.suffix
    else:
      return s


  def truncate_left_to_width(self, s, width):
    if len(s) > width:
      truncated = self.style['truncated']
      return truncated.prefix + s[-width+truncated.prefix_length:]
    else:
      return s


  def path_list_get(self, index=None):
    if index is None:  index = self.index
    try:               return self.path_list[index]
    except IndexError: return None


  def ls(self):
    self.path_list      = self.sort_path_list(  self.iter2paths( self.cwd.iterdir() )  )
    self.path_list_len  = max(len(self.path_list), 0)
    self.path_list_last = max(self.path_list_len - 1, 0)
    self.path_list_any  = self.path_list_len > 0


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
    self.page_info = f' : {self.page1}/{self.pages1} ' if self.pages > 0 else ''


  def draw_header(self, message):
    self.save_cursor_xy()
    self.cursor_home()
    self.clear_line()
    self.puts(message)
    self.restore_cursor_xy()


  def draw_header_info(self):
    _style    = self.style['header']
    row_info  = f"   {self.index + self.path_list_any}/{self.path_list_len}{self.page_info}"
    width     = self.WIDTH - len(row_info) - _style.length
    path      = self.truncate_left_to_width(str(self.cwd), width)
    gap       = ' ' * (width - len(path))
    self.draw_header(_style.format(f"{path}{gap}{row_info}"))


  def draw_header_alert(self, message):
    _style  = self.style['header']
    width   = self.WIDTH - _style.length
    message = self.truncate_left_to_width(message, width).center(width)
    self.draw_header(_style.format(message))
    
    
  def draw_row(self, index=None, active=False):
    if index is None: index = self.index
    path = self.path_list_get(index)
    if path is None: return
    path_name = path.name

    selected = self.subselection.get(path_name, False)
    row_style = Style()
    row_style.apply(self.style[filetype(path)])

    # if isinstance(selected, dict) and True in selected.values():
    if isinstance(selected, dict) and selected:
      row_style.apply(self.style['nested_selected'])
    elif selected:
      row_style.apply(self.style['selected'])
    else:
      row_style.apply(self.style['unselected'])
      
    if active:
      row_style.apply(self.style['active'])
    else:
      row_style.apply(self.style['inactive'])

    row_style.reset = True
    row_style.update_template()
    width = self.WIDTH - row_style.length
    text = self.truncate_right_to_width(path_name, width)
    text = row_style.format(text)

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


  def refresh(self):
    active_element = self.path_list_get()
    self.ls()
    try: self.index = self.path_list.index(active_element)
    except ValueError: pass
    self.draw_page()


  def refresh_manual(self):
    self.refresh()
    self.draw_header_alert("Directory listing refreshed")


  def toggle_selected(self):
    path = self.path_list_get(self.index).name
    if path is None: return
    if self.subselection.get(path, False):
      del self.subselection[path]
    else:
      self.subselection[path] = True
    self.draw_cursor()


  def toggle_all_selected(self): # TO-DO del unselect
    all_selected = all(self.subselection.get(path.name, False) for path in self.path_list)
    if all_selected:
      message ="All deselected"
      # for key in self.subselection.keys():
        # del self.subselection[key]
      self.subselection.clear()
    else:
      message = "All selected"
      for path in self.path_list:
        self.subselection[path.name] = True
    self.refresh()
    self.draw_header_alert(message)


  def toggle_show_hidden(self):
    if self.iter2paths is self._iter2paths_with_hidden:
      self.iter2paths = self._iter2paths_no_hidden
      message = "Hidden files ignored"
    else:
      self.iter2paths = self._iter2paths_with_hidden
      message = "Hidden files displayed"
    self.refresh()
    self.draw_header_alert(message)


  def toggle_show_dirs_first(self):
    if self.sort_path_list is self._sort_path_list:
      self.sort_path_list = self._sort_path_list_directories_first
      message = "Directories listed first"
    else:
      self.sort_path_list = self._sort_path_list
      message = "All listed alphabetically"
    self.refresh()
    self.draw_header_alert(message)


  def ascend(self):
    parent = self.cwd.parent
    if parent.is_relative_to(self.root):
      key_hierarchy = parent.relative_to(self.root).parts
      subselection = self.selection
      for key in key_hierarchy:   # recurse from root to nesting n-1 to go up 1
        subselection = subselection[key]
      if not subselection.get(self.cwd.name, True):
        del subselection[self.cwd.name]
      self.subselection = subselection
      cwd = self.cwd
      self.cwd = parent
      self.ls()
      self.index = self.path_list.index(cwd)
      self.draw_page()
    else:
      self.draw_header_alert(f"Cannot ascend past root")


  def descend(self):
    newdir = self.path_list_get(self.index)
    newdirname = newdir.name
    cwd = self.cwd
    self.cwd = newdir.resolve()
    self.ls()
    self.index = 0
    subselection = self.subselection.get(newdirname, None)
    if not isinstance(subselection, dict):
      self.subselection[newdirname] = {}
      subselection = self.subselection[newdirname]
    self.subselection = subselection
    self.draw_page()
    if not self.path_list_any:
      self.draw_header_alert(f"{newdirname} is empty")


  def select_or_descend(self):
    path = self.path_list_get(self.index)
    if path is None: return
    if path.is_dir(): self.descend()
    else: self.toggle_selected()


  @classmethod
  def _nested_dict_to_path_strings(cls, path_prefix: str, selection: dict):
    paths = []
    for k,v in selection.items():
      if v is True:
        paths.append(f"{path_prefix}/{k}")
      elif isinstance(v, dict):
        paths += cls._nested_dict_to_path_strings(f"{path_prefix}/{k}", v)
    return paths


  def get_selection_paths(self):
    return self._nested_dict_to_path_strings(str(self.root), self.selection)


  @classmethod
  def _nested_dict_to_path_dict(cls, selection: dict):
    true_selection = {}
    for k,v in selection.items():
      if v is True:
        true_selection[k] = v
      elif isinstance(v, dict):
        if v:
          true_selection[k] = cls._nested_dict_to_path_dict(v)
    return true_selection


  def get_selection_dict(self):
    return self._nested_dict_to_path_dict(self.selection)