import json
import os

from index import get_file_path

CONFIG_FILENAME = 'config.json'
CONFIG_PATH = '~/.config/dir-assistant'

CONFIG_DEFAULT_SETTINGS = [
    {
        "name": "DIR_ASSISTANT_LLM_MODEL",
        "default": "",
        "help": "Filepath for your LLM model relative to dir-assistant/models."
    },
    {
        "name": "DIR_ASSISTANT_EMBED_MODEL",
        "default": "",
        "help": "Filepath for your EMBEDDING model relative to dir-assistant/models."
    },
    {
        "name": "DIR_ASSISTANT_LLAMA_CPP_OPTIONS",
        "default": {"n_ctx": 0, "verbose": False},
        "help": "Options for llama-cpp Python."
    },
    {
        "name": "DIR_ASSISTANT_LLAMA_CPP_EMBED_OPTIONS",
        "default": {"n_ctx": 8192, "n_batch": 512, "verbose": False, "rope_scaling_type": 2, "rope_freq_scale": 0.75},
        "help": "Options for embedding."
    },
    {
        "name": "DIR_ASSISTANT_LLAMA_CPP_INSTRUCTIONS",
        "default": "You are a helpful AI assistant.",
        "help": "System instructions for your model."
    },
    {
        "name": "DIR_ASSISTANT_GLOBAL_IGNORES",
        "default": ['.git/', '.vscode/', 'node_modules/', 'build/', '.idea/', '__pycache__'],
        "help": "List of global paths to ignore."
    },
    {
        "name": "DIR_ASSISTANT_CONTEXT_FILE_RATIO",
        "default": 0.5,
        "help": "Context file ratio."
    },
    {
        "name": "DIR_ASSISTANT_ACTIVE_MODEL_IS_LOCAL",
        "default": False,
        "help": "Indicates if local LLM model is active."
    },
    {
        "name": "DIR_ASSISTANT_LITELLM_MODEL",
        "default": "gemini/gemini-1.5-flash-latest",
        "help": "LiteLLM model identifier."
    },
    {
        "name": "DIR_ASSISTANT_LITELLM_CONTEXT_SIZE",
        "default": 500000,
        "help": "Context size for API model in tokens."
    },
    {
        "name": "DIR_ASSISTANT_LITELLM_MODEL_USES_SYSTEM_MESSAGE",
        "default": False,
        "help": "Indicates if the API model uses a system message."
    },
    {
        "name": "DIR_ASSISTANT_LITELLM_PASS_THROUGH_CONTEXT_SIZE",
        "default": False,
        "help": "Indicates if context size needs to be passed through."
    },
    {
        "name": "DIR_ASSISTANT_USE_CGRAG",
        "default": True,
        "help": "Flag to use CGRAG."
    },
    {
        "name": "DIR_ASSISTANT_PRINT_CGRAG",
        "default": False,
        "help": "Flag to print CGRAG."
    }
]


def check_config_file():
    # Always called at the start of the program
    filepath = get_file_path(CONFIG_PATH, CONFIG_FILENAME)
    if not os.path.isfile(filepath):
        # Create the config file if it doesn't exist
        config = {}
        for setting in CONFIG_DEFAULT_SETTINGS:
            config[setting["name"]] = setting["default"]
        with open(filepath, "w") as config_file:
            json.dump(config, config_file, indent=2)

def ensure_config_settings_are_present(config_file, settings):
    for setting in CONFIG_DEFAULT_SETTINGS:
        if setting["name"] not in settings:
            settings[setting["name"]] = setting["default"]
    json.dump(settings, config_file, indent=2)

def config(args):
    filepath = get_file_path(CONFIG_PATH, CONFIG_FILENAME)
    with open(filepath, "r") as config_file:
        settings = json.load(config_file)
    with open(filepath, "w") as config_file:
        ensure_config_settings_are_present(config_file, settings)
    print("- Configuration settings:")
    if args.mode == None:
    for setting in CONFIG_SETTINGS:
        print(f"- {setting['name']}: {settings[setting['name']]} (Default: {setting['default']}, Help: {setting['help']})")
