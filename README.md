# dir-assistant
A minimal CLI LLM assistant that allows you to chat with the current directory's files.

This project runs LLMs via the fantastic [llama-cpp-python](https://github.com/abetlen/llama-cpp-python) package.

## Setup

Install `pyenv` if you have not already: https://github.com/pyenv/pyenv-installer

Then run:
```
./setup.sh
```

CMAKE_ARGS="-DCMAKE_HIP_PLATFORM=amd" pip install llama-cpp-python
CMAKE_ARGS="-DCMAKE_HIP_PLATFORM=nvidia" pip install llama-cpp-python

## Model Download

Download your favorite LLM gguf and place it in the models directory.

## Configure

This script should be run once when you first install `dir-assistant`, and then again whenever you would
like to modify its configuration:

```
./config.sh
```

Alternatively you can edit `config.json` once it is created.

## Run

First export the necessary environment variables at the start of every terminal session
(this script can be added to your `.bashrc`):

```
soruce /path-to/dir-assistant/export.sh
```

Then navigate to the directory you would like your LLM to see and run dir-assistant:

```
dir-assistant
```

## Limitations

- This project uses a naive approach for including files in the current working directory. For this reason, it will only work well with projects that can be contained in your LLM's context window.

## Recommended Models

- [CodeQwen 1.5 7B Chat](https://huggingface.co/Qwen/CodeQwen1.5-7B-Chat-GGUF): This is an excellent coding model with an extremely accurate 64K token context window. It should work well with projects under 5k lines of code.