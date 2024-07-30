#!/bin/sh

# Ensure you first make .pypirc with appropriate tokens
#[pypi]
#  username = __token__
#  password = 
#
#[testpypi]
#  username = __token__
#  password = 

rm dist/*
pip install build twine
python -m build
python -m twine upload dist/*
