#!/bin/sh
# Ensure you first make .pypirc with appropriate tokens
#[pypi]
#  username = __token__
#  password =
#
#[testpypi]
#  username = __token__
#  password =

# Exit immediately if a command exits with a non-zero status.
set -e

echo "Cleaning up old distribution files..."
rm -rf dist

echo "Installing/upgrading build tools (build, twine, setuptools, wheel)..."
pip install --upgrade build twine setuptools wheel

echo "Building the distribution..."
python -m build

echo "Verifying the distribution with twine check..."
python -m twine check dist/*

echo "Uploading the distribution to PyPI..."
python -m twine upload dist/*

echo "Publish script finished successfully."
