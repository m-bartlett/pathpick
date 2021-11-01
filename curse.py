#!/usr/bin/env python
import termios, atexit, sys, os, signal, pathlib, argparse
from textwrap import shorten
from time import sleep

"""
https://invisible-island.net/xterm/ctlseqs/ctlseqs.html
ESC [    Control Sequence Introducer (CSI  is 0x9b).
"""

puts = lambda s: print(s, end='')


## Manual terminal graphics init ########################################################################

fd = sys.stdin.fileno()
stty = termios.tcgetattr(fd)  # save current TTY settings
def cleanup(pause=True):
  global fd, stty
    # *T*erminal *C*hange *S*hell *A*ction
    # TCSANOW -> change occurs immediately
    # TCSADRAIN -> await all output to be transmitted. Use when changing parameters that affect output.
    # TCSAFLUSH -> await all output to be transmitted, and all existing unprocessed input is discarded.
  termios.tcsetattr(fd, termios.TCSADRAIN, stty) # restore saved TTY settings, e.g. echo & icanon
  puts(
    "\033[?25h"              # Show cursor
    "\033[?1004l"            # Disable focus-in/out reporting method 1
    "\033]777;focus;off\x07" # Disable focus-in/out reporting method 2 (urxvt)
  )
  if pause: sleep(5)
  puts(
    "\033[2J"                # Clear screen
    "\033[?1049l"            # Switch back to primary screen buffer
  )

new = termios.tcgetattr(fd)       #
new[3] = new[3] & ~termios.ECHO   # disable echo, i.e. don't print input chars
new[3] = new[3] & ~termios.ICANON # disable canonical (line edit) mode, chars sent immediately without buffer
termios.tcsetattr(fd, termios.TCSADRAIN, new)

puts(
  "\033[?1004h"           # Enable focus-in/out reporting method 1
  "\033]777;focus;on\x07" # Enable focus-in/out reporting method 2 (urxvt)
  "\033[?25l"             # Hide cursor
  "\033[?1049h"           # Switch to alternate screen buffer
  "\033[0;0H"             # Move cursor to position 0,0 (top left)
  "\033[2J"               # Clear entire screen
)

atexit.register(cleanup) # in case an unexpected exit occurs, restore the terminal back to its starting state

## Manual terminal graphics end #########################################################################


def die(message='', exit_code=1):
  atexit.unregister(cleanup)
  cleanup(pause=False)
  sys.stdout.flush()
  sys.stderr.flush()
  if len(message):
    print(message, file = sys.stderr if exit_code > 0 else sys.stdout)
  sys.exit(exit_code)



character_action_map = {
  ord("Q"):  lambda e: die(exit_code=1),
  ord("q"):  lambda e: die(exit_code=1),
  ord(" "):  lambda e: puts("space"),
  ord("\t"): lambda e: puts("tab"),
  27:        lambda e: control_character_action_map[e](),
  10:        lambda e: puts("enter"),
}

control_character_action_map = {
  ord("M"): lambda: puts("mouse"),
  ord("I"): lambda: puts("focus"),
  ord("O"): lambda: puts("unfocus"),
  ord("A"): lambda: puts("up"),
  ord("B"): lambda: puts("down"),
  ord("C"): lambda: puts("right"),
  ord("D"): lambda: puts("left"),
  ord(' '): lambda: die(exit_code=1)
}



WIDTH, HEIGHT = 10,10
def resize(*args):
  global WIDTH
  global HEIGHT
  WIDTH, HEIGHT = os.get_terminal_size()
  # puts(
  #   "\033[0H" # Move to 0,0 (top left)
  #   "\033[0J" # Clear from cursor to end of screen
  #   # f"\033[{HEIGHT}E" # Move down HEIGHT lines
  # )
  # sys.stdout.flush()

signal.signal(signal.SIGWINCH, resize)
resize()


parser = argparse.ArgumentParser()
parser.add_argument("--ascii", action="store_true", help="Use ascii symbols to denote filesystem hiearchy")
parser.add_argument("--root", type=str, default=None, help="Directory to explore. Default is $PWD")
parser.add_argument("--absolute", action="store_true", help="Use absolute paths for selection display and output")
parser.add_argument("--hidden", type=str, help="Show hidden files and directories that are prefixed with '.'")
parser.add_argument("--directories-first", type=str, help="")
args = parser.parse_args()

if args.root:
  root = pathlib.Path(args.root).expanduser()
  if not root.exists(): die(f"Error: path '{root}' does not exist")
  if not root.is_dir(): die(f"Error: path '{root}' is not a directory")
else:
  root = pathlib.Path() # defaults to process $PWD

if args.absolute:
  root = root.absolute()

cwd = root

path_list = [p for p in cwd.glob('*')]

cursor=0

# _path_to_screen_list = lambda s:

draw_page(path_list, cursor):
  puts(
    "\033[0;0H" # Move cursor to position 0,0 (top left)
    "\033[2J"   # Clear entire screen
  )
  page_height = 3 - ...
  print(cwd)
  print('\n'.join([shorten(str(i), WIDTH, placeholder='...') for i in path_list]))


selected = {}
screen_list = _path_to_screen_list(cwd)
print('\n'.join(screen_list))


while True:
  sys.stdout.flush()
  try:
    char, escape, event  = os.read(fd, 3).ljust(3)
    try:
      puts(f"\033[0;0H\033[0K")
      character_action_map[char](event)
    except KeyError:
      print(char, escape, event)

  except ValueError:
    continue

  except KeyboardInterrupt:
    cleanup()
    exit(0)
