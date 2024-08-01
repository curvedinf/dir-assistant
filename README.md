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

## Install

Install with pip:

```
pip install dir-assistant
```

The default configuration for `dir-assistant` is API-mode. If you download an LLM model with `download-llm` below, 
local-mode will automatically be set. To change from API-mode to local-mode, set the `ACTIVE_MODEL_IS_LOCAL` setting.

## Embedding Model Download

You must download an embedding model regardless of whether you are running in local or API mode. You can
download a good default embedding model with:

```
dir-assistant models download-embed
```

If you would like to use another embedding model, open the models directory with:

```
dir-assistant models
```

Note: The embedding model will be hardware accelerated after using the `platform` subcommand. To change whether it is
hardware accelerated, change `n_gpu_layers = -1` to `n_gpu_layers = 0` in the config.

## Select A Hardware Platform

By default `dir-assistant` is installed with CPU-only compute support. It will work properly without this step,
but if you would like to hardware accelerate `dir-assistant`, use the command below to compile 
`llama-cpp-python` with your hardware's support.

```
dir-assistant platform cuda
```

Available options: `cpu`, `cuda`, `rocm`, `metal`, `vulkan`, `sycl`

### For Platform Install Issues

If you have any issues building llama-cpp-python, reference the project's install 
instructions for more info: https://github.com/abetlen/llama-cpp-python

## API Configuration

To configure which LLM API dir-assistant uses, you must edit `LITELLM_MODEL` and the appropriate API key in 
your configuration. To open your configuration file, enter:

`dir-assistant config open`

Once editing the file, change:

```
[DIR_ASSISTANT]
LITELLM_MODEL = "gemini/gemini-1.5-flash-latest"
LITELLM_CONTEXT_SIZE = 500000
...
[DIR_ASSISTANT.LITELLM_API_KEYS]
GEMINI_API_KEY = "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
```

LiteLLM supports all major LLM APIs, including APIs hosted locally. View the available options in the 
[LiteLLM providers list](https://docs.litellm.ai/docs/providers).

## Local LLM Model Download

You can download a low requirements default local LLM model (Phi 3 128k) with:

```
dir-assistant models download-llm
```

If you would like to use another local LLM model, open the models directory with:

```
dir-assistant models
```

Note: The local LLM model will be hardware accelerated after using the `platform` subcommand. To change whether it is
hardware accelerated, change `n_gpu_layers = -1` to `n_gpu_layers = 0` in the config.

## Configure Settings

To print current configs:

`dir-assistant config`

To open the config file:

`dir-assistant config open`

Llama.cpp provides a large number of options to customize how your local model is run. Most of these options are
exposed via `llama-cpp-python`. You can configure them with the `[DIR_ASSISTANT.LLAMA_CPP_OPTIONS]`, 
`[DIR_ASSISTANT.LLAMA_CPP_EMBED_OPTIONS]`, and `[DIR_ASSISTANT.LLAMA_CPP_COMPLETION_OPTIONS]` sections in the 
config file.

The options available for `llama-cpp-python` are documented in the
[Llama constructor documentation](https://llama-cpp-python.readthedocs.io/en/latest/api-reference/#llama_cpp.Llama).

What the options do is also documented in the 
[llama.cpp CLI documentation](https://github.com/ggerganov/llama.cpp/blob/master/examples/main/README.md).

## Upgrading

Some version upgrades may have incompatibility issues in the embedding index cache. Use this command to delete the
index cache so it may be regenerated:

```
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
