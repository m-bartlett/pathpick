.PHONY: all run clean uninstall

PREFIX ?= /usr/local
PYTHON ?= /usr/bin/env python

TARGET := pathpick
SHELL := /bin/bash
BUILD_DIR := app

all: $(TARGET)

run:
	$(PYTHON) -m src

clean:
	$(PYTHON) setup.py clean
	find . -type f -name '*.pyc' -delete
	rm -rf __pycache__ build dist *.egg-info  src/__pycache__ src/*.egg-info app $(TARGET)

setupinstall: clean
	$(PYTHON) setup.py install

pipinstall: clean
	pip install -U . --use-feature=in-tree-build

$(TARGET):
	mkdir -p $(BUILD_DIR)
	cp -r src $(BUILD_DIR)/$(TARGET)
	$(PYTHON) -m zipapp \
		$(BUILD_DIR) \
		--main $(TARGET).__main__:main \
		--python $(shell which python) \
		--output $(TARGET) \
		--compress
	rm -rf $(BUILD_DIR)

app: $(TARGET)

install: $(TARGET)
	install -m 755 $(TARGET) $(PREFIX)/bin/$(TARGET)
	make clean

uninstall:
	rm $(PREFIX)/bin/$(TARGET)