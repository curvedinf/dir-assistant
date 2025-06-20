# Dir-Assistant

Dir-Assistant is a command-line tool that allows you to chat with an LLM about the files in your current directory. It automatically includes the most relevant files in the context of your conversation, making it a powerful companion for coding, analysis, and other file-based tasks.

![Dir-Assistant Demo](./docs/images/demo.gif)

## Features

-   **Automatic Context:** Recursively scans your directory and finds the most relevant files for your prompt.
-   **Local & API Models:** Supports both local GGUF models via `llama-cpp-python` and API-based models via `LiteLLM`.
-   **Chat & Single-Prompt Modes:** Use it as an interactive chat assistant or for one-off questions.
-   **File Watching:** Automatically re-indexes files when they change.
-   **CGRAG:** Contextually-Guided Retrieval-Augmented Generation for more accurate file retrieval.
-   **RAG Caching:** Optimizes context and reduces API costs by caching and reordering file artifacts.
-   **Git Integration:** Can automatically commit file changes made during a chat session.
-   **Configurable:** Extensive configuration options, including environment variable overrides.

## Quickstart (Chat with API Model - OpenAI)

1.  **Install:**
    ```shell
    pip install dir-assistant
    ```
2.  **Get API Key:** From [OpenAI Platform](https://platform.openai.com/api-keys).
3.  **Set Key & Configure:**
    ```shell
    dir-assistant setkey OPENAI_API_KEY your_openai_key
    dir-assistant config --set ACTIVE_MODEL_IS_LOCAL=false
    dir-assistant config --set LITELLM_COMPLETION_OPTIONS.model=gpt-4o
    ```
4.  **Run:**
    ```shell
    dir-assistant
    ```

## Quickstart (Chat with API Model - Anthropic Claude)

1.  **Install:**
    ```shell
    pip install dir-assistant
    ```
2.  **Get API Key:** From [Anthropic Console](https://console.anthropic.com/dashboard).
3.  **Set Key & Configure:**
    ```shell
    dir-assistant setkey ANTHROPIC_API_KEY your_claude_key
    dir-assistant config --set ACTIVE_MODEL_IS_LOCAL=false
    dir-assistant config --set LITELLM_MODEL_USES_SYSTEM_MESSAGE=true
    dir-assistant config --set LITELLM_COMPLETION_OPTIONS.model=anthropic/claude-3-7-sonnet-20240729
    ```
4.  **Run:**
    ```shell
    dir-assistant
    ```

## Quickstart (Chat with Local Model)

1.  **Install with hardware acceleration:**
    ```shell
    # For NVIDIA GPUs (CUDA)
    pip install dir-assistant[cuBLAS]
    # For Apple Silicon (Metal)
    pip install dir-assistant[metal]
    # For other platforms or CPU-only
    pip install dir-assistant[recommended]
    ```
2.  **Download a default model:**
    ```shell
    dir-assistant models download-llm
    ```
3.  **Run:**
    ```shell
    dir-assistant
    ```

## Installation

```shell
# Basic installation
pip install dir-assistant

# To include llama-cpp-python with recommended settings
pip install dir-assistant[recommended]

# For NVIDIA GPU acceleration (cuBLAS)
pip install dir-assistant[cuBLAS]

# For Apple Silicon GPU acceleration (Metal)
pip install dir-assistant[metal]
```

After installation, it is recommended to run `dir-assistant platform` to configure hardware acceleration for local models.

## Configuration

`dir-assistant` is highly configurable via a TOML file located at `~/.config/dir-assistant/config.toml`.

-   **Open config file for editing:** `dir-assistant config open`
-   **List current configuration:** `dir-assistant config`
-   **Set a specific value:** `dir-assistant config --set KEY=VALUE` (e.g., `dir-assistant config --set VERBOSE=true`)

### API Configuration

You can connect to any LLM provider supported by [LiteLLM](https://docs.litellm.ai/docs/providers).

#### Anthropic (e.g., Claude 3.7 Sonnet)
Claude models are highly capable and offer a great balance of speed and intelligence.
1.  **Get API Key:** From [Anthropic Console](https://console.anthropic.com/dashboard).
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
### RAG Caching and Context Optimization
`dir-assistant` includes an advanced system to optimize the context sent to the LLM, aiming to reduce latency and API costs, especially for users who frequently interact with similar sets of files. This system works by caching successful orderings of file "artifacts" (chunks of file content) and reordering them based on your historical usage patterns.

This feature is always on and works in the background. You can fine-tune its behavior using the following settings in your configuration file (`dir-assistant config open`):

```toml
[DIR_ASSISTANT]
# ... other settings

# The percentage of the least relevant files (based on RAG distance) that can
# be replaced by more historically relevant files from the cache.
# A higher value allows more aggressive replacement of less relevant files
# with potentially more useful, historically-used files.
# Range: 0.0 to 1.0. A value of 0.3 means 30% of the initial RAG results
# are considered for replacement.
ARTIFACT_EXCLUDABLE_FACTOR = 0.3

# The time-to-live (in seconds) for a cached context prefix. If a prefix isn't
# used within this time, it's considered expired and won't be used for optimization.
# This prevents outdated context orderings from being used.
# Default is 3600 (1 hour).
API_CONTEXT_CACHE_TTL = 3600

# Weights used by the optimizer to score and reorder file artifacts.
# Adjusting these can change how aggressively the optimizer prioritizes
# different factors when deciding the final order of files in the prompt.
[DIR_ASSISTANT.RAG_OPTIMIZER_WEIGHTS]
# How much to value artifacts that appear frequently in past prompts.
# Higher value prioritizes popular files.
frequency = 1.0
# How much to penalize artifacts for appearing later in past prompts.
# A negative weight is not recommended. This helps push more consistently
# important files to the front.
position = 1.0
# How much to value files that have not been modified recently (more stable).
# This assumes that stable, unchanged files are more foundational.
stability = 1.0
# How much to value prefix orderings that have appeared frequently in history.
# This helps reuse successful prompt structures.
historical_hits = 1.0
# How much to value prefix orderings that are currently in the active cache.
# This gives a boost to very recently successful prompt structures.
cache_hits = 1.0
```
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
directory. [Huggingface](https://huggingface.co/models) has numerous GGUF models available. The models 
directory can be opened in a file browser using:
```shell
dir-assistant models
```
Once you have moved the model to the models folder, open the config and change the `LLM_MODEL` setting:
```shell
dir-assistant config open
```
Then edit the setting:
```toml
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
the helptext, please report a Github issue.
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
- ~~Support for thinking models~~
- ~~CGRAG-specific LLM configuration~~
- ~~RAG Caching and Context Optimization~~
- Web search
- Daemon mode for API-based use
## Additional Credits
Special thanks to [Blazed.deals](https://blazed.deals) for sponsoring this project.
