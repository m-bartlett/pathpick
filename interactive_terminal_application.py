import termios, atexit, sys, os, signal

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


  def resize(self, *args):
    self.WIDTH, self.HEIGHT = os.get_terminal_size()


  def __init__(self):
    self.fd = sys.stdin.fileno()
    self.stty = termios.tcgetattr(self.fd)  # save current TTY settings


  def cursor_home(self):           self.puts('\033[0H')
  def cursor_x(self, x):           self.puts(f'\033[{x}G')
  def cursor_y(self, y):           self.puts(f'\033[{y}H')
  def cursor_xy(self, x, y):       self.puts(f'\033[{y};{x}H')
  def cursor_up(self, n=0):        self.puts(f'\033[{n}F')
  def cursor_down(self, n=0):      self.puts(f'\033[{n}E')
  def clear_line_to_end(self):     self.puts('\033[0K')
  def clear_line_to_start(self):   self.puts('\033[1K')
  def clear_line(self):            self.puts('\033[2K')
  def clear_screen_to_end(self):   self.puts('\033[0J')
  def clear_screen_to_start(self): self.puts('\033[1J')
  def clear_screen(self):          self.puts('\033[2J')
  def hide_cursor(self):           self.puts("\033[?25l")
  def show_cursor(self):           self.puts("\033[?25h")
  def alt_screen(self):            self.puts("\033[?1049h")
  def primary_screen(self):        self.puts("\033[?1049l")
  def save_cursor_xy(self):        self.puts("\033[s")
  def restore_cursor_xy(self):     self.puts("\033[u")
  
  
  def color(self, text, fg=None, bg=None, bold=False):
    color=[]
    if fg is not None: color.append(f"3{fg}")
    if bg is not None: color.append(f"4{bg}")
    if bold:           color.append("1")
    if len(color):     color = f"\033[{';'.join(color)}m"
    return f"{color}{text}\033[0m"


  def close(self):
    termios.tcsetattr(self.fd, termios.TCSADRAIN, self.stty) # restore saved TTY settings, e.g. echo & icanon
    self.show_cursor()
    # self.clear_screen()
    self.puts(
      "\033[?1004l"            # Disable focus-in/out reporting method 1
      "\033]777;focus;off\x07" # Disable focus-in/out reporting method 2 (urxvt)
    )
    from time import sleep
    sys.stderr.flush()
    sys.stdout.flush()
    sleep(5)
    self.primary_screen()


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
    )
    self.hide_cursor()
    self.alt_screen()
    self.clear_screen()
    signal.signal(signal.SIGWINCH, self.resize)
    self.resize()


  def end(self, *args, return_code=1, throw=False):
    atexit.unregister(self.close) # prevent duplicate execution of terminal restore
    self.close()
    signal.signal(signal.SIGWINCH, signal.SIG_DFL) # remove signal handler
    self.end    = lambda: None
    self.close  = lambda: None
    self.launch = lambda: None
    if throw:
      raise KeyboardInterrupt # received a user-input exit
    return return_code


  def __enter__(self):
    self.launch()
    return self


  __exit__  = end