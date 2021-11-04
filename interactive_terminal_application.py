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


  def close(self):
    termios.tcsetattr(self.fd, termios.TCSADRAIN, self.stty) # restore saved TTY settings, e.g. echo & icanon
    self.puts(
      # "\033[2J"                # Clear screen
      "\033[?25h"              # Show cursor
      "\033[?1004l"            # Disable focus-in/out reporting method 1
      "\033]777;focus;off\x07" # Disable focus-in/out reporting method 2 (urxvt)
    # )
    # from time import sleep
    # sys.stderr.flush()
    # sys.stdout.flush()
    # sleep(5)
    # self.puts(
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
    atexit.unregister(self.close) # prevent duplicate execution of terminal restore
    self.close()
    signal.signal(signal.SIGWINCH, signal.SIG_DFL) # remove signal handler
    self.__exit__ = lambda: None
    if throw:
      raise KeyboardInterrupt # received a user-input exit
    return return_code


  def __enter__(self):
    self.launch()
    return self


  __exit__  = end