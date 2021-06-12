PACKAGE_NAME := readcsv
SHELL        := bash
VENV         := venv
ACTIVATE     := source $(VENV)/bin/activate
VERSION      := $(shell tr -d ' ' < setup.cfg | awk -F= '/^version=/ {print $$2}')
DISTWHEEL    := $(PACKAGE_NAME)-$(VERSION)-py3-none-any.whl
README       := README.md
README_API   := README_api.md
SRC          := src
SOURCES      := $(wildcard $(SRC)/$(PACKAGE_NAME)/*.py)
PYVER        := 3.9
PYTHON       := python$(PYVER)
RUN_PY_MOD   := $(PYTHON) -m
RUN_TESTS    := $(RUN_PY_MOD) $(PACKAGE_NAME).test_csvreader
WITH_VENV    := $(ACTIVATE) &&
PIP_INSTALL  := $(WITH_VENV) pip install
OPTIONALS    := attrdict
MD_VIEWER    := retext
DOCS_INDEX   := docs/html/$(PACKAGE_NAME)/index.html

# Macros for use in path generation
space :=
space +=
comma = ,
colon = :
join-with = $(subst $(space),$1,$(strip $2))
path-gen  = $(join-with $(colon),$1)

RUN_MAIN       := $(RUN_PY_MOD) $(PACKAGE_NAME)
RUN_EXAMPLE1   := $(RUN_PY_MOD) $(PACKAGE_NAME).examples

RUN_EXAMPLES   := ( $(RUN_EXAMPLE1 )
WITH_PYPATH    := PYTHONPATH=$(PWD)/$(SRC)

PYLINT_DISABLED := \
    invalid-name,too-many-branches,line-too-long
PYLINT_FLAGS := -d $(subst $(space),$(comma),$(PYLINT_DISABLED))

CLEAN_PATTERNS := \
    build \
    dist \
    src/$(PACKAGE_NAME)/__pycache__ \
    .pytest_cache \
    *.whl \
    src/*.egg-info

all: build

version:
	@echo Package: $(PACKAGE_NAME)
	@echo Version: $(VERSION)
	@echo Wheel:   $(DISTWHEEL)
	@echo Sources: $(SOURCES)

lint: venv
	$(WITH_VENV) pylint $(PYLINT_FLAGS) $(SRC)

$(README_API): venv $(SOURCES)
	$(WITH_VENV) $(WITH_PYPATH) pdoc $(PACKAGE_NAME) > $(README_API)

docs-html: venv
	mkdir -p docs
	$(WITH_VENV) $(WITH_PYPATH) pdoc --html -o docs/html $(PACKAGE_NAME)

docs: $(README_API) clean-docs docs-html

view-docs: docs
	command -v $(MD_VIEWER) && $(MD_VIEWER) README*.md || echo "Markdown viewer not installed" &
	xdg-open file://$(PWD)/$(DOCS_INDEX) &

build-reqs: venv
	($(WITH_VENV) pip list | egrep '^build[[:space:]]') || ( $(PIP_INSTALL) --upgrade build )

.PHONY:: build
build: build-reqs
	$(WITH_VENV) python3 -m build

.PHONY:: dist
dist: $(DISTWHEEL)
dist/$(DISTWHEEL): build

$(DISTWHEEL): dist/$(DISTWHEEL)
	cp dist/$(DISTWHEEL) ./

wheel: $(DISTWHEEL)

clean: clean-docs clean-venv
	rm -rf $(CLEAN_PATTERNS)

clean-docs:
	rm -rf ./docs

clean-venv:
	rm -rf ./$(VENV)

create-venv:
	$(PYTHON) -m venv $(VENV)
	$(PIP_INSTALL) --upgrade pip
	$(PIP_INSTALL) pylint pdoc3 build pytest $(OPTIONALS)

.PHONY:: venv
venv:
	test -d $(VENV) || make create-venv

venv-install: venv $(DISTWHEEL)
	$(PIP_INSTALL) --force-reinstall $(DISTWHEEL)

venv-run-example1: venv-install
	$(WITH_VENV) $(RUN_EXAMPLE1)

venv-run-examples: venv-run-example1

venv-run-tests: venv-install
	$(WITH_VENV) $(RUN_TESTS)

venv-test: clean-venv venv-run-examples venv-run-tests

examples: example1

example1:
	$(WITH_PYPATH) $(RUN_EXAMPLE1)

test: venv
	$(WITH_VENV) $(WITH_PYPATH) $(RUN_TESTS)

run: examples

test-targets1: clean-docs clean-venv clean
test-targets2: docs clean-docs clean
test-targets3: build wheel venv-install clean
test-targets4: venv-run-tests venv-run-examples clean
test-targets5: test examples clean

test-makefile-targets:
	for n in $$(seq 1 5) ; do make test-targets$$n || exit 1; done
	echo all targets completed successfully
