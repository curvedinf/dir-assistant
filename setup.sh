#!/bin/sh

# Requires pyenv to be installed: https://github.com/pyenv/pyenv-installer
if command -v pyenv 1>/dev/null 2>&1; then
    eval "$(pyenv init -)"
    eval "$(pyenv virtualenv-init -)"
fi
pyenv install 3.11 -s
pyenv virtualenv 3.11 dir-assistant
pyenv activate dir-assistant
pip install --upgrade pip

echo "Select platform to use:"
echo "1) CPU"
echo "2) Nvidia"
echo "3) AMD"
read platform

case $platform in
    1)
        pip install --upgrade --force-reinstall --no-cache-dir -r requirements.txt
        ;;
    2)
        CMAKE_ARGS="-DCMAKE_HIP_PLATFORM=nvidia" pip install --upgrade --force-reinstall --no-cache-dir -r requirements.txt
        ;;
    3)
        CMAKE_ARGS="-DCMAKE_HIP_PLATFORM=amd" pip install --upgrade --force-reinstall --no-cache-dir -r requirements.txt
        ;;
    *)
        echo "Invalid option. Exiting."
        exit 1
        ;;
esac
