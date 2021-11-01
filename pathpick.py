#!/usr/bin/env python3
import curses
import argparse
import os
import pathlib


KEYS_ENTER  = (curses.KEY_ENTER, ord('\n'), ord('\r'))
KEYS_UP     = (curses.KEY_UP,    ord('k'))
KEYS_DOWN   = (curses.KEY_DOWN,  ord('j'))
KEYS_SELECT = (curses.KEY_RIGHT, ord(' '))

# parser = argparse.ArgumentParser()
# parser.add_argument("--ascii", action="store_true", help="use ascii symbols to denote filesystem hiearchy")
# parser.add_argument("--root", type=str, help="directory to explore (can't ascend up from this directory). Default is $PWD")
# parser.add_argument("--absolute", type=str, help="use absolute paths for selection display and output")
# parser.add_argument("--hidden", type=str, help="show hidden files and directories that are prefixed with '.'")
# parser.add_argument("--directories-first", type=str, help="show hidden files and directories that are prefixed with '.'")
# args = parser.parse_args()

CHILD_NTH_ = "├"
CHILD_MORE = "│"
CHILD_LAST = "└"
CHILD_LEAF = "─"

"""
- Selecting child of selected folder unselects the folder (i.e. if folder isn't a nested dict but a string, it represents the folder)
- Change view to show dir as root dir if descending inward?
- Don't allow ascending past initial dir
"""




class InteractiveFilesystemPathSelector():

  screen = []
  selected = {}
  index = 0
  page = 0

  def move():
    window.clrtoeol()

    ...

  def line_down():
    ...

  def page_up():
    ...

  def page_down():
    ...

  def select(self):
    ...




  def move_up(self):
      self.index -= 1
      if self.index < 0:
          self.index = len(self.options) - 1

  def move_down(self):
      self.index += 1
      if self.index >= len(self.options):
          self.index = 0

  def select(self):
      if self.multiselect:
          if self.index in self.all_selected:
              self.all_selected.remove(self.index)
          else:
              self.all_selected.append(self.index)

  def get_selected(self):
      """return the current selected option as a tuple: (option, index)
         or as a list of tuples (in case multiselect==True)
      """
      if self.multiselect:
          return_tuples = []
          for selected in self.all_selected:
              return_tuples.append((self.options[selected], selected))
          return return_tuples
      else:
          return self.options[self.index], self.index

  def get_title_lines(self):
      if self.title:
          return self.title.split('\n') + ['']
      return []

  def get_option_lines(self):
      lines = []
      for index, option in enumerate(self.options):
          # pass the option through the options map of one was passed in
          if self.options_map_func:
              option = self.options_map_func(option)

          if index == self.index:
              prefix = self.indicator
          else:
              prefix = len(self.indicator) * ' '

          if self.multiselect and index in self.all_selected:
              format = curses.color_pair(1)
              line = ('{0} {1}'.format(prefix, option), format)
          else:
              line = '{0} {1}'.format(prefix, option)
          lines.append(line)

      return lines

  def get_lines(self):
      title_lines = self.get_title_lines()
      option_lines = self.get_option_lines()
      lines = title_lines + option_lines
      current_line = self.index + len(title_lines) + 1
      return lines, current_line

  def draw(self):
      """draw the curses ui on the screen, handle scroll if needed"""
      self.screen.clear()

      x, y = 1, 1  # start point
      max_y, max_x = self.screen.getmaxyx()
      max_rows = max_y - y  # the max rows we can draw

      lines, current_line = self.get_lines()

      # calculate how many lines we should scroll, relative to the top
      scroll_top = getattr(self, 'scroll_top', 0)
      if current_line <= scroll_top:
          scroll_top = 0
      elif current_line - scroll_top > max_rows:
          scroll_top = current_line - max_rows
      self.scroll_top = scroll_top

      lines_to_draw = lines[scroll_top:scroll_top+max_rows]

      for line in lines_to_draw:
          if type(line) is tuple:
              self.screen.addnstr(y, x, line[0], max_x-2, line[1])
          else:
              self.screen.addnstr(y, x, line, max_x-2)
          y += 1

      self.screen.refresh()

  def run_loop(self):
      while True:
          self.draw()
          c = self.screen.getch()
          if c in KEYS_UP:
              self.move_up()
          elif c in KEYS_DOWN:
              self.move_down()
          elif c in KEYS_ENTER:
              if self.multiselect and len(self.all_selected) < self.min_selection_count:
                  continue
              return self.get_selected()
          elif c in KEYS_SELECT and self.multiselect:
              self.mark_index()
          elif c in self.custom_handlers:
              ret = self.custom_handlers[c](self)
              if ret:
                  return ret

  def config_curses(self):
      try:
          curses.use_default_colors() # use the default colors of the terminal
          curses.curs_set(0) # hide the cursor
          curses.init_pair(1, curses.COLOR_GREEN, curses.COLOR_WHITE) # add some color for multi_select
      except:
          curses.initscr() # Curses failed to initialize color support, eg. when TERM=vt100

  def _start(self, screen):
      self.screen = screen
      self.config_curses()
      return self.run_loop()

  def start(self):
      return curses.wrapper(self._start)


def pick(*args, **kwargs):
    """Construct and start a :class:`Picker <Picker>`.

    Usage::

      >>> from pick import pick
      >>> title = 'Please choose an option: '
      >>> options = ['option1', 'option2', 'option3']
      >>> option, index = pick(options, title)
    """
    picker = Picker(*args, **kwargs)
    return picker.start()


title = 'Please choose an option: '
options = ['option1', 'option2', 'option3']
option, index = pick(options, title)