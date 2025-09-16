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
connect it to dir-assistant using the [custom API server](configuration.md#connecting-to-a-custom-api-server)
feature._
The default configuration for `dir-assistant` is API-mode. If you download an LLM model with `download-llm`,
local-mode will automatically be set. To change from API-mode to local-mode, set the `ACTIVE_MODEL_IS_LOCAL` setting.
#### For Ubuntu 24.04
`pip3` has been replaced with `pipx` starting in Ubuntu 24.04.
```shell
pipx install dir-assistant
```
