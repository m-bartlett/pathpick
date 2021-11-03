#!/usr/bin/env python
import termios, atexit, sys, os, signal, pathlib
from textwrap import shorten
# from time import sleep

"""
https://invisible-island.net/xterm/ctlseqs/ctlseqs.html
ESC [    Control Sequence Introducer (CSI  is 0x9b).
"""

def singleton(cls):
  instances = {}
  def getinstance(*args, **kwargs):
    return instances.get(cls, cls(*args, **kwargs))
  return getinstance


class InteractiveTerminalApplication():
  fd, stty = None, None
  WIDTH, HEIGHT = 10, 10

  @staticmethod
  def puts(s):
    print(s, end='')
    sys.stdout.flush()

  @staticmethod
  def _do_nothing():
    return


  def resize(self, *args):
    self.WIDTH, self.HEIGHT = os.get_terminal_size()


  def __init__(self):
    self.fd = sys.stdin.fileno()
    self.stty = termios.tcgetattr(self.fd)  # save current TTY settings


  def close(self):
    termios.tcsetattr(self.fd, termios.TCSADRAIN, self.stty) # restore saved TTY settings, e.g. echo & icanon
    self.puts(
      # "\033[2J"                # Clear screen
      "\033[?25h"              # Show cursor
      "\033[?1004l"            # Disable focus-in/out reporting method 1
      "\033]777;focus;off\x07" # Disable focus-in/out reporting method 2 (urxvt)
      "\033[?1049l"            # Switch back to primary screen buffer
    )


  def launch(self):
    """ Manual terminal graphics init """
    atexit.register(self.close) # in case an unexpected exit occurs, restore the terminal back to its starting state
    new = termios.tcgetattr(self.fd)       #
    new[3] = new[3] & ~termios.ECHO   # disable echo, i.e. don't print input chars
    new[3] = new[3] & ~termios.ICANON # disable canonical (line edit) mode, chars sent immediately without buffer
      # *T*erminal *C*hange *S*hell *A*ction
      # TCSANOW -> change occurs immediately
      # TCSADRAIN -> await all output to be transmitted. Use when changing parameters that affect output.
      # TCSAFLUSH -> await all output to be transmitted, and all existing unprocessed input is discarded.
    termios.tcsetattr(self.fd, termios.TCSADRAIN, new)
    self.puts(
      "\033[?1004h"           # Enable focus-in/out reporting method 1
      "\033]777;focus;on\x07" # Enable focus-in/out reporting method 2 (urxvt)
      "\033[?25l"             # Hide cursor
      "\033[?1049h"           # Switch to alternate screen buffer
      "\033[2J"               # Clear entire screen
    )
    signal.signal(signal.SIGWINCH, self.resize)
    self.resize()


  def end(self, *args, return_code=1, throw=False):
    atexit.unregister(self.close)
    self.close()
    signal.signal(signal.SIGWINCH, signal.SIG_DFL) # remove signal handler
    self.__exit__ = self._do_nothing
    if throw:
      raise KeyboardInterrupt
    return return_code


  def __enter__(self):
    self.launch()
    return self

  __exit__  = end




@singleton
class InteractiveFilesystemPathSelector(InteractiveTerminalApplication):
  HEIGHT_1 = 0
  selected = {}
  subselected = selected
  path_list = []
  path_list_last = 0
  index = 0

  @staticmethod
  def _glob2paths_no_hidden(glob):
    return [
      ( p.name + '/' if p.is_dir() else p.name )
      for p in glob
      if not p.name.startswith('.')
    ]

  @staticmethod
  def _glob2paths_with_hidden(glob):
    return [
      ( p.name + '/' if p.is_dir() else p.name )
      for p in glob
    ]

  @staticmethod
  def _sort_path_list(glob):
    return sorted(glob)

  @staticmethod
  def _sort_path_list_directories_first(glob):
      path_list = [i for i in glob]
      dirs = [i for i in glob if i.endswith('/')]
      files = [i for i in glob if not i.endswith('/')]
      return sorted(dirs) + sorted(files)


  def __init__( self,
                root       = None,
                absolute   = False,
                hidden     = False,
                dirs_first = False  ):
    super().__init__()

    if root:
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
      ord(" "):  lambda e: self.select,
      ord("\t"): lambda e: self.select,
      27:        lambda e: self.control_character_action_map[e](), # escaped '['
      # 10:        lambda e: self.end(return_code=0), # enter key
      10:        lambda e: print(self.path_list), # enter key
    }

    self.control_character_action_map = {            # TO-DO: page up/down
      # ord("M"): lambda: puts("mouse"),
      # ord("I"): lambda: puts("focus"),
      # ord("O"): lambda: puts("unfocus"),
      ord("A"): self.cursor_up,          # up
      ord("B"): self.cursor_down,        # down
      ord("C"): self.select_or_descend,  # right
      ord("D"): self.ascend,             # left
      ord(' '): lambda: self.end(return_code=1, throw=True)  # escape
    }
    

  def resize(self, *args):
    self.WIDTH, self.HEIGHT = os.get_terminal_size()
    self.HEIGHT_1 = self.HEIGHT - 1
    self.HEIGHT_2 = self.HEIGHT - 2
    self.HEIGHT_3 = self.HEIGHT - 3


  def cd(self, _dir):
    if _dir=='.':
      return
    elif _dir=='..':
      cwd = self.cwd.parent
    else:
      cwd = self.cwd/_dir
    if not str(cwd).startswith(str(self.root)):
      raise RecursionError("Can't leave root directory")
    self.cwd = cwd
    self.ls()


  def ls(self):
    self.path_list = self.sort_path_list(  self.glob2paths( self.cwd.glob('*') )  )
    self.path_list_len = len(self.path_list)
    self.path_list_last = self.path_list_len - 1


  def read_key(self):
    char, escape, event  = os.read(self.fd, 3).ljust(3)
    try: self.character_action_map[char](event)
    except KeyError: pass


  def draw_page(self):
    self.puts(
      "\033[0;0H" # Move cursor to position 0,0 (top left)
      "\033[2J"   # Clear entire screen
    )
    page, row = divmod(self.index, self.HEIGHT_1)
    row += 2
    page_start = page * self.HEIGHT_1
    page_end = page_start + self.HEIGHT_1 # min(self.HEIGHT_2, self.path_list_len - page_start)
    print(self.cwd, page, page_start, page_end, row, self.index)
    prefix = '  '
    self.puts(prefix)
    self.puts( ('\n'+prefix).join([ shorten(str(i), self.WIDTH, placeholder='...')
                                for i in self.path_list[page_start:page_end] ]) )
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


  def select(self):
    self.puts('select')


  def select_or_descend(self):
    self.puts('select_or_descend')


  def ascend(self):
    self.puts('ascend')






if __name__ == "__main__":

  import argparse
  parser = argparse.ArgumentParser()
  parser.add_argument("root", type=str, nargs='?', default=None, help="Directory to explore. Default is $PWD")
  parser.add_argument("--absolute", action="store_true", help="Use absolute paths for selection display and output")
  parser.add_argument("--hidden", action="store_true", help="Show hidden files and directories that are prefixed with '.'")
  parser.add_argument("--dirs-first", action="store_true", help="")
  args = parser.parse_args()

  with InteractiveFilesystemPathSelector( root         = args.root,
                                          absolute     = args.absolute,
                                          hidden       = args.hidden,
                                          dirs_first = args.dirs_first ) as fsp:
    fsp.draw_page()
    while True:
      try:
        fsp.read_key()
      except KeyboardInterrupt:
        break