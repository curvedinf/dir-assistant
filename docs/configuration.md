# Configuration

This document provides a comprehensive guide to configuring `dir-assistant`.

## Table of Contents
1. [API Configuration](#api-configuration)
   - [General API Settings](#general-api-settings)
   - [Configuring for Specific API Providers](#configuring-for-specific-api-providers)
   - [CGRAG-Specific Model Configuration](#cgrag-specific-model-configuration)
   - [Connecting to a Custom API Server](#connecting-to-a-custom-api-server)
2. [Local LLM Configuration](#local-llm-configuration)
   - [Local LLM Model Download](#local-llm-model-download)
   - [Configuring A Custom Local Model](#configuring-a-custom-local-model)
   - [Llama.cpp Options](#llamacpp-options)
3. [Embedding Model Configuration](#embedding-model-configuration)
4. [Hardware Platform Selection](#optional-select-a-hardware-platform)
5. [General Configuration](#general-configuration-local-and-api-mode)
   - [RAG Caching and Context Optimization](#rag-caching-and-context-optimization)

---

## API Configuration
If you wish to use an API LLM, you will need to configure `dir-assistant` accordingly.
### General API Settings
To use any API-based LLM, ensure the following general settings in your configuration file (open with `dir-assistant config open`):
```toml
[DIR_ASSISTANT]
ACTIVE_MODEL_IS_LOCAL = false  # For using an API model
LITELLM_CONTEXT_SIZE = 70000 # Adjust based on the model
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
    Refer to the [Quickstart for Gemini](usage.md#quickstart-chat-with-api-model-google-gemini) for a streamlined setup. The [Optimized Settings](usage.md#optimized-settings-for-coding-assistance) section also features a Gemini configuration.
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
    Refer to the [Quickstart for Claude](usage.md#quickstart-chat-with-api-model-anthropic-claude) for a streamlined setup.
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
    Refer to the [Quickstart for OpenAI](usage.md#quickstart-chat-with-api-model-openai) for a streamlined setup.
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
# If api_base doesn't work, try base_url instead. LiteLLM has used both for the same purpose.
# api_key = "sk-xxxxxxxxxx" # If your custom server requires an API key, set it here or as an environment variable
```
Ensure that `ACTIVE_MODEL_IS_LOCAL` is set to `false`. The `model` name should be what your custom server expects. Some servers might also require an `api_key` even if hosted locally.

---

## Local LLM Configuration
### Local LLM Model Download
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

---

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

---

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
### Context Caching Optimization
`dir-assistant` includes a system to optimize the context sent to your LLM server, aiming to maximize the utilization of context caching implemented in many LLM servers. Context caching reduces latency and cost by reusing computation from previous prompts. For this to work, the beginning of a new prompt must exactly match the beginning of a previous one.

In `dir-assistant`, the context is primarily composed of chunks of your files, known as RAG artifacts. Context optimization's goal is to order these artifacts consistently to create stable "prefixes" (the initial sequence of artifacts) that the LLM system can cache.

#### Optimization Strategy
The optimizer follows a three-tiered strategy to construct the best possible artifact list for caching:

1.  **Core vs. Excludable Artifacts**: First, it divides the initial RAG results (based on semantic relevance) into two groups:
    *   **Core Artifacts**: The most relevant artifacts that *must* be included in the context.
    *   **Excludable Artifacts**: The least relevant artifacts, which can be swapped out to improve cache hits.
    The `ARTIFACT_EXCLUDABLE_FACTOR` setting controls this division. For example, a value of `0.2` means the top 80% of artifacts are "core," and the bottom 20% are "excludable."

2.  **Prefix Matching with Swapping**: The optimizer then searches through previously cached prefixes. This list of prefixes includes every prefix combination from every previous prompt. It looks for the longest prefix that meets two conditions:
    *   It must contain all **core artifacts**.
    *   The number of new artifacts it introduces (those not in the initial RAG results) must be less than or equal to the number of available **excludable artifacts**.
    This allows `dir-assistant` to "swap" less relevant files from the current query for files from a cached prefix, thereby reconstructing the cached context and achieving a cache hit. If multiple prefixes are viable, the one with the most historical hits is chosen. If the cached prefix is small enough, excludable artifacts from this prompt are backfilled in.

3.  **Fallback Sorting**: If no suitable cached prefix can be constructed, the optimizer falls back to a default sorting algorithm. The default sorting algorithm attempts to predict which artifacts will be most reusable to future prompts by scoring attributes of their usage history (frequency, position, stability) and their embedding vector cosine similarity. This mechanism attempts to make the current context maximally reusable for future prompts.

#### Context Caching Optimization Settings
You can tune the optimizer's behavior through the following settings in your configuration file (`dir-assistant config open`):
```toml
[DIR_ASSISTANT]
# The percentile of the most distant RAG results that can be replaced
# by artifacts from a cached prefix. A value of 0.2 means the bottom
# 20% of semantically relevant files can be swapped out.
ARTIFACT_EXCLUDABLE_FACTOR = 0.2

# The time-to-live (in seconds) for a cached context prefix.
# Default is 3600 (1 hour). Set to your LLM server's TTL.
API_CONTEXT_CACHE_TTL = 3600

# Weights used by the optimizer to score and reorder file artifacts in the
# fallback sorting scenario. Adjusting these can change how aggressively
# the optimizer prioritizes different factors.
[DIR_ASSISTANT.RAG_OPTIMIZER_WEIGHTS]
frequency = 1.0
position = 1.0
stability = 1.0
historical_hits = 1.0 # Used to tie-break between equally long prefixes
```
