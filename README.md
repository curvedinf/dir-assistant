# dir-assistant

Chat with your current directory's files using a local or API LLM.

![(Demo GIF of dir-assistant being run)](demo.gif)

Dir-assistant has local platform support for CPU (OpenBLAS), Cuda, ROCm, Metal, Vulkan, and SYCL.

Dir-assistant has API support for all major LLM APIs. More info in the 
[LiteLLM Docs](https://docs.litellm.ai/docs/providers).

Dir-assistant uses a unique method for finding the most important files to include when submitting your
prompt to an LLM called CGRAG (Contextually Guided Retrieval-Augmented Generation). You can read 
[this blog post](https://medium.com/@djangoist/how-to-create-accurate-llm-responses-on-large-code-repositories-presenting-cgrag-a-new-feature-of-e77c0ffe432d) for more information about how it works.

This project runs local LLMs via the fantastic [llama-cpp-python](https://github.com/abetlen/llama-cpp-python) package
and runs API LLMS using the also fantastic [LiteLLM](https://github.com/BerriAI/litellm) package.

## New Features

* Now installable via pip
* Thorough CLI functionality including platform installation, model downloading, and config editing.
* User files have been moved to appropriate home hidden directories.
* Config now has llama.cpp completion options exposed (top_k, frequency_penalty, etc.)

## Quickstart

In this section are recipes to run `dir-assistant` in basic capacity to get you started quickly.

### Quickstart with Local Default Model (Phi 3 128k)

To get started locally, you can download a default llm model. This model requires approximately 6GB of
memory to run effectively. To run via CPU:

```shell
pip install dir-assistant
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

### Quickstart with API Model

To get started using an API model, you can use Google Gemini 1.5 Flash, which is currently free.
To begin, you need to sign up for [Google AI Studio](https://aistudio.google.com/) and 
[create an API key](https://aistudio.google.com/app/apikey). After you create your API key,
enter the following commands:

```shell
pip install dir-assistant
dir-assistant models download-embed
dir-assistant setkey GEMINI_API_KEY xxxxxYOURAPIKEYHERExxxxx
cd directory/to/chat/with
dir-assistant
```

You can optionally hardware-accelerate your local embedding model so indexing is quicker:

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

## Install

Install with pip:

```shell
pip install dir-assistant
```

The default configuration for `dir-assistant` is API-mode. If you download an LLM model with `download-llm`, 
local-mode will automatically be set. To change from API-mode to local-mode, set the `ACTIVE_MODEL_IS_LOCAL` setting.

## Embedding Model Download

You must download an embedding model regardless of whether you are running in local or API mode. You can
download a good default embedding model with:

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
LITELLM_MODEL = "gemini/gemini-1.5-flash-latest"
LITELLM_CONTEXT_SIZE = 500000
...
[DIR_ASSISTANT.LITELLM_API_KEYS]
GEMINI_API_KEY = "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
```

LiteLLM supports all major LLM APIs, including APIs hosted locally. View the available options in the 
[LiteLLM providers list](https://docs.litellm.ai/docs/providers).

There is a convenience subcommand for modifying and adding API keys:

```shell
dir-assistant setkey GEMINI_API_KEY xxxxxYOURAPIKEYHERExxxxx
```

However, in most cases you will need to modify other options when changing APIs.

## Local LLM Model Download

If you want to use a local LLM, you can download a low requirements default model (Phi 3 128k) with:

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

## Running

```shell
dir-assistant
```

Running `dir-assistant` will scan all files recursively in your current directory. The most relevant files will 
automatically be sent to the LLM when you enter a prompt.

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

## Limitations

- Only tested on Ubuntu 22.04. Please let us know if you run it successfully on other platforms by submitting an issue.
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
- Web search
- API Embedding models
- Simple mode for better compatibility with external script automations
