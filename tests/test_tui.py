from .core import *


def test_basic_selection(session_tmp_path):
  ips = InteractivePathSelector( root=session_tmp_path.absolute(),
                                 show_hidden=True,
                                 dirs_first =False )
  ips.launch()
  ips.toggle_selected()
  ips.end(throw=False)
  assert ips.get_selection_paths()[0] == str(session_tmp_path / 'file')
  assert ips.get_selection_dict() == {'file': True}


def test_toggle_selected(capturable_interactive_path_selector, ANSI_capsys):
  with capturable_interactive_path_selector() as ips:
    ips.selection={}
    ips.subselection=ips.selection
    ips.toggle_selected()
    ips.toggle_selected()
  out, err = ANSI_capsys.readouterr()
  assert out == '> +file> file'


def test_draw_page(capturable_interactive_path_selector, ANSI_capsys):
  with capturable_interactive_path_selector() as ips:
    ips.selection={}
    ips.subselection=ips.selection
    ips.draw_page()
  out, err = ANSI_capsys.readouterr()
  assert '1/4\n file\n hash/\n hidden/\n nest/> file' in out


def test_truncating_paths(capturable_interactive_path_selector, ANSI_capsys):
  with capturable_interactive_path_selector() as ips:
    ips.row_down()
    ips.select_or_descend()
  out, err = ANSI_capsys.readouterr()
  assert out.endswith('...')


def test_truncating_header(capturable_interactive_path_selector, ANSI_capsys):
  with capturable_interactive_path_selector(dirs_first=True) as ips:
    ips.row_down()
    ips.row_down()
    for i in range(9):
      ips.select_or_descend()
    ips.draw_header_info()
  out, err = ANSI_capsys.readouterr()
  assert out.endswith('...t/nest/nest/nest/nest/nest/nest   1/1')


def test_hidden_false(capturable_interactive_path_selector, ANSI_capsys):
  with capturable_interactive_path_selector(show_hidden=False) as ips:
    ips.selection={}
    ips.subselection=ips.selection

    ips.row_down()
    ips.row_down()
    ips.select_or_descend()
    ips.select_or_descend()

  out, err = ANSI_capsys.readouterr()
  assert ips.subselection == {}
  assert ips.get_selection_dict() == {}
  assert 'hidden' in out
  assert '0/0' in out


def test_hidden_true(capturable_interactive_path_selector, ANSI_capsys):
  with capturable_interactive_path_selector(show_hidden=True) as ips:
    ips.selection={}
    ips.subselection=ips.selection

    ips.row_down()
    ips.row_down()
    ips.select_or_descend()
    ips.select_or_descend()
    ips.row_down()
    ips.select_or_descend()
    ips.row_down()
    ips.select_or_descend()

  out, err = ANSI_capsys.readouterr()
  assert ips.subselection == {'.1':True,'.2':True,'.3':True}
  assert ips.get_selection_dict() == {'hidden':{'.1':True,'.2':True,'.3':True}}
  assert 'hidden' in out
  assert all(s in out for s in ['.1', '.2', '.3'])


def test_dir_first_false(capturable_interactive_path_selector, ANSI_capsys):
  with capturable_interactive_path_selector(dirs_first=False) as ips:
    ips.selection={}
    ips.subselection=ips.selection
    ips.select_or_descend()
  out, err = ANSI_capsys.readouterr()
  assert out == '> +file'


def test_dir_first_true(capturable_interactive_path_selector, ANSI_capsys):
  with capturable_interactive_path_selector(dirs_first=True) as ips:
    ips.selection={}
    ips.subselection=ips.selection
    ips.select_or_descend()
  out, err = ANSI_capsys.readouterr()
  assert out != '> +file'
  assert 'hash' in out


def test_alt_style(capturable_interactive_path_selector, ANSI_capsys):
  style = { 'active':     {'prefix': '-->', 'suffix': '<--'},
            'inactive':   {'prefix': '<--', 'suffix': '-->'},
            'unselected': {'prefix': '?', 'suffix': '?'},
            'selected':   {'prefix': '!', 'suffix': '!'}}
  with capturable_interactive_path_selector( dirs_first=False,
                                             style=style ) as ips:
    ips.selection={}
    ips.subselection=ips.selection
    ips.refresh()
    ips.select_or_descend()
    ips.row_down()
    ips.toggle_selected()
  out, err = ANSI_capsys.readouterr()
  assert all( s in out for s in [ '-->?file?<--',
                                  '-->!file!<--',
                                  '<--!file!-->',
                                  '<--?hash/?-->',
                                  '<--?hidden/?-->',
                                  '-->?hash/?<--',
                                  '-->!hash/!<--' ] )


def test_keybind_toggle_all_selected(capturable_interactive_path_selector, ANSI_capsys):
  with capturable_interactive_path_selector() as ips:
    ips.toggle_all_selected()
  out, err = ANSI_capsys.readouterr()
  assert all(s in out for s in ['+file','+hash','+hidden','+nest'])
  assert ips.get_selection_dict() == {'hash':True,'nest':True,'file':True,'hidden':True}


def test_keybind_toggle_show_dirs_first(capturable_interactive_path_selector, ANSI_capsys):
  with capturable_interactive_path_selector(dirs_first=False) as ips:
    ips.selection={}
    ips.subselection=ips.selection
    ips.draw_page()
    ips.toggle_show_dirs_first()
  out, err = ANSI_capsys.readouterr()
  out = out.replace('\n','')
  assert 'file hash/ hidden/ nest/' in out
  assert 'hash/ hidden/ nest/ file' in out


def test_keybind_toggle_show_hidden(capturable_interactive_path_selector, ANSI_capsys):
  with capturable_interactive_path_selector(show_hidden=False) as ips:
    ips.selection={}
    ips.subselection=ips.selection
    ips.row_down()
    ips.row_down()
    ips.select_or_descend()
    ips.select_or_descend()
    ips.toggle_show_hidden()
    ips.select_or_descend()
  out, err = ANSI_capsys.readouterr()
  assert all(s in out for s in ['.1', '.2', '.3'])
  assert out.endswith('> +.1')


def test_keybind_refresh_manual(capturable_interactive_path_selector, ANSI_capsys, session_tmp_path):
  new = session_tmp_path/'new'
  with capturable_interactive_path_selector() as ips:
    ips.selection={}
    ips.subselection=ips.selection
    ips.draw_page()
    new.touch()
    ips.refresh_manual()
    new.unlink()
  out, err = ANSI_capsys.readouterr()
  out = out.replace('\n','')
  assert 'file hash/ hidden/ nest/>' in out
  assert 'file hash/ hidden/ nest/ new>' in out