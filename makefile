.DEFAULT_GOAL := default
.PHONY = default all clean compile install buildext

PYTHON3="python"
PIP3="pip"

default: clean compile
all: clean compile install
upload: clean sdist

clean:
	@echo '[make clean]'
	@rm -rf build dist *.egg-info */*__pycache__ */*/*__pycache__

compile:
	@echo '[make compile]'
	@python setup.py bdist_wheel

install:
	@echo '[make install]'
	${PIP3} install dist/*.whl --force-reinstall --no-deps

sdist:
	@echo '[make upload]'
	@python setup.py sdist
	@twine upload dist/*.gz
