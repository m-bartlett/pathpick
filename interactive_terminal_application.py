import termios, atexit, sys, os, signal, io
import fcntl, termios, struct, shutil

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
  WIDTH, HEIGHT = 80, 25
  HEIGHT_1 = 24  # cache HEIGHT - 1 for graphical calculations


  @staticmethod
  def ioctl_GWINSZ(fd):
      try: cr = struct.unpack('hh', fcntl.ioctl(fd, termios.TIOCGWINSZ, '1234'))
      except: return
      return cr

  def get_terminal_size(self):
      env = os.environ
      cr = self.ioctl_GWINSZ(0) or self.ioctl_GWINSZ(1) or self.ioctl_GWINSZ(2)
      if not cr:
          try:
              # fd = os.open(os.ctermid(), os.O_RDONLY)
              cr = self.ioctl_GWINSZ(self.fd)
              # os.close(fd)
          except:
              pass
      if not cr:
          try: cr = shutil.get_terminal_size()
          except: cr = (env.get('LINES', 25), env.get('COLUMNS', 80))
      return int(cr[1]), int(cr[0])
  

  def puts(self, s):
    self.tty.write(s)
    self.tty.flush()
    
  
  def resize(self, *args):
    self.WIDTH, self.HEIGHT = self.get_terminal_size()
    self.HEIGHT_1 = self.HEIGHT - 1


  def __init__(self):
    """Open a different FD for TUI stdout so this application can be piped or captured to a shell
    variables without disrupting the TUI graphics and passing garbage ANSI sequences elsewhere"""
    self.fd   = os.open(os.ctermid(), os.O_NOCTTY | os.O_RDWR) # open file descriptor on controlling terminal
    self.stty = termios.tcgetattr(self.fd)  # save current TTY settings
    self.tty  = io.TextIOWrapper(io.FileIO(self.fd, 'w')) # open tty as a file-like for printing
    

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
  
  
  @staticmethod
  def ANSI_style( text,
                  fg        = None,
                  bg        = None,
                  bold      = False,
                  italic    = False,
                  underline = False,
                  reverse   = False  ):
    ANSI_sequence = []
    if fg is not None: ANSI_sequence.append(f"3{fg}")
    if bg is not None: ANSI_sequence.append(f"4{bg}")
    if bold:           ANSI_sequence.append("1")
    if italic:         ANSI_sequence.append("3")
    if underline:      ANSI_sequence.append("4")
    if reverse:        ANSI_sequence.append("7")
    if ANSI_sequence:  ANSI_sequence = f"\033[{';'.join(ANSI_sequence)}m"
    else:              ANSI_sequence=''
    return f"{ANSI_sequence}{text}\033[0m"


  def close(self):
    termios.tcsetattr(self.fd, termios.TCSADRAIN, self.stty) # restore saved TTY settings, e.g. echo & icanon
    self.show_cursor()
    # self.clear_screen()
    self.puts(
      "\033[?1004l"            # Disable focus-in/out reporting method 1
      "\033]777;focus;off\x07" # Disable focus-in/out reporting method 2 (urxvt)
    )
    self.primary_screen()
    try:
      sys.stderr.flush()
      sys.stdout.flush()
      self.tty.flush()
      self.tty.close()
    except BrokenPipeError: pass


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


  def end(self, *args, throw=False):
    atexit.unregister(self.close) # prevent duplicate execution of terminal restore
    self.close()
    signal.signal(signal.SIGWINCH, signal.SIG_DFL) # remove signal handler
    self.end      = lambda: None
    self.close    = lambda: None
    self.launch   = lambda: None
    self.__exit__ = lambda: None
    if throw:
      raise KeyboardInterrupt # received a user-input exit
    return False


  __exit__ = end
  
  def __enter__(self):
    self.launch()
    return self