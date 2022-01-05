import shutil
import pytest
import random
import atexit
import sys
import re
import contextlib
from src.interactive_path_selector import InteractivePathSelector
from src.interactive_terminal_application import InteractiveTerminalApplication

ansi_cursor_regex = re.compile(r'(\x1b\[\??[\d;]*[a-zA-Z])+', flags=re.MULTILINE)


@pytest.fixture(scope="session")
def session_tmp_path(tmp_path_factory):   # Create a standard directory hierarchy to test features
  tmp = tmp_path_factory.mktemp('tmp', numbered=False)
  (tmp/'file').touch()

  (hashes := tmp / 'hash').mkdir(parents=True, exist_ok=True)
  (hashes / random.randbytes(64).hex()).touch()

  (hidden := tmp / 'hidden').mkdir(parents=True, exist_ok=True)
  for hiddenfile in [hidden/'.1', hidden/'.2', hidden/'.3']:
    hiddenfile.touch()

  nest = tmp
  for nesting in range(8):
    nest /= 'nest'
    nest.mkdir(parents=True, exist_ok=True)
    (nest/'file').touch()

  atexit.register(lambda: shutil.rmtree(tmp.parent.absolute()))
  return tmp


def _monkeypatch_puts(s):
  sys.stdout.write(s)
  sys.stdout.flush()


@pytest.fixture(scope="function")   # Replace TUI output fd with pytest stdout to capture TUI output
def capturable_interactive_path_selector(monkeypatch, session_tmp_path):

  @contextlib.contextmanager
  def F(**kwargs):
    kwargs['root'] = session_tmp_path.absolute()
    ips = InteractivePathSelector(**kwargs)
    _puts = ips.puts
    monkeypatch.setattr(ips, "get_terminal_size", lambda *x: (40,25))
    monkeypatch.setattr(ips, "puts", lambda *x:None)
    ips.launch()
    monkeypatch.setattr(ips, "puts", _monkeypatch_puts)
    try:
      yield ips
    finally:
      monkeypatch.setattr(ips, "puts", lambda *x:None)
      ips.end(throw=False)

  return F


@pytest.fixture(scope="function")
def ANSI_capsys(monkeypatch, capsys): # regular capsys but purge ANSI cursor movement sequences
  readouterr = capsys.readouterr
  def _cleanout():
    captured = readouterr()
    cleanout = ansi_cursor_regex.sub('', captured.out).strip()
    cleanerr = ansi_cursor_regex.sub('', captured.err).strip()
    return (cleanout, cleanerr)
  monkeypatch.setattr(capsys, "readouterr", _cleanout)
  return capsys
