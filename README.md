# Dir-Assistant: Your AI-Powered Directory Assistant
Dir-assistant is a powerful command-line tool that brings the intelligence of Large Language Models (LLMs) to your local file system. It recursively scans your current directory and any other specified directories, builds a context of your files, and allows you to chat with an AI that has a deep understanding of your project's structure and content.
It supports both local LLMs (via `llama-cpp-python`) and a wide range of API-based models (via `LiteLLM`), including those from OpenAI, Anthropic, and Google.
![Dir-Assistant Demo](https://github.com/user-attachments/assets/757a7027-e439-4d32-95f2-51ab85c1c876)
_Above: Dir-assistant writes code to update itself with a new feature_
## Features
-   **Recursive Directory Scanning:** Automatically includes all text files from the current and specified directories.
-   **Intelligent Context Building:** Uses Retrieval-Augmented Generation (RAG) to find the most relevant file chunks for your prompt.
-   **Local & API Model Support:**
    -   Run local GGUF models directly for privacy and offline use.
    -   Connect to any API supported by LiteLLM (OpenAI, Anthropic, Google, etc.).
-   **Contextually-Guided RAG (CGRAG):** An advanced, two-step process that first uses the LLM to generate a "guidance" query, leading to more accurate file retrieval before generating the final answer.
-   **RAG Caching and Optimization:** Intelligently caches and reorders file context to reduce API costs and latency on subsequent, similar prompts.
-   **Hardware Acceleration:** Supports CUDA, ROCm, Metal, Vulkan, and SYCL for `llama-cpp-python` to accelerate local model inference.
-   **Automated Git Commits:** Can be configured to automatically apply file changes and commit them to your Git repository.
-   **File Watching:** Automatically re-indexes files when they are modified.
-   **Flexible Configuration:** Extensive configuration options via a TOML file and environment variables.
## Quickstart: Chat with API Model (Google Gemini)
This quickstart gets you running with Google's Gemini 1.5 Flash model, which has a generous free tier.
1.  **Install `dir-assistant`:**
    ```shell
    pip install dir-assistant
    ```
    _For Ubuntu 24.04, use `pipx install dir-assistant`._
2.  **Get a Google API Key:**
    -   Go to [Google AI Studio](https://aistudio.google.com/).
    -   Click "Get API Key" and create a new key.
3.  **Set the API Key:**
    ```shell
    dir-assistant setkey GEMINI_API_KEY your_api_key_here
    ```
4.  **Start chatting:**
    ```shell
    dir-assistant
    ```
    The assistant will now use the Gemini API.
## Quickstart: Chat with API Model (Anthropic Claude)
This quickstart gets you running with Anthropic's powerful Claude models.
1.  **Install `dir-assistant`:**
    ```shell
    pip install dir-assistant
    ```
2.  **Get an Anthropic API Key:**
    -   Sign up at [Anthropic](https://www.anthropic.com/claude).
    -   Navigate to your account settings to get an API key.
3.  **Set the API Key:**
    ```shell
    dir-assistant setkey ANTHROPIC_API_KEY your_api_key_here
    ```
4.  **Configure the Model:**
    Open the config file:
    ```shell
    dir-assistant config open
    ```
    Set the model to Claude and enable system messages:
    ```toml
    [DIR_ASSISTANT]
    # ...
    ACTIVE_MODEL_IS_LOCAL = false
    LITELLM_MODEL_USES_SYSTEM_MESSAGE = true
    [DIR_ASSISTANT.LITELLM_COMPLETION_OPTIONS]
    model = "anthropic/claude-3-7-sonnet-20240729"
    ```
5.  **Start chatting:**
    ```shell
    dir-assistant
    ```
## Quickstart: Chat with API Model (OpenAI)
This quickstart gets you running with OpenAI's models like GPT-4o.
1.  **Install `dir-assistant`:**
    ```shell
    pip install dir-assistant
    ```
2.  **Get an OpenAI API Key:**
    -   Go to the [OpenAI Platform](https://platform.openai.com/api-keys).
    -   Create a new secret key.
3.  **Set the API Key:**
    ```shell
    dir-assistant setkey OPENAI_API_KEY your_api_key_here
    ```
4.  **Configure the Model:**
    Open the config file:
    ```shell
    dir-assistant config open
    ```
    Set the model to GPT-4o and enable system messages:
    ```toml
    [DIR_ASSISTANT]
    # ...
    ACTIVE_MODEL_IS_LOCAL = false
    LITELLM_MODEL_USES_SYSTEM_MESSAGE = true
    [DIR_ASSISTANT.LITELLM_COMPLETION_OPTIONS]
    model = "gpt-4o"
    ```
5.  **Start chatting:**
    ```shell
    dir-assistant
    ```
## Quickstart: Chat with a Local Model
This guide helps you set up `dir-assistant` to run an LLM on your own machine.
1.  **Install with local model support:**
    ```shell
    # This includes llama-cpp-python
    pip install dir-assistant[recommended]
    ```
    _For Ubuntu 24.04, use `pipx install 'dir-assistant[recommended]'`._
2.  **Optional: Select a Hardware Platform for Acceleration:**
    (Recommended for performance)
    ```shell
    # For NVIDIA GPUs
    dir-assistant platform cuda
    # For AMD GPUs
    # dir-assistant platform rocm
    # For Apple Silicon
    # dir-assistant platform metal
    ```
    _For Ubuntu 24.04, add `--pipx`, e.g., `dir-assistant platform cuda --pipx`._
3.  **Download a default model:**
    This downloads both an embedding model and a general-purpose instruction-tuned LLM.
    ```shell
    dir-assistant models download-embed
    dir-assistant models download-llm
    ```
    This will automatically set `ACTIVE_MODEL_IS_LOCAL = true` and `ACTIVE_EMBED_IS_LOCAL = true` in your config.
4.  **Start chatting:**
    ```shell
    dir-assistant
    ```
## Optimized Settings for Coding Assistance
For the best coding experience, we recommend using a combination of high-quality API models. This setup uses Voyage's specialized code embedding model, Claude 3.7 Sonnet for the final response, and the fast Gemini 1.5 Flash for the CGRAG guidance step.
1.  **Get API Keys** for [Anthropic](https://www.anthropic.com/claude), [Google](https://aistudio.google.com/), and [Voyage AI](https://voyageai.com/).
2.  **Set API Keys:**
    ```shell
    dir-assistant setkey ANTHROPIC_API_KEY your_anthropic_key
    dir-assistant setkey GEMINI_API_KEY your_google_key
    dir-assistant setkey VOYAGE_API_KEY your_voyage_key
    ```
3.  **Update Configuration (`dir-assistant config open`):**
    ```toml
    [DIR_ASSISTANT]
    # General Settings
    SYSTEM_INSTRUCTIONS = "You are an expert AI software engineer."
    ACTIVE_MODEL_IS_LOCAL = false
    ACTIVE_EMBED_IS_LOCAL = false # Use API-based embedding
    USE_CGRAG = true
    PRINT_CGRAG = false # Set to true to see the guidance step
    COMMIT_TO_GIT = true # If you want the assistant to commit changes
    LITELLM_MODEL_USES_SYSTEM_MESSAGE = true # Important for Claude
    # Context sizes
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
