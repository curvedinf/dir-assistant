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
- Automatically optimizes prompts for context caching optimization to reduce cost and latency. Typical use cases have 50-90% cache hits.
### New Features
- Switched from euclidean distance to cosine similarity for artifact relevancy filtering. When upgrading, you will need to run `dir-assistant clear`.
- Added `ARTIFACT_COSINE_CUTOFF` and `ARTIFACT_COSINE_CGRAG_CUTOFF` to exclude artifacts with low cosine similarity.
- Updated support for the latest version of `llama-cpp-python`.

## Quickstart
In this section are recipes to run `dir-assistant` in basic capacity to get you started quickly.
1. [Local Model](#Local-Model)
1. [Gemini](#Gemini)
1. [Claude](#Claude)
1. [GPT5](#GPT5)
1. [Other Models](#Other-Models)
1. [Detailed Documentation](#Detailed-Documentation)
### Local Model
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
### Gemini
To get started using an API model, you can use Google Gemini 2.5 Flash, which is currently free.
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
### Claude
To get started quickly with Anthropic's Claude models:
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
    model = "anthropic/claude-sonnet-4-5-20250929"
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
### OpenAI
To get started quickly with OpenAI's models:
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
    model = "gpt-5"
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
### Automation Usage
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

## Other Models

`Dir-assistant` supports almost every local and API model. Almost all local models (except the bleeding edge) are supported via embedded `llama-cpp-python` integration, which supports GGUF format model files. Almost all API models are supported via LiteLLM integration, including generic OpenAI-compatible APIs like local servers. To learn how to use the model of your choice, view the [configuration docs](docs/configuration.md).

## Detailed Documentation
1. [Install](docs/install.md)
2. [Usage](docs/usage.md)
3. [Configuration](docs/configuration.md)
4. [Project Information](docs/project_info.md)
5. [Contributors](CONTRIBUTORS.md)
