#!/bin/bash

if command -v pyenv 1>/dev/null 2>&1; then
    eval "$(pyenv init -)"
    eval "$(pyenv virtualenv-init -)"
fi
pyenv activate dir-assistant
DIR_ASSISTANT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
python $DIR_ASSISTANT_ROOT/config.py