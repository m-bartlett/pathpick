.PHONY: all run clean uninstall

SHELL := /bin/bash
TARGET := pathpick
BUILD_DIR := app
PREFIX ?= /usr/local

all: $(TARGET)

run:
	python -m src

clean:
	python setup.py clean
	find . -type f -name '*.pyc' -delete
	rm -rf __pycache__ build dist *.egg-info  src/__pycache__ src/*.egg-info app $(TARGET)

setupinstall: clean
	python setup.py install

pipinstall: clean
	pip install -U . --use-feature=in-tree-build

$(TARGET):
	mkdir -p $(BUILD_DIR)
	cp -r src $(BUILD_DIR)/$(TARGET)
	python -m zipapp \
		$(BUILD_DIR) \
		--main pathpick.__main__:main \
		--python $(shell which python) \
		--output $(TARGET) \
		--compress
	rm -rf $(BUILD_DIR)

app: $(TARGET)

install: $(TARGET)
	install -m 755 $(TARGET) $(PREFIX)/bin/$(TARGET)

uninstall:
	install -m 755 $(TARGET) $(PREFIX)/bin/$(TARGET)