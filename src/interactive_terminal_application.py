import atexit, sys, os, signal, io, fcntl, termios, struct, shutil

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
    try:
      return struct.unpack('hh', fcntl.ioctl(fd, termios.TIOCGWINSZ, '1234'))
    except:
      return


  def get_terminal_size(self):
    if not (cr := self.ioctl_GWINSZ(self.fd)):
      try:    cr = shutil.get_terminal_size()
      except: cr = (os.getenv('LINES', 25), os.getenv('COLUMNS', 80))
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
  

  def close(self):
    termios.tcsetattr(self.fd, termios.TCSADRAIN, self.stty) # restore saved TTY settings, e.g. echo & icanon
    self.show_cursor()
    # self.clear_screen()
    self.primary_screen()
    try:
      sys.stderr.flush()
      sys.stdout.flush()
      self.tty.flush()
      self.tty.close()
    except BrokenPipeError: pass


  def launch(self):
    """ Manual terminal graphics init """
    # See `man termios` for flag information
    atexit.register(self.close) # in case an unexpected exit occurs, restore the terminal back to its starting state
    new = termios.tcgetattr(self.fd)       #

    # `& ~()` disables flags, `|()` enables flags
    iflag, oflag, cflag, lflag, ispeed, ospeed, cc = new

    iflag = iflag | (0
      # termios.IGNCR | # Ignore carriage return
      # termios.ICRNL   # Translate carriage return to newline (unless IGNCR=1)
    )

    lflag = lflag & ~( termios.ECHO   | # echo input -- disable printing input
                       termios.ICANON ) # Disable canonical mode so input is available immediately

      # *T*erminal *C*hange *S*hell *A*ction
      # TCSANOW -> change occurs immediately
      # TCSADRAIN -> await all output to be transmitted. Use when changing parameters that affect output.
      # TCSAFLUSH -> await all output to be transmitted, and all existing unprocessed input is discarded.
    termios.tcsetattr( self.fd,
                       termios.TCSADRAIN,
                       [iflag, oflag, cflag, lflag, ispeed, ospeed, cc] )
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