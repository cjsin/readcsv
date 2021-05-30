PACKAGE_NAME := readcsv
SHELL        := bash
ACTIVATE     := source venv/bin/activate
VERSION      := $(shell tr -d ' ' < setup.cfg | awk -F= '/^version=/ {print $$2}')
DISTWHEEL    := $(PACKAGE_NAME)-$(VERSION)-py3-none-any.whl
README       := README.md
SRC          := src
SOURCES      := $(wildcard $(SRC)/$(PACKAGE_NAME)/*.py)

all: build

version:
	@echo Package: $(PACKAGE_NAME)
	@echo Version: $(VERSION)
	@echo Wheel: $(DISTWHEEL)
	@echo Sources: $(SOURCES)

lint:
	pylint-3 src

doc: $(README)
	pdoc $(PACKAGE_NAME) > $(README)

build-reqs:
	pip list | egrep '^build[[:space:]]' || python3 -m pip install --upgrade build

.PHONY:: build
build: build-reqs $(SOURCES)
	python3 -m build

clean:
	rm -rf venv build dist src/__pycache__ .pytest_cache

dist/$(DISTWHEEL): build

$(DISTWHEEL): dist/$(DISTWHEEL)
	cp dist/$@ ./

wheel: $(DISTWHEEL)

clean-venv:
	rm -rf ./venv

.PHONY:: venv
venv:
	python3 -m venv venv
	$(ACTIVATE) && pip install --upgrade pip

venv-install: venv $(DISTWHEEL)
	$(ACTIVATE) && pip install --force-reinstall $(DISTWHEEL)

venv-run-examples: venv-install
	$(ACTIVATE) && python3 -m $(PACKAGE_NAME).examples

venv-run-tests: venv-install
	$(ACTIVATE) && python3 -m $(PACKAGE_NAME).test_csvreader

venv-test: clean-venv venv-run-examples

test:
	PYTHONPATH=$(PWD)/src python3 -m $(PACKAGE_NAME).test_csvreader
