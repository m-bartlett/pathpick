# https://makefiletutorial.com
.PHONY: all run clean uninstall

TARGET := pathpick
SHELL := /bin/bash

PREFIX ?= /usr/local
PYTHON ?= /usr/bin/env python

BUILD_DIR := app
SOURCE_DIR := src

SRC := $(shell find $(SOURCE_DIR) -type f)

all: $(TARGET)

run:
	$(PYTHON) -m $(SOURCE_DIR)

clean:
	$(PYTHON) setup.py clean
	find . -type f -name '*.pyc' -delete
	rm -rfv \
		__pycache__               \
		.pytest_cache             \
		build                     \
		dist                      \
		*.egg-info                \
		$(SOURCE_DIR)/__pycache__ \
		$(SOURCE_DIR)/*.egg-info  \
		$(BUILD_DIR)              \
		$(TARGET)

setupinstall: clean
	$(PYTHON) setup.py install

pipinstall: clean
	pip install -U . --use-feature=in-tree-build

$(TARGET): $(SRC)
	mkdir -p $(BUILD_DIR)
	cp -r $(SOURCE_DIR) $(BUILD_DIR)/$(TARGET)
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