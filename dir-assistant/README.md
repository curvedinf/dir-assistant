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
`dir-assistant` is a CLI python application available through `pip` that recursively indexes all text files in the current working directory so you can chat with them using a local or API LLM. By "chat with them", it is meant that their contents will automatically be included in the prompts sent to the LLM, with the most contextually relevant files included first. `dir-assistant` is designed primarily for use as a coding aid and automation tool.
## Features
- **Local & API Model Support:** Works with local GGUF models via `llama-cpp-python` and API-based models (OpenAI, Anthropic, Gemini, etc.) via `LiteLLM`.
- **RAG-Powered Context:** Uses Retrieval-Augmented Generation (RAG) to find and include the most relevant file snippets in the prompt.
- **Advanced Context Optimization:** Employs a unique RAG optimizer that analyzes historical usage to predictively reorder file context, improving cache hits and reducing API costs and latency.
- **CGRAG:** An optional two-step process (Contextually-Guided RAG) that first generates a conceptual guide to improve the accuracy of file retrieval for complex queries. You can read [this blog post](https://medium.com/@djangoist/how-to-create-accurate-llm-responses-on-large-code-repositories-presenting-cgrag-a-new-feature-of-e77c0ffe432d) for more information.
- **Interactive & Single-Prompt Mode:** Use it for interactive sessions or for one-off questions in scripts.
- **File Watching:** Automatically re-indexes files when they change.
- **Git Integration:** Can automatically apply file changes and commit them to your repository.
## Table of Contents
1. [Quickstart](#quickstart)
    1. [Chat with Local Default Model](#chat-with-local-default-model)
    2. [Chat with API Model (Google Gemini)](#chat-with-api-model-google-gemini)
    3. [Chat with API Model (Anthropic Claude)](#chat-with-api-model-anthropic-claude)
    4. [Chat with API Model (OpenAI)](#chat-with-api-model-openai)
    5. [Non-interactive Prompt with API Model](#non-interactive-prompt-with-api-model)
2. [Examples](#examples)
3. [Configuration](#configuration)
    1. [RAG Caching and Context Optimization](#rag-caching-and-context-optimization)
    2. [Optimized Settings for Coding Assistance](#optimized-settings-for-coding-assistance)
4. [Installation](#installation)
5. [Embedding Model Configuration](#embedding-model-configuration)
6. [Optional: Select A Hardware Platform](#optional-select-a-hardware-platform)
7. [API Configuration](#api-configuration)
   1. [General API Settings](#general-api-settings)
   2. [Configuring for Specific API Providers](#configuring-for-specific-api-providers)
   3. [CGRAG-Specific Model Configuration](#cgrag-specific-model-configuration)
   4. [Connecting to a Custom API Server](#connecting-to-a-custom-api-server)
8. [Local LLM Model Download](#local-llm-model-download)
   1. [Configuring A Custom Local Model](#configuring-a-custom-local-model)
   2. [Llama.cpp Options](#llamacpp-options)
9. [Usage](#usage)
    1. [Command-Line Options](#command-line-options)
    2. [Automated file update and git commit](#automated-file-update-and-git-commit)
    3. [Additional directories](#additional-directories)
    4. [Ignoring files](#ignoring-files)
    5. [Overriding Configurations with Environment Variables](#overriding-configurations-with-environment-variables)
10. [Upgrading](#upgrading)
11. [Additional Help](#additional-help)
12. [Contributors](#contributors)
13. [Acknowledgements](#acknowledgements)
14. [Limitations](#limitations)
15. [Todos](#todos)
16. [Additional Credits](#additional-credits)
## Quickstart
In this section are recipes to run `dir-assistant` in basic capacity to get you started quickly.
### Chat with Local Default Model
To get started locally, you can download a default llm model. Default configuration with this model requires 3GB of memory on most hardware. To run via CPU:
```shell
pip install dir-assistant[recommended]
dir-assistant models download-embed
dir-assistant models download-llm
cd /path/to/your/project
dir-assistant
```
To run with hardware acceleration, first use the `platform` subcommand:
```shell
...
dir-assistant platform cuda
cd /path/to/your/project
dir-assistant
```
See which platforms are supported using `-h`: `dir-assistant platform -h`
#### For Windows
It is not recommended to use `dir-assistant` directly with local LLMs on Windows because `llama-cpp-python` requires a C compiler, which can be difficult to set up. Instead, we recommend using another LLM server like LMStudio and connecting to it as a [custom API server](#connecting-to-a-custom-api-server).
#### For Ubuntu 24.04
`pip3` has been replaced with `pipx` starting in Ubuntu 24.04. Use `pipx` instead of `pip`.
```shell
pipx install dir-assistant[recommended]
...
dir-assistant platform cuda --pipx
```
### Chat with API Model (Google Gemini)
The default API model is Google's Gemini 1.5 Flash, which has a generous free tier.
1.  Get an API key from [Google AI Studio](https://aistudio.google.com/app/apikey).
2.  Install `dir-assistant` and set your key:
    ```shell
    pip install dir-assistant
    dir-assistant setkey GEMINI_API_KEY "your_key_here"
    ```
3.  Go to your project directory and run:
    ```shell
    cd /path/to/your/project
    dir-assistant
    ```
### Chat with API Model (Anthropic Claude)
1.  Get an API key from [Anthropic](https://console.anthropic.com/).
2.  Set your API key:
    ```shell
    dir-assistant setkey ANTHROPIC_API_KEY "your_key_here"
    ```
3.  Configure `dir-assistant` by running `dir-assistant config open` and setting the following:
    ```toml
    [DIR_ASSISTANT]
    ACTIVE_MODEL_IS_LOCAL = false
    LITELLM_MODEL_USES_SYSTEM_MESSAGE = true # Important for Claude
    [DIR_ASSISTANT.LITELLM_COMPLETION_OPTIONS]
    model = "anthropic/claude-3-7-sonnet-20240729"
    ```
### Chat with API Model (OpenAI)
1.  Get an API key from the [OpenAI Platform](https://platform.openai.com/api-keys).
2.  Set your API key:
    ```shell
    dir-assistant setkey OPENAI_API_KEY "your_key_here"
    ```
3.  Configure `dir-assistant` by running `dir-assistant config open` and setting the following:
    ```toml
    [DIR_ASSISTANT]
    ACTIVE_MODEL_IS_LOCAL = false
    LITELLM_MODEL_USES_SYSTEM_MESSAGE = true # Important for OpenAI
    [DIR_ASSISTANT.LITELLM_COMPLETION_OPTIONS]
    model = "gpt-4o"
    ```
### Non-interactive Prompt with API Model
You can use `dir-assistant` in scripts by passing a single prompt.
```shell
pip install dir-assistant
dir-assistant setkey GEMINI_API_KEY "your_key_here"
cd /path/to/your/project
dir-assistant -s "Describe the files in this directory"
```
## Examples
See the [examples directory](https://github.com/curvedinf/dir-assistant/tree/main/examples) for scripts, such as one that analyzes stock sentiment on Reddit:
```bash
./examples/reddit-stock-sentiment.sh 
Downloading top posts from r/wallstreetbets...
Analyzing sentiment of stocks mentioned in subreddits...
Sentiment Analysis Results:
TSLA 6.5                            
SPY 4.2
NVDA 3.1
...
```
## Configuration
You can configure `dir-assistant` by editing its configuration file.
```shell
dir-assistant config open
```
### RAG Caching and Context Optimization
`dir-assistant` includes an advanced system to optimize the context sent to the LLM, aiming to reduce latency and API costs. This system works by caching successful orderings of file "artifacts" (chunks of file content) and reordering them based on your historical usage patterns. This feature is always on. You can fine-tune its behavior using the following settings in your configuration file:
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
### Optimized Settings for Coding Assistance
For complex coding tasks, we recommend a high-quality embedding model combined with a powerful primary LLM and a fast, inexpensive secondary LLM for CGRAG guidance. As of writing, a strong combination is `voyage-code-3` (embeddings), `claude-3-7-sonnet` (primary), and `gemini-1.5-flash` (CGRAG).
_Note: Don't forget to add your API keys! Get them from [Anthropic](https://console.anthropic.com/), [Google AI Studio](https://aistudio.google.com/), and [Voyage AI](https://voyage.ai/)._
```toml
[DIR_ASSISTANT]
SYSTEM_INSTRUCTIONS = "You are a helpful AI assistant tasked with assisting my coding."
GLOBAL_IGNORES = [ ".gitignore", ".d", ".obj", ".sql", "js/vendors", ".tnn", ".env", "node_modules", ".min.js", ".min.css", "htmlcov", ".coveragerc", ".pytest_cache", ".egg-info", ".git/", ".vscode/", "build/", ".idea/", "__pycache__", ]
CONTEXT_FILE_RATIO = 0.9
ACTIVE_MODEL_IS_LOCAL = false
ACTIVE_EMBED_IS_LOCAL = false
USE_CGRAG = true
COMMIT_TO_GIT = true
LITELLM_MODEL_USES_SYSTEM_MESSAGE = true
[DIR_ASSISTANT.LITELLM_API_KEYS]
ANTHROPIC_API_KEY = "your_anthropic_key_here"
GEMINI_API_KEY = "your_google_key_here"
VOYAGE_API_KEY = "your_voyage_key_here"
# Main model for generating the final, high-quality response
[DIR_ASSISTANT.LITELLM_COMPLETION_OPTIONS]
model = "anthropic/claude-3-7-sonnet-20240729"
timeout = 600
# A faster, cheaper model for the initial CGRAG guidance step
[DIR_ASSISTANT.LITELLM_CGRAG_COMPLETION_OPTIONS]
model = "gemini/gemini-1.5-flash-latest"
timeout = 300
# High-quality embedding model specialized for code
[DIR_ASSISTANT.LITELLM_EMBED_COMPLETION_OPTIONS]
model = "voyage/voyage-code-3"
```
## Installation
Install with pip:
```shell
pip install dir-assistant
```
To enable all features, including local hardware acceleration, install the `recommended` extras:
```shell
pip install dir-assistant[recommended]
```
## Embedding Model Configuration
An embedding model is required. You can choose whether the embedding model is local or API-based using the `ACTIVE_EMBED_IS_LOCAL` setting. Generally, local embedding is faster, while API embedding may offer higher quality. To use local embedding, download a default model:
```shell
pip install dir-assistant[recommended]
dir-assistant models download-embed
```
This automatically sets `ACTIVE_EMBED_IS_LOCAL = true` and configures the downloaded model.
## Optional: Select A Hardware Platform
By default, `dir-assistant` is installed with CPU-only support. To enable hardware acceleration for local models, use the `platform` command:
```shell
dir-assistant platform cuda
```
Available options: `cpu`, `cuda`, `rocm`, `metal`, `vulkan`, `sycl`.
If you encounter issues, refer to the [llama-cpp-python documentation](https://github.com/abetlen/llama-cpp-python) for system dependency information.
## API Configuration
### General API Settings
To use any API-based LLM, run `dir-assistant config open` and ensure the following:
```toml
[DIR_ASSISTANT]
ACTIVE_MODEL_IS_LOCAL = false
# LITELLM_CONTEXT_SIZE = 200000 # Adjust based on model (e.g., Gemini 1.5 Pro: 1M, Claude 3.7: 200K)
# LITELLM_MODEL_USES_SYSTEM_MESSAGE = true # Often true for Claude, OpenAI, etc.
```
Use the `setkey` subcommand to add API keys:
```shell
dir-assistant setkey GEMINI_API_KEY "your_key_here"
```
### CGRAG-Specific Model Configuration
When `USE_CGRAG = true`, you can specify a different, often faster and cheaper, model for the initial guidance call to reduce cost and latency. If not specified, the primary model is used for both steps.
```toml
[DIR_ASSISTANT]
USE_CGRAG = true
# Main model
[DIR_ASSISTANT.LITELLM_COMPLETION_OPTIONS]
model = "anthropic/claude-3-7-sonnet-20240729"
# Optional: Faster model for the CGRAG guidance step
[DIR_ASSISTANT.LITELLM_CGRAG_COMPLETION_OPTIONS]
model = "gemini/gemini-1.5-flash-latest"
```
### Connecting to a Custom API Server
To connect to a local server (Ollama, LMStudio, etc.), configure the `api_base` in your config file:
```toml
[DIR_ASSISTANT]
ACTIVE_MODEL_IS_LOCAL = false
[DIR_ASSISTANT.LITELLM_COMPLETION_OPTIONS]
model = "custom/my-local-model" # Adjust as per your server's requirements
api_base = "http://localhost:1234/v1" # URL to your server's endpoint
# api_key = "sk-..." # If your server requires a key
```
## Local LLM Model Download
To use a local LLM, download a default model:
```shell
pip install dir-assistant[recommended]
dir-assistant models download-llm
```
This automatically sets `ACTIVE_MODEL_IS_LOCAL = true` and configures the downloaded model.
### Configuring A Custom Local Model
To use your own GGUF model, place it in the models directory (`dir-assistant models open`) and update your config file (`dir-assistant config open`):
```toml
[DIR_ASSISTANT]
LLM_MODEL = "My-Custom-Model.Q5_K_M.gguf"
```
### Llama.cpp Options
You can configure `llama-cpp-python` settings for local models in your config file. See the [Llama constructor documentation](https://llama-cpp-python.readthedocs.io/en/latest/api-reference/#llama_cpp.Llama) for available options.
```toml
[DIR_ASSISTANT.LLAMA_CPP_OPTIONS]
n_ctx = 8192 # Context size
n_gpu_layers = -1 # -1 for full GPU offload
[DIR_ASSISTANT.LLAMA_CPP_COMPLETION_OPTIONS]
temperature = 0.7
```
## Usage
Start the assistant in your project directory:
```shell
dir-assistant
```
### Command-Line Options
`dir-assistant` is shorthand for `dir-assistant start`.
- `-i, --ignore`: A list of space-separated filepaths to ignore.
- `-d, --dirs`: A list of space-separated directories to work on (current directory is always included).
- `-s, --single-prompt`: Run a single prompt and output the final answer.
- `-v, --verbose`: Show debug information during execution.
- `-n, --no-color`: Disable colored output.
### Automated file update and git commit
To allow `dir-assistant` to modify files and commit them, enable `COMMIT_TO_GIT = true` in the config. The assistant will prompt for confirmation before applying changes.
### Additional directories
Include files from outside your current directory:
```shell
dir-assistant -d /path/to/other/project
```
### Ignoring files
Ignore files via the command line or by adding them to the `GLOBAL_IGNORES` list in your config file.
```shell
dir-assistant -i "*.log" "dist/"
```
### Overriding Configurations with Environment Variables
Any configuration setting can be overridden using environment variables. The variable name must be prefixed with `DIR_ASSISTANT__` and use double underscores for nested keys.
```shell
# Override the model being used
export DIR_ASSISTANT__LLM_MODEL="mistral-7b-instruct.Q4_K_M.gguf"
# Override a nested key
export DIR_ASSISTANT__LLAMA_CPP_EMBED_OPTIONS__n_ctx=2048
# Run with inline environment variables
DIR_ASSISTANT__COMMIT_TO_GIT=true dir-assistant
```
## Upgrading
If you encounter issues after upgrading, especially with embedding models, clear all caches:
```shell
dir-assistant clear
```
This will remove `index_cache.sqlite`, `prefix_cache.sqlite`, `prompt_history.sqlite`, and the prompt history file, forcing them to be regenerated on the next run.
## Additional Help
Use the `-h` argument with any command or subcommand for more information. For other issues, please open a ticket on GitHub.
## Contributors
We appreciate contributions from the community! For a list of contributors and how you can contribute, please see [CONTRIBUTORS.md](CONTRIBUTORS.md).
## Acknowledgements
- Local LLMs are run via the fantastic [llama-cpp-python](https://github.com/abetlen/llama-cpp-python) package.
- API LLMs are run using the also fantastic [LiteLLM](https://github.com/BerriAI/litellm) package.
## Limitations
- Dir-assistant only detects and reads text files at this time.
## Todos
- ~~API LLMs~~
- ~~RAG~~
- ~~File caching~~
- ~~CGRAG~~
- ~~RAG Context Optimization~~
- ~~Multi-line input~~
- ~~File watching~~
- ~~Single-step pip install~~
- ~~Model download~~
- ~~Commit to git~~
- ~~API Embedding models~~
- ~~Single-prompt mode~~
- ~~Support for custom APIs~~
- ~~Support for thinking models~~
- ~~CGRAG-specific LLM configuration~~
- Web search
- Daemon mode for API-based use
## Additional Credits
Special thanks to [Blazed.deals](https://blazed.deals) for sponsoring this project.