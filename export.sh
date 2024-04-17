#!/bin/bash

# Add the bin directory to the PATH
DIR_ASSISTANT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DIR_ASSISTANT_BIN="$DIR_ASSISTANT_ROOT/bin"
export PATH="$DIR_ASSISTANT_BIN:$PATH"
export DIR_ASSISTANT_ROOT
echo "dir-assistant at $DIR_ASSISTANT_BIN added to PATH"
