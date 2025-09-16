# Usage

This document provides a guide to using `dir-assistant`, including quickstart examples, general tips, and advanced usage scenarios.

## Table of Contents
1. [Quickstart](#quickstart)
   - [Chat with Local Default Model](#quickstart-chat-with-local-default-model)
   - [Chat with API Model (Google Gemini)](#quickstart-chat-with-api-model-google-gemini)
   - [Chat with API Model (Anthropic Claude)](#quickstart-chat-with-api-model-anthropic-claude)
   - [Chat with API Model (OpenAI)](#quickstart-chat-with-api-model-openai)
   - [Non-interactive Prompt with API Model](#quickstart-non-interactive-prompt-with-api-model)
2. [Running `dir-assistant`](#running)
   - [Options for Running](#options-for-running)
   - [Automated File Update and Git Commit](#automated-file-update-and-git-commit)
   - [Additional Directories](#additional-directories)
   - [Ignoring Files](#ignoring-files)
   - [Overriding Configurations with Environment Variables](#overriding-configurations-with-environment-variables)
3. [General Usage Tips](#general-usage-tips)
   - [Optimized Settings for Coding Assistance](#optimized-settings-for-coding-assistance)
4. [Examples](#examples)

---

## Quickstart
In this section are recipes to run `dir-assistant` in basic capacity to get you started quickly.
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
[Connecting to a Custom API Server](configuration.md#connecting-to-a-custom-api-server)
For instructions on setting up LMStudio to host an API, follow their guide:
https://lmstudio.ai/docs/app/api
#### For Ubuntu 24.04
`pip3` has been replaced with `pipx` starting in Ubuntu 24.04.
```shell
pipx install dir-assistant[recommended]
...
dir-assistant platform cuda --pipx
```
### Quickstart Chat with API Model (Google Gemini)
To get started using an API model, you can use Google Gemini 1.5 Flash, which is currently free.
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
Note: The [Python.org](https://python.org) installer is recommended for Windows. The Windows
Store installer does not add dir-assistant to your PATH so you will need to call it
with `python -m dir_assistant` if you decide to go that route.
```shell
pip install dir-assistant
dir-assistant setkey GEMINI_API_KEY xxxxxYOURAPIKEYHERExxxxx
cd directory/to/chat/with
dir-assistant
```
#### For Ubuntu 24.04
`pip3` has been replaced with `pipx` starting in Ubuntu 24.04.
```shell
pipx install dir-assistant
dir-assistant setkey GEMINI_API_KEY xxxxxYOURAPIKEYHERExxxxx
cd directory/to/chat/with
dir-assistant
```
### Quickstart Chat with API Model (Anthropic Claude)
To get started quickly with Anthropic's Claude models (e.g., Claude 3.7 Sonnet):
1.  Obtain an API key from [Anthropic](https://console.anthropic.com/).
2.  Install `dir-assistant` and set your API key:
    ```shell
    pip install dir-assistant
    dir-assistant setkey ANTHROPIC_API_KEY xxxxxYOURAPIKEYHERExxxxx
    ```
3.  Configure `dir-assistant` to use Claude. Open the config file with `dir-assistant config open` and make sure these settings are present:
    ```toml
    [DIR_ASSISTANT]
    ACTIVE_MODEL_IS_LOCAL = false
    LITELLM_MODEL_USES_SYSTEM_MESSAGE = true
    LITELLM_CONTEXT_SIZE = 200000
    [DIR_ASSISTANT.LITELLM_COMPLETION_OPTIONS]
    model = "anthropic/claude-3-7-sonnet-20240729"
    ```
4.  Navigate to your project directory and run:
    ```shell
    cd directory/to/chat/with
    dir-assistant
    ```
#### For Windows (Claude)
```shell
pip install dir-assistant
dir-assistant setkey ANTHROPIC_API_KEY xxxxxYOURAPIKEYHERExxxxx
# Then, configure the model as shown above using 'dir-assistant config open'
cd directory/to/chat/with
dir-assistant
```
#### For Ubuntu 24.04 (Claude)
```shell
pipx install dir-assistant
dir-assistant setkey ANTHROPIC_API_KEY xxxxxYOURAPIKEYHERExxxxx
# Then, configure the model as shown above using 'dir-assistant config open'
cd directory/to/chat/with
dir-assistant
```
### Quickstart Chat with API Model (OpenAI)
To get started quickly with OpenAI's models (e.g., GPT-4o):
1.  Obtain an API key from [OpenAI](https://platform.openai.com/api-keys).
2.  Install `dir-assistant` and set your API key:
    ```shell
    pip install dir-assistant
    dir-assistant setkey OPENAI_API_KEY xxxxxYOURAPIKEYHERExxxxx
    ```
3.  Configure `dir-assistant` to use an OpenAI model. Open the config file with `dir-assistant config open` and make sure these settings are present:
    ```toml
    [DIR_ASSISTANT]
    ACTIVE_MODEL_IS_LOCAL = false
    LITELLM_MODEL_USES_SYSTEM_MESSAGE = true
    LITELLM_CONTEXT_SIZE = 128000
    [DIR_ASSISTANT.LITELLM_COMPLETION_OPTIONS]
    model = "gpt-4o"
    ```
4.  Navigate to your project directory and run:
    ```shell
    cd directory/to/chat/with
    dir-assistant
    ```
#### For Windows (OpenAI)
```shell
pip install dir-assistant
dir-assistant setkey OPENAI_API_KEY xxxxxYOURAPIKEYHERExxxxx
# Then, configure the model as shown above using 'dir-assistant config open'
cd directory/to/chat/with
dir-assistant
```
#### For Ubuntu 24.04 (OpenAI)
```shell
pipx install dir-assistant
dir-assistant setkey OPENAI_API_KEY xxxxxYOURAPIKEYHERExxxxx
# Then, configure the model as shown above using 'dir-assistant config open'
cd directory/to/chat/with
dir-assistant
```
### Quickstart Non-interactive Prompt with API Model
The non-interactive mode of `dir-assistant` allows you to create scripts which analyze
your files without user interaction.
To get started using an API model, you can use Google Gemini 1.5 Flash, which is currently free.
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

---

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

---

## General Usage Tips
Dir-assistant is a powerful tool with many configuration options. This section provides some
general tips for using `dir-assistant` to achieve the best results.
### Optimized Settings for Coding Assistance
There are quite literally thousands of models that can be used with `dir-assistant`. For complex coding tasks on large codebases, we recommend a high-quality embedding model combined with a powerful primary LLM and a fast, inexpensive secondary LLM for CGRAG guidance. As of writing, a strong combination is `voyage-code-3` (embeddings), `claude-3-7-sonnet` (primary), and `gemini-1.5-flash` (CGRAG).

To use these models, open the config file with `dir-assistant config open` and use the following configuration as a template.
_Note: Don't forget to add your API keys! Get them from [Anthropic](https://www.anthropic.com/claude), [Google AI Studio](https://aistudio.google.com/), and [Voyage AI](https://voyage.ai/)._
```toml
[DIR_ASSISTANT]
SYSTEM_INSTRUCTIONS = "You are a helpful AI assistant tasked with assisting my coding."
GLOBAL_IGNORES = [ ".gitignore", ".d", ".obj", ".sql", "js/vendors", ".tnn", ".env", "node_modules", ".min.js", ".min.css", "htmlcov", ".coveragerc", ".pytest_cache", ".egg-info", ".git/", ".vscode/", "build/", ".idea/", "__pycache__", ]
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
LITELLM_MODEL_USES_SYSTEM_MESSAGE = true # Important for models like Claude and some Gemini models
LITELLM_PASS_THROUGH_CONTEXT_SIZE = false
LITELLM_CONTEXT_SIZE = 200000 # Main model context size (e.g., Claude 3.7 Sonnet)
LITELLM_EMBED_CONTEXT_SIZE = 4000 # Embedding model context size
LITELLM_CGRAG_CONTEXT_SIZE = 200000 # CGRAG model context size
MODELS_PATH = "~/.local/share/dir-assistant/models/"
LLM_MODEL = "" # Local model, overridden by API settings below
EMBED_MODEL = "" # Local embedding model, overridden by API settings below

[DIR_ASSISTANT.LITELLM_API_KEYS]
ANTHROPIC_API_KEY = "your_anthropic_key_here"
GEMINI_API_KEY = "your_google_key_here"
VOYAGE_API_KEY = "your_voyage_key_here"

# Main model for generating the final, high-quality response
[DIR_ASSISTANT.LITELLM_COMPLETION_OPTIONS]
model = "anthropic/gemini-2.5-pro"
timeout = 600

# Optional: A faster, cheaper model for the initial CGRAG guidance step
[DIR_ASSISTANT.LITELLM_CGRAG_COMPLETION_OPTIONS]
model = "gemini/gemini-2.5-flash"
timeout = 300

# High-quality embedding model specialized for code
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

---

## Examples
See [examples](https://github.com/curvedinf/dir-assistant/tree/main/examples).
```bash
./reddit-stock-sentiment.sh
Downloading top posts from r/wallstreetbets...
  % Total    % Received % Xferd  Average Speed   Time    Time     Time  Current
                                 Dload  Upload   Total   Spent    Left  Speed
100  173k  100  173k    0     0   353k      0 --:--:-- --:--:-- --:--:--  353k
Analyzing sentiment of stocks mentioned in subreddits...
Sentiment Analysis Results:
TSLA 6.5
SPY 4.2
NVDA 3.1
BTC 2.8
MSTR 2.5
PLTR -4.5
IONQ -5.2
RGTI -6.1
STRK -7.3
TWLO -8.0
```
