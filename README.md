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
- Context optimization for utilizing LLM context caching to reduce cost and latency.
- Optionally configure a separate, faster LLM for the CGRAG guidance step to reduce cost and latency.
## Table of Contents
1. [New Features](#new-features)
2. [Quickstart](#quickstart)
    1. [Quickstart Chat with Local Default Model](#quickstart-chat-with-local-default-model)
    2. [Quickstart Chat with API Model (Google Gemini)](#quickstart-chat-with-api-model-google-gemini)
    3. [Quickstart Chat with API Model (Anthropic Claude)](#quickstart-chat-with-api-model-anthropic-claude)
    4. [Quickstart Chat with API Model (OpenAI)](#quickstart-chat-with-api-model-openai)
    5. [Quickstart Non-interactive Prompt with API Model](#quickstart-non-interactive-prompt-with-api-model)
3. [Examples](#examples)
4. [General Usage Tips](#general-usage-tips)
    1. [Optimized Settings for Coding Assistance](#optimized-settings-for-coding-assistance)
5. [Install](#install)
6. [Embedding Model Configuration](#embedding-model-configuration)
7. [Optional: Select A Hardware Platform](#optional-select-a-hardware-platform)
8. [General Configuration](#general-configuration-local-and-api-mode)
   1. [RAG Caching and Context Optimization](#RAG-Caching-and-Context-Optimization)
9. [API Configuration](#api-configuration)
   1. [General API Settings](#general-api-settings)
   2. [Configuring for Specific API Providers](#configuring-for-specific-api-providers)
      1. [Google Gemini](#google-gemini)
      2. [Anthropic Claude (e.g., Claude 3.7 Sonnet)](#anthropic-claude-eg-claude-37-sonnet)
      3. [OpenAI (e.g., GPT-4o)](#openai-eg-gpt-4o)
   3. [CGRAG-Specific Model Configuration](#cgrag-specific-model-configuration)
   4. [Connecting to a Custom API Server](#connecting-to-a-custom-api-server)
10. [Local LLM Model Download](#local-llm-model-download)
   1. [Configuring A Custom Local Model](#configuring-a-custom-local-model)
   2. [Llama.cpp Options](#llamacpp-options)
11. [Running](#running)
    1. [Automated file update and git commit](#automated-file-update-and-git-commit)
    2. [Additional directories](#additional-directories)
    3. [Ignoring files](#ignoring-files)
    4. [Overriding Configurations with Environment Variables](#overriding-configurations-with-environment-variables)
12. [Upgrading](#upgrading)
13. [Limitations](#limitations)
14. [Additional Help](#additional-help)
15. [Contributors](#contributors)
16. [Acknowledgements](#acknowledgements)

## New Features
* File artifact context optimization for maximal utilization of LLM context caching
* Separate configuration options for the CGRAG API model so you can now use a quicker and less expensive
model for the CGRAG guidance step.
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
[Connecting to a Custom API Server](#connecting-to-a-custom-api-server)
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
model = "anthropic/claude-3-7-sonnet-20240729"
timeout = 600

# Optional: A faster, cheaper model for the initial CGRAG guidance step
[DIR_ASSISTANT.LITELLM_CGRAG_COMPLETION_OPTIONS]
model = "gemini/gemini-1.5-flash-latest"
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
## Embedding Model Configuration
You must use an embedding model regardless of whether you are running an LLM via local or API mode, but you can also
choose whether the embedding model is local or API using the `ACTIVE_EMBED_IS_LOCAL` setting. Generally local embedding 
will be faster, but API will be higher quality. If you wish to use local embedding, you can download a 
good default embedding model with:
```shell
pip install dir-assistant[recommended]
dir-assistant models download-embed
```
If you would like to use another local embedding model, download a gguf file and place it in the
models directory. The models directory can be opened in a file browser using:
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
## General Configuration (Local and API Mode)
### RAG Caching and Context Optimization
`dir-assistant` includes an advanced system to optimize the context sent to the LLM,
aiming to increase utiliziation of context caching in modern LLM systems. Context 
caching is a method used by LLM systems to reduce the amount of processing required
to generate responses by reusing identical vector states from previous prompts.

To utilize this feature, the beginning of a prompt must be identical to the 
beginning of a previous prompt. In the context of `dir-assistant`, this 
means attempting to order RAG artifacts in a way that maximizes the number 
of times an identical order of artifacts is sent to the LLM. This is 
harder than it sounds!

The context opimizer in `dir-assistant` accomplishes this by reordering 
RAG artifacts. Additionally, it may exclude up to `ARTIFACT_EXCLUDABLE_FACTOR`
of the least relevant artifacts if there are suitable previous prompts 
that have been sent with the remainder of the artifacts for your current
prompt.

It will be common that no previous prompts, or any permutations of their
beginnings, are suitable for your current prompt. In that case 
`dir-assistant` will intelligently order the new artifacts it will send
based on a variety of factors to attempt to maximize future cache hits
including:

- How frequently the artifacts appear in past prompts 
- What position the artifacts have been in past prompts
- How often the artifacts are changed on disk

There are a variety of configuration options available to tune the behavior:
```toml
[DIR_ASSISTANT]
# The percentage of the least relevant files (based on RAG distance) that can
# be replaced by more historically relevant files from the cache.
# A higher value allows more aggressive replacement.
# Range: 0.0 to 1.0. Default: 0.3 (30%)
ARTIFACT_EXCLUDABLE_FACTOR = 0.3
# The time-to-live (in seconds) for a cached context prefix.
# Default is 3600 (1 hour).
API_CONTEXT_CACHE_TTL = 3600
# Weights used by the optimizer to score and reorder file artifacts.
# Adjusting these can change how aggressively the optimizer prioritizes
# different factors when deciding the final order of files in the prompt.
[DIR_ASSISTANT.RAG_OPTIMIZER_WEIGHTS]
# How much to value artifacts that appear frequently in past prompts.
frequency = 1.0
# How much to penalize artifacts for appearing later in past prompts.
position = 1.0
# How much to value files that have not been modified recently.
stability = 1.0
# How much to value prefix orderings that have appeared frequently in history.
historical_hits = 1.0
# How much to value prefix orderings that are currently in the active cache.
cache_hits = 1.0
```
## API Configuration
If you wish to use an API LLM, you will need to configure `dir-assistant` accordingly.
### General API Settings
To use any API-based LLM, ensure the following general settings in your configuration file (open with `dir-assistant config open`):
```toml
[DIR_ASSISTANT]
ACTIVE_MODEL_IS_LOCAL = false  # Crucial for using API models
# LITELLM_CONTEXT_SIZE = 200000 # Adjust based on the model (e.g., Gemini 1.5 Pro: 1M, Claude 3.7: 200K, GPT-4o: 128K)
# LITELLM_MODEL_USES_SYSTEM_MESSAGE = true # Often true for modern APIs like Claude, OpenAI, and some Gemini models
```
You will also need to provide an API key for the service you intend to use. There is a convenience subcommand for modifying and adding API keys:
```shell
dir-assistant setkey YOUR_API_KEY_NAME xxxxxYOURAPIKEYVALUExxxxx
# Example: dir-assistant setkey GEMINI_API_KEY your_actual_gemini_key
```
Alternatively, you can add keys directly to the `[DIR_ASSISTANT.LITELLM_API_KEYS]` section in your config file.
LiteLLM supports all major LLM APIs. View the available options and model identifiers in the [LiteLLM providers list](https://docs.litellm.ai/docs/providers).
### Configuring for Specific API Providers
Below are example configurations for some popular API providers. Remember to replace placeholder API keys and model names with your actual credentials and desired models.
#### Google Gemini
Google's Gemini models, like Gemini 1.5 Flash or Gemini 1.5 Pro, are excellent choices. Gemini 1.5 Flash is often available with a generous free tier.
1.  **Get API Key:** From [Google AI Studio](https://aistudio.google.com/).
2.  **Set Key:** `dir-assistant setkey GEMINI_API_KEY your_gemini_key`
3.  **Configure `dir-assistant config open`:**
    ```toml
    [DIR_ASSISTANT]
    ACTIVE_MODEL_IS_LOCAL = false
    LITELLM_CONTEXT_SIZE = 200000 # Gemini 1.5 Flash default, Pro is 1M (can be 2M)
    # LITELLM_MODEL_USES_SYSTEM_MESSAGE = false # Default, but some Gemini models might benefit if set to true
    [DIR_ASSISTANT.LITELLM_API_KEYS]
    GEMINI_API_KEY = "your_gemini_key" # Or set via setkey command
    [DIR_ASSISTANT.LITELLM_COMPLETION_OPTIONS]
    model = "gemini/gemini-1.5-flash-latest" # Default is gemini-1.5-flash-latest
    # model = "gemini/gemini-1.5-pro-latest" # For higher capability
    timeout = 600
    ```
    Refer to the [Quickstart for Gemini](#quickstart-chat-with-api-model-google-gemini) for a streamlined setup. The [Optimized Settings](#optimized-settings-for-coding-assistance) section also features a Gemini configuration.
#### Anthropic Claude (e.g., Claude 3.7 Sonnet)
Anthropic's Claude models are known for their strong reasoning and large context windows.
1.  **Get API Key:** From [Anthropic](https://www.anthropic.com/claude).
2.  **Set Key:** `dir-assistant setkey ANTHROPIC_API_KEY your_claude_key`
3.  **Configure `dir-assistant config open`:**
    ```toml
    [DIR_ASSISTANT]
    ACTIVE_MODEL_IS_LOCAL = false
    LITELLM_MODEL_USES_SYSTEM_MESSAGE = true # Claude models use system messages
    LITELLM_CONTEXT_SIZE = 200000 # Claude 3.7 Sonnet supports 200K tokens
    [DIR_ASSISTANT.LITELLM_API_KEYS]
    ANTHROPIC_API_KEY = "your_claude_key" # Or set via setkey command
    [DIR_ASSISTANT.LITELLM_COMPLETION_OPTIONS]
    model = "anthropic/claude-3-7-sonnet-20240729" # Latest Sonnet model identifier
    # model = "anthropic/claude-3-opus-20240229" # For highest capability
    # model = "anthropic/claude-3-haiku-20240307" # For speed
    timeout = 600
    ```
    Refer to the [Quickstart for Claude](#quickstart-chat-with-api-model-anthropic-claude) for a streamlined setup.
#### OpenAI (e.g., GPT-4o)
OpenAI models like GPT-4o offer a balance of performance and cutting-edge features.
1.  **Get API Key:** From [OpenAI Platform](https://platform.openai.com/api-keys).
2.  **Set Key:** `dir-assistant setkey OPENAI_API_KEY your_openai_key`
3.  **Configure `dir-assistant config open`:**
    ```toml
    [DIR_ASSISTANT]
    ACTIVE_MODEL_IS_LOCAL = false
    LITELLM_MODEL_USES_SYSTEM_MESSAGE = true # OpenAI models use system messages
    LITELLM_CONTEXT_SIZE = 128000 # GPT-4o supports 128K tokens
    [DIR_ASSISTANT.LITELLM_API_KEYS]
    OPENAI_API_KEY = "your_openai_key" # Or set via setkey command
    [DIR_ASSISTANT.LITELLM_COMPLETION_OPTIONS]
    model = "gpt-4o" # Latest flagship model
    # model = "gpt-4-turbo"
    # model = "gpt-3.5-turbo" # For cost-effectiveness
    timeout = 600
    ```
    Refer to the [Quickstart for OpenAI](#quickstart-chat-with-api-model-openai) for a streamlined setup.
### CGRAG-Specific Model Configuration
When using CGRAG (`USE_CGRAG = true`), `dir-assistant` performs two calls to the LLM:
1.  **Guidance Call**: A first call to generate a list of relevant concepts to improve file retrieval.
2.  **Response Call**: A second call with the improved context to generate the final answer.

You can optionally specify a different, often faster and cheaper, model for the initial guidance call. This can significantly reduce API costs and improve response times without sacrificing the quality of the final answer, which is still handled by your primary model.

To configure a separate model for CGRAG, add the `LITELLM_CGRAG_COMPLETION_OPTIONS` section to your config file (`dir-assistant config open`):
```toml
[DIR_ASSISTANT]
# ... other settings
USE_CGRAG = true

# Main model for generating the final, high-quality response
[DIR_ASSISTANT.LITELLM_COMPLETION_OPTIONS]
model = "anthropic/claude-3-7-sonnet-20240729"
timeout = 600

# Optional: A faster, cheaper model for the initial CGRAG guidance step
[DIR_ASSISTANT.LITELLM_CGRAG_COMPLETION_OPTIONS]
model = "gemini/gemini-1.5-flash-latest"
timeout = 300
```
If the `LITELLM_CGRAG_COMPLETION_OPTIONS` section or its `model` key is not specified, `dir-assistant` will default to using the model defined in `LITELLM_COMPLETION_OPTIONS` for both calls. You can also set `LITELLM_CGRAG_CONTEXT_SIZE` to specify a different context size for the CGRAG model.
### Connecting to a Custom API Server
If you would like to connect to a custom API server, such as your own ollama, llama.cpp, LMStudio, 
vLLM, or other OpenAPI-compatible API server, dir-assistant supports this. To configure for this,
open the config with `dir-assistant config open` and make following changes:
```toml
[DIR_ASSISTANT]
ACTIVE_MODEL_IS_LOCAL = false # Ensure API mode
[DIR_ASSISTANT.LITELLM_COMPLETION_OPTIONS]
# The 'model' parameter here might be a model name known to your custom server,
# or it might be a LiteLLM-style prefix if your server uses it.
# For generic OpenAI-compatible servers, often you just specify the model name.
model = "custom/my-model-name" # Example, adjust as per your server's requirements
api_base = "http://localhost:1234/v1" # URL to your server's OpenAI-compatible endpoint
# api_key = "sk-xxxxxxxxxx" # If your custom server requires an API key, set it here or as an environment variable
```
Ensure that `ACTIVE_MODEL_IS_LOCAL` is set to `false`. The `model` name should be what your custom server expects. Some servers might also require an `api_key` even if hosted locally.
## Local LLM Model Download
If you want to use a local LLM directly within `dir-assistant` using `llama-cpp-python`, 
you can download a low requirements default model with:
```shell
pip install dir-assistant[recommended]
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
## Limitations
- Dir-assistant only detects and reads text files at this time.
## Additional Help
Use the `-h` argument with any command or subcommand to view more information. If your problem is beyond the scope of
the helptext, please report a Github issue.
## Contributors
We appreciate contributions from the community! For a list of contributors and how you can contribute,
please see [CONTRIBUTORS.md](CONTRIBUTORS.md).
## Acknowledgements
- Local LLMs are run via the fantastic [llama-cpp-python](https://github.com/abetlen/llama-cpp-python) package
- API LLMS are run using the also fantastic [LiteLLM](https://github.com/BerriAI/litellm) package
- Special thanks to [Blazed.deals](https://blazed.deals) for sponsoring this project.
