<p align="center">
  <img 
    title="pathpick logo"
    alt="pathpick logo"
    align="center"
    height="100"
    src="https://user-images.githubusercontent.com/85039141/147019614-a3dcfa9f-dace-4909-964d-e2af8da36290.png#gh-light-mode-only"
  >
  <img
    title="pathpick logo"
    alt="pathpick logo"
    align="center"
    height="100"
    src="https://user-images.githubusercontent.com/85039141/147019574-a416d0d8-2289-4b00-998d-06950e36424f.png#gh-dark-mode-only"
  >
  <br/><br/>Interactive filesystem path selector TUI
</p>

## About

## Usage

### Examples


## Dependencies
- python >= 3.7.0
- python standard library
- GNU Make _(optional)_
- pytest _(optional, for running tests)_

## Install

### Standalone Executable Zipped App

**This method does not make any changes to your python site packages.**

This installation method uses the `zipapp` module. Python can execute a zip of python files so long as the first bytes of the zip are a hashbang (e.g. `#!/usr/bin/python`) and the zip has the executable bit set.

To install an executable named `pathpick` to `/usr/local/bin/` by default, run:

    make install

Modify the `PREFIX` environment variable to change this:

    PREFIX=~/.local make install

Ensure `$PREFIX/bin` is in your `$PATH` for easy execution, and verify such with:

    pathpick --version

### Python Module

#### pip (Not on PyPI as of writing)
To install with pip run either

    pip install . --use-feature=in-tree-build

or alternatively

    make pipinstall

#### setuptools
To install with setup.py run either

    python setup.py install

or alternatively

    make setupinstall


## Customization
  - --config
  - config.ini

## Tests
If you have pytest installed, simply execute `pytest` in the root of this repository.

Alternatively, try `make test` to install pytest to a temporary python virtual environment, execute `pytest` from this virtual environment, and destroy the virtual environment after the testing is completed.

## References
- gist on how to create [Python zipapp web apps](https://gist.github.com/lukassup/cf289fdd39124d5394513a169206631c)
- https://makefiletutorial.com
