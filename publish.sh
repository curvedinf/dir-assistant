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

echo "Formatting code..."
./format-code.sh

echo "Running tests..."
pytest

if [ $? -ne 0 ]; then
    echo "Tests failed. Aborting publish."
    exit 1
fi

echo "Making release commit..."
RELEASE_VERSION=$(grep 'version=' setup.py | cut -d '"' -f 2)
git add .
git commit -m "Release ${RELEASE_VERSION}"
git tag "${RELEASE_VERSION}"
git push origin main
git push origin "${RELEASE_VERSION}"

echo "Cleaning up old distribution files..."
rm -rf dist

echo "Installing/upgrading build tools (build, twine, setuptools, wheel, pytest)..."
pip install --upgrade build twine setuptools wheel pytest

echo "Building the distribution..."
python -m build

echo "Verifying the distribution with twine check..."
python -m twine check dist/*

echo "Uploading the distribution to PyPI..."
python -m twine upload dist/*

echo "Publish script finished successfully."
