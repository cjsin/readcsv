PACKAGE_NAME := readcsv
SHELL        := bash
ACTIVATE     := source venv/bin/activate
VERSION      := $(shell tr -d ' ' < setup.cfg | awk -F= '/^version=/ {print $$2}')
DISTWHEEL    := $(PACKAGE_NAME)-$(VERSION)-py3-none-any.whl
README       := README.md
README_API   := README_api.md
SRC          := src
SOURCES      := $(wildcard $(SRC)/$(PACKAGE_NAME)/*.py)

RUN_EXAMPLES := python3 -m $(PACKAGE_NAME).examples
RUN_TESTS    := python3 -m $(PACKAGE_NAME).test_csvreader
WITH_PYPATH  := PYTHONPATH=$(PWD)/$(SRC)
WITH_VENV    := $(ACTIVATE) &&

OPTIONALS    := attrdict

all: build

version:
	@echo Package: $(PACKAGE_NAME)
	@echo Version: $(VERSION)
	@echo Wheel: $(DISTWHEEL)
	@echo Sources: $(SOURCES)

lint: venv
	$(WITH_VENV) pylint $(SRC)

doc: venv $(README)
	$(WITH_VENV) pdoc $(PACKAGE_NAME) >> $(README_API)

build-reqs: venv
	$(WITH_VENV) pip list | egrep '^build[[:space:]]' || python3 -m pip install --upgrade build

.PHONY:: build
build: build-reqs $(SOURCES)
	$(WITH_VENV) python3 -m build

clean:
	rm -rf venv build dist src/__pycache__ .pytest_cache

dist/$(DISTWHEEL): build

$(DISTWHEEL): dist/$(DISTWHEEL)
	cp dist/$@ ./

wheel: $(DISTWHEEL)

clean-venv:
	rm -rf ./venv

create-venv:
	python3 -m venv venv
	$(WITH_VENV) pip install --upgrade pip

.PHONY:: venv
venv:
	test -d venv || make create-venv
	$(WITH_VENV) pip install pylint pdoc3 build $(OPTIONALS)

venv-install: venv $(DISTWHEEL)
	$(WITH_VENV) pip install --force-reinstall $(DISTWHEEL)

run-examples:
	$(WITH_PYPATH) $(RUN_EXAMPLES)

run-tests:
	$(WITH_PYPATH) $(RUN_TESTS)

venv-run-examples: venv-install
	$(WITH_VENV) $(RUN_EXAMPLES)

venv-run-tests: venv-install
	$(WITH_VENV) $(RUN_TESTS)

venv-test: clean-venv venv-run-examples

test:
	PYTHONPATH=$(PWD)/src $(RUN_TESTS)
