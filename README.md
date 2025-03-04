# dir-assistant

[![PyPI](https://img.shields.io/pypi/v/dir-assistant)](https://pypi.org/project/dir-assistant/)
[![GitHub license](https://img.shields.io/github/license/curvedinf/dir-assistant)](LICENSE)
[![GitHub last commit](https://img.shields.io/github/last-commit/curvedinf/dir-assistant)](https://github.com/curvedinf/dir-assistant/commits/main)
[![PyPI - Downloads](https://img.shields.io/pypi/dm/dir-assistant)](https://pypi.org/project/dir-assistant/)
[![GitHub stars](https://img.shields.io/github/stars/curvedinf/dir-assistant)](https://github.com/curvedinf/dir-assistant/stargazers)
[![Ko-fi Link](kofi.webp)](https://ko-fi.com/A0A31B6VB6)

Chat with your current directory's files using a local or API LLM.

![(Demo GIF of dir-assistant being run)](demo.gif)

## Summary

`dir-assistant` is a CLI python application available through `pip` that recursively indexes all text 
files in the current working directory so you can chat with them using a local or API LLM. By 
"chat with them", it is meant that their contents will automatically be included in the prompts sent 
to the LLM, with the most contextually relevant files included first. `dir-assistant` is designed 
primarily for use as a coding aid and automation tool.

### Features

- Includes an interactive chat mode and a single prompt non-interactive mode.
- When enabled, it will automatically make file updates and commit to git.
- Local platform support for CPU (OpenBLAS), Cuda, ROCm, Metal, Vulkan, and SYCL. 
- API support for all major LLM APIs. More info in the 
[LiteLLM Docs](https://docs.litellm.ai/docs/providers).
- Uses a unique method for finding the most important files to include when submitting your
prompt to an LLM called CGRAG (Contextually Guided Retrieval-Augmented Generation). You can read 
[this blog post](https://medium.com/@djangoist/how-to-create-accurate-llm-responses-on-large-code-repositories-presenting-cgrag-a-new-feature-of-e77c0ffe432d) for more information about how it works.

## Table of Contents
1. [New Features](#new-features)
   1. [Notable Upstream News](#notable-upstream-news)
3. [Quickstart](#quickstart)
    1. [Quickstart with Local Default Model](#quickstart-with-local-default-model)
    2. [Quickstart with API Model](#quickstart-with-api-model)
    3. [Quickstart Non-interactive Prompt with API Model](#quickstart-non-interactive-prompt-with-api-model)
4. [General Usage Tips](#general-usage-tips)
    1. [Optimized Settings for Coding Assistance](#optimized-settings-for-coding-assistance)
5. [Install](#install)
5. [Embedding Model Configuration](#embedding-model-configuration)
6. [Optional: Select A Hardware Platform](#optional-select-a-hardware-platform)
7. [API Configuration](#api-configuration)
   1. [Connecting to a Custom API Server](#connecting-to-a-custom-api-server). 
8. [Local LLM Model Download](#local-llm-model-download)
9. [Running](#running)
   1. [Automated file update and git commit](#automated-file-update-and-git-commit)
   2. [Additional directories](#additional-directories)
   3. [Ignoring files](#ignoring-files)
   4. [Overriding Configurations with Environment Variables](#overriding-configurations-with-environment-variables)
14. [Upgrading](#upgrading)
15. [Additional Help](#additional-help)
16. [Contributors](#contributors)
17. [Acknowledgements](#acknowledgements)
18. [Limitations](#limitations)
19. [Todos](#todos)
20. [Additional Credits](#additional-credits)

## New Features

* Added `llama-cpp-python` as an optional instead of required dependency downloadable 
with `pip install dir-assistant[recommended]`
* Official Windows support
* Custom API server connections using the new LiteLLM completion settings config section. This enables 
you to use your own GPU rig with `dir-assistant`. See 
[Connecting to a Custom API Server](#connecting-to-a-custom-api-server). 

### Notable Upstream News

This section is dedicated to changes in libraries which can impact users of `dir-assistant`.

#### llama-cpp-python

* KV cache quants now available for most models. This enables reduced memory consumption per context token.
* Improved flash attention implementation for ROCM. This drastically reduces VRAM usage for large contexts on AMD cards.

These changes allow a 32B model with 128k context to comfortably run on all GPUs with at least 20GB of VRAM if enabled.

## Quickstart

In this section are recipes to run `dir-assistant` in basic capacity to get you started quickly.

### Quickstart Chat with API Model

To get started using an API model, you can use Google Gemini 2.0 Flash, which is currently free.
To begin, you need to sign up for [Google AI Studio](https://aistudio.google.com/) and 
[create an API key](https://aistudio.google.com/app/apikey). After you create your API key,
enter the following commands:

```shell
pip install dir-assistant
dir-assistant setkey GEMINI_API_KEY xxxxxYOURAPIKEYHERExxxxx
cd directory/to/chat/with
dir-assistant
```

#### For Windows

Scripts installed with `pip` are not added to the `PATH` on Windows, but you can directly run
the `dir_assistant` module with `python`:

```shell
pip install dir-assistant
python -m dir_assistant setkey GEMINI_API_KEY xxxxxYOURAPIKEYHERExxxxx
cd directory/to/chat/with
python -m dir_assistant
```

#### For Ubuntu 24.04

`pip3` has been replaced with `pipx` starting in Ubuntu 24.04.

```shell
pipx install dir-assistant
dir-assistant setkey GEMINI_API_KEY xxxxxYOURAPIKEYHERExxxxx
cd directory/to/chat/with
dir-assistant
```

### Quickstart Chat with Local Default Model

To get started locally, you can download a default llm model. Default configuration with this model requires 
3GB of memory on most hardware. You will be able to adjust the configuration to fit higher or lower memory 
requirements. To run via CPU:

```shell
pip install dir-assistant[recommended]
dir-assistant models download-embed
dir-assistant models download-llm
cd directory/to/chat/with
dir-assistant
```

To run with hardware acceleration, use the `platform` subcommand:

```shell
...
dir-assistant platform cuda
cd directory/to/chat/with
dir-assistant
```

See which platforms are supported using `-h`:

```shell
dir-assistant platform -h
```

#### For Windows

It is not recommended to use `dir-assistant` directly with local LLMs on Windows. This is because
`llama-cpp-python` requires a C compiler for installation via pip, and setting one up is not
a trivial task on Windows like it is on other platforms. Instead, it is recommended to
use another LLM server such as LMStudio and configure `dir-assistant` to use it as
a custom API server. To do this, ensure you are installing `dir-assistant` without
the `recommended` dependencies:

```shell
pip install dir-assistant
```

Then configure `dir-assistant` to connect to your custom LLM API server:

[Connecting to a Custom API Server](#connecting-to-a-custom-api-server)

For instructions on setting up LMStudio to host an API, follow their guide:

https://lmstudio.ai/docs/app/api

Note: You can run `dir-assistant` via `python -m dir_assistant` on Windows.

#### For Ubuntu 24.04

`pip3` has been replaced with `pipx` starting in Ubuntu 24.04.

```shell
pipx install dir-assistant[recommended]
...
dir-assistant platform cuda --pipx
```

### Quickstart Non-interactive Prompt with API Model

The non-interactive mode of `dir-assistant` allows you to create scripts which analyze
your files without user interaction.

To get started using an API model, you can use Google Gemini 2.0 Flash, which is currently free.
To begin, you need to sign up for [Google AI Studio](https://aistudio.google.com/) and 
[create an API key](https://aistudio.google.com/app/apikey). After you create your API key,
enter the following commands:

```shell
pip install dir-assistant
dir-assistant setkey GEMINI_API_KEY xxxxxYOURAPIKEYHERExxxxx
cd directory/to/chat/with
dir-assistant -s "Describe the files in this directory"
```

#### For Ubuntu 24.04

`pip3` has been replaced with `pipx` starting in Ubuntu 24.04.

```shell
pipx install dir-assistant
dir-assistant setkey GEMINI_API_KEY xxxxxYOURAPIKEYHERExxxxx
cd directory/to/chat/with
dir-assistant -s "Describe the files in this directory"
```

## Install

Install with pip:

```shell
pip install dir-assistant
```

You can also install `llama-cpp-python` as an optional dependency to enable dir-assistant to
directly run local LLMs:

```shell
pip install dir-assistant[recommended]
```

_Note: `llama-cpp-python` is not updated often so may not run the latest models or have the latest
features of Llama.cpp. You may have better results with a separate local LLM server and
connect it to dir-assistant using the [custom API server](#connecting-to-a-custom-api-server)
feature._

The default configuration for `dir-assistant` is API-mode. If you download an LLM model with `download-llm`, 
local-mode will automatically be set. To change from API-mode to local-mode, set the `ACTIVE_MODEL_IS_LOCAL` setting.

#### For Ubuntu 24.04

`pip3` has been replaced with `pipx` starting in Ubuntu 24.04.

```shell
pipx install dir-assistant
```

## General Usage Tips

Dir-assistant is a powerful tool with many configuration options. This section provides some
general tips for using `dir-assistant` to achieve the best results.

### Optimized Settings for Coding Assistance

There are quite literally thousands of models that can be used with `dir-assistant`. The best results
in terms of quality for complex coding tasks on large codebases as of writing have been achieved 
with `voyage-code-3` and `gemini-2.0-flash-thinking-exp`. To use these models open the config 
file with `dir-assistant config open` and modify this optimized configuration to suit your needs:

_(Note: Don't forget to add your own API keys!)_

```toml
[DIR_ASSISTANT]
SYSTEM_INSTRUCTIONS = "You are a helpful AI assistant tasked with assisting my coding. "
GLOBAL_IGNORES = [ ".gitignore", ".d", ".obj", ".sql", "js/vendors", ".tnn", ".env", "node_modules", ".min.js", ".min.css", "htmlcov", ".coveragerc", ".pytest_cache", ".egg-info", ".git/", ".vscode/", "node_modules/", "build/", ".idea/", "__pycache__", ]
CONTEXT_FILE_RATIO = 0.9
ACTIVE_MODEL_IS_LOCAL = false
ACTIVE_EMBED_IS_LOCAL = false
USE_CGRAG = true
PRINT_CGRAG = false
OUTPUT_ACCEPTANCE_RETRIES = 2
COMMIT_TO_GIT = true
VERBOSE = false
NO_COLOR = false
LITELLM_EMBED_REQUEST_DELAY = 0
LITELLM_MODEL_USES_SYSTEM_MESSAGE = true
LITELLM_PASS_THROUGH_CONTEXT_SIZE = false
LITELLM_CONTEXT_SIZE = 30000
LITELLM_EMBED_CONTEXT_SIZE = 4000
MODELS_PATH = "~/.local/share/dir-assistant/models/"
LLM_MODEL = "agentica-org_DeepScaleR-1.5B-Preview-Q4_K_M.gguf"
EMBED_MODEL = "nomic-embed-text-v1.5.Q4_K_M.gguf"

[DIR_ASSISTANT.LITELLM_API_KEYS]
GEMINI_API_KEY = "yourkeyhere"
VOYAGE_API_KEY = "yourkeyhere"

[DIR_ASSISTANT.LITELLM_COMPLETION_OPTIONS]
model = "gemini/gemini-2.0-flash"
timeout = 600

[DIR_ASSISTANT.LITELLM_EMBED_COMPLETION_OPTIONS]
model = "voyage/voyage-code-3"
timeout = 600

[DIR_ASSISTANT.LLAMA_CPP_COMPLETION_OPTIONS]
frequency_penalty = 1.1
presence_penalty = 1.0

[DIR_ASSISTANT.LLAMA_CPP_OPTIONS]
n_ctx = 10000
verbose = false
n_gpu_layers = -1
rope_scaling_type = 2
rope_freq_scale = 0.75

[DIR_ASSISTANT.LLAMA_CPP_EMBED_OPTIONS]
n_ctx = 4000
n_batch = 512
verbose = false
rope_scaling_type = 2
rope_freq_scale = 0.75
n_gpu_layers = -1
```

## Embedding Model Configuration

You must use an embedding model regardless of whether you are running an LLM via local or API mode, but you can also
choose whether the embedding model is local or API using the `ACTIVE_EMBED_IS_LOCAL` setting. Generally local embedding 
will be faster, but API will be higher quality. To start, it is recommended to use a local model. You can download a 
good default embedding model with:

```shell
dir-assistant models download-embed
```

If you would like to use another embedding model, open the models directory with:

```shell
dir-assistant models
```

Note: The embedding model will be hardware accelerated after using the `platform` subcommand. To disable
hardware acceleration, change `n_gpu_layers = -1` to `n_gpu_layers = 0` in the config.

## Optional: Select A Hardware Platform

By default `dir-assistant` is installed with CPU-only compute support. It will work properly without this step,
but if you would like to hardware accelerate `dir-assistant`, use the command below to compile 
`llama-cpp-python` with your hardware's support.

```shell
dir-assistant platform cuda
```

Available options: `cpu`, `cuda`, `rocm`, `metal`, `vulkan`, `sycl`

Note: The embedding model and the local llm model will be run with acceleration after selecting a platform. To disable 
hardware acceleration change `n_gpu_layers = -1` to `n_gpu_layers = 0` in the config.

#### For Ubuntu 24.04

`pip3` has been replaced with `pipx` starting in Ubuntu 24.04.

```shell
dir-assistant platform cuda --pipx
```

### For Platform Install Issues

System dependencies may be required for the `platform` command and are outside the scope of these instructions.

If you have any issues building `llama-cpp-python`, the project's install instructions may offer more 
info: https://github.com/abetlen/llama-cpp-python

## API Configuration

If you wish to use an API LLM, you will need to configure it. To configure which LLM API 
dir-assistant uses, you must edit `LITELLM_MODEL` and the appropriate API key in your configuration. To open 
your configuration file, enter:

```shell
dir-assistant config open
```

Once editing the file, change:

```toml
[DIR_ASSISTANT]
LITELLM_CONTEXT_SIZE = 200000

[DIR_ASSISTANT.LITELLM_API_KEYS]
GEMINI_API_KEY = "xxxxxxxxxxxxxxxxxxx"

[DIR_ASSISTANT.LITELLM_COMPLETION_OPTIONS]
model = "gemini/gemini-2.0-flash-latest"
```

LiteLLM supports all major LLM APIs, including APIs hosted locally. View the available options in the 
[LiteLLM providers list](https://docs.litellm.ai/docs/providers).

There is a convenience subcommand for modifying and adding API keys:

```shell
dir-assistant setkey GEMINI_API_KEY xxxxxYOURAPIKEYHERExxxxx
```

However, in most cases you will need to modify other options when changing APIs.

### Connecting to a Custom API Server

If you would like to connect to a custom API server, such as your own ollama, llama.cpp, LMStudio, 
vLLM, or other OpenAPI-compatible API server, dir-assistant supports this. To configure for this,
open the config with `dir-assistant config open` and make following changes (LMStudio's base_url
shown for the example):

```toml
[DIR_ASSISTANT]
ACTIVE_MODEL_IS_LOCAL = false

[DIR_ASSISTANT.LITELLM_COMPLETION_OPTIONS]
model = "openai/mistral-small-24b-instruct-2501"
base_url = "http://localhost:1234/v1"
```

## Local LLM Model Download

If you want to use a local LLM directly within `dir-assistant` using `llama-cpp-python`, 
you can download a low requirements default model with:

```shell
dir-assistant models download-llm
```

Note: The local LLM model will be hardware accelerated after using the `platform` subcommand. To disable hardware
acceleration, change `n_gpu_layers = -1` to `n_gpu_layers = 0` in the config.

### Configuring A Custom Local Model

If you would like to use a custom local LLM model, download a GGUF model and place it in your models
directory. [Huggingface](https://huggingface.co/models) has numerous GGUF models to choose from. The models 
directory can be opened in a file browser using this command:

```shell
dir-assistant models
```

After putting your gguf in the models directory, you must configure dir-assistant to use it:

```shell
dir-assistant config open
```

Edit the following setting:

```shell
[DIR_ASSISTANT]
LLM_MODEL = "Mistral-Nemo-Instruct-2407.Q6_K.gguf"
```

### Llama.cpp Options

Llama.cpp provides a large number of options to customize how your local model is run. Most of these options are
exposed via `llama-cpp-python`. You can configure them with the `[DIR_ASSISTANT.LLAMA_CPP_OPTIONS]`, 
`[DIR_ASSISTANT.LLAMA_CPP_EMBED_OPTIONS]`, and `[DIR_ASSISTANT.LLAMA_CPP_COMPLETION_OPTIONS]` sections in the 
config file.

The options available for `llama-cpp-python` are documented in the
[Llama constructor documentation](https://llama-cpp-python.readthedocs.io/en/latest/api-reference/#llama_cpp.Llama).

What the options do is also documented in the 
[llama.cpp CLI documentation](https://github.com/ggerganov/llama.cpp/blob/master/examples/main/README.md).

The most important `llama-cpp-python` options are related to tuning the LLM to your system's VRAM:

* Setting `n_ctx` lower will reduce the amount of VRAM required to run, but will decrease the amount of 
file text that can be included when running a prompt.
* `CONTEXT_FILE_RATIO` sets the proportion of prompt history to file text to be included when sent to the LLM. 
Higher ratios mean more file text and less prompt history. More file text generally improves comprehension.
* If your llm `n_ctx` times `CONTEXT_FILE_RATIO` is smaller than your embed `n_ctx`, your file text chunks 
have the potential to be larger than your llm context, and thus will not be included. To ensure all files 
can be included, make sure your embed context is smaller than `n_ctx` times `CONTEXT_FILE_RATIO`.
* Larger embed `n_ctx` will chunk your files into larger sizes, which allows LLMs to understand them more
easily.
* `n_batch` must be smaller than the `n_ctx` of a model, but setting it higher will probably improve
performance.

For other tips about tuning Llama.cpp, explore their documentation and do some google searches.

## Running

```shell
dir-assistant
```

Running `dir-assistant` will scan all files recursively in your current directory. The most relevant files will 
automatically be sent to the LLM when you enter a prompt.

`dir-assistant` is shorthand for `dir-assistant start`. All arguments below are applicable for both.

#### Options for Running

The following arguments are available while running `dir-assistant`:

- `-i --ignore`: A list of space-separated filepaths to ignore
- `-d --dirs`: A list of space-separated directories to work on (your current directory will always be used)
- `-s --single-prompt`: Run a single prompt and output the final answer
- `-v --verbose`: Show debug information during execution

Example usage:

```shell
# Run a single prompt and exit
dir-assistant -s "What does this codebase do?"

# Show debug information
dir-assistant -v

# Ignore specific files and add additional directories
dir-assistant -i ".log" ".tmp" -d "../other-project"
```

### Automated file update and git commit
The `COMMIT_TO_GIT` feature allows `dir-assistant` to make changes directly to your files and commit the changes to git
during the chat. By default, this feature is disabled, but after enabling it, the assistant will suggest file changes 
and ask whether to apply the changes. If confirmed, it stages the changes and creates a git commit with the prompt 
message as the commit message.

To enable the `COMMIT_TO_GIT` feature, update the configuration:

```shell
dir-assistant config open
```

Change or add the following setting:

```toml
[DIR_ASSISTANT]
...
COMMIT_TO_GIT = true
```

Once enabled, the assistant will handle the Git commit process as part of its workflow. To undo a commit,
type `undo` in the prompt.

### Additional directories

You can include files from outside your current directory to include in your `dir-assistant` session:

```shell
dir-assistant -d /path/to/dir1 ../dir2
```

### Ignoring files

You can ignore files when starting up so they will not be included in the assistant's context:

```shell
dir-assistant -i file.txt file2.txt
```

There is also a global ignore list in the config file. To configure it first open the config file:

```shell
dir-assistant config open
```

Then edit the setting:

```toml
[DIR_ASSISTANT]
...
GLOBAL_IGNORES = [
    ...
    "file.txt"
]
```

### Overriding Configurations with Environment Variables

Any configuration setting can be overridden using environment variables. The environment variable name should match the configuration key name:

```shell
# Override the model path
export DIR_ASSISTANT__LLM_MODEL="mistral-7b-instruct.Q4_K_M.gguf"

# Enable git commits
export DIR_ASSISTANT__COMMIT_TO_GIT=true

# Change context ratio
export DIR_ASSISTANT__CONTEXT_FILE_RATIO=0.7

# Change llama.cpp embedding options
export DIR_ASSISTANT__LLAMA_CPP_EMBED_OPTIONS__n_ctx=2048

# Example setting multiple env vars inline with the command
DIR_ASSISTANT__COMMIT_TO_GIT=true DIR_ASSISTANT__CONTEXT_FILE_RATIO=0.7 dir-assistant
```

This allows multiple config profiles for your custom use cases.

```shell
# Run with different models
DIR_ASSISTANT__LLM_MODEL="model1.gguf" dir-assistant -s "What does this codebase do?"
DIR_ASSISTANT__LLM_MODEL="model2.gguf" dir-assistant -s "What does this codebase do?"

# Test with different context ratios
DIR_ASSISTANT__CONTEXT_FILE_RATIO=0.8 dir-assistant
```
## Upgrading

Some version upgrades may have incompatibility issues in the embedding index cache. Use this command to delete the
index cache so it may be regenerated:

```shell
dir-assistant clear
```

## Additional Help

Use the `-h` argument with any command or subcommand to view more information. If your problem is beyond the scope of
the helptext, please report a github issue.

## Contributors

We appreciate contributions from the community! For a list of contributors and how you can contribute,
please see [CONTRIBUTORS.md](CONTRIBUTORS.md).

## Acknowledgements

- Local LLMs are run via the fantastic [llama-cpp-python](https://github.com/abetlen/llama-cpp-python) package
- API LLMS are run using the also fantastic [LiteLLM](https://github.com/BerriAI/litellm) package

## Limitations

- Dir-assistant only detects and reads text files at this time.

## Todos

- ~~API LLMs~~
- ~~RAG~~
- ~~File caching (improve startup time)~~
- ~~CGRAG (Contextually-Guided Retrieval-Augmented Generation)~~
- ~~Multi-line input~~
- ~~File watching (automatically reindex changed files)~~
- ~~Single-step pip install~~
- ~~Model download~~
- ~~Commit to git~~
- ~~API Embedding models~~
- ~~Immediate mode for better compatibility with custom script automations~~
- ~~Support for custom APIs~~
- Web search
- Daemon mode for API-based use

## Additional Credits

Special thanks to [Blazed.deals](https://blazed.deals) for sponsoring this project.
