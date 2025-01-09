from os import environ, getenv, makedirs
from os.path import expanduser, join
from subprocess import run

import toml
from dynaconf import Dynaconf

CONFIG_FILENAME = "config.toml"
CONFIG_PATH = "~/.config/dir-assistant"
CONFIG_DEFAULTS = {
    "SYSTEM_INSTRUCTIONS": "You are a helpful AI assistant.",
    "GLOBAL_IGNORES": [
        ".git/",
        ".vscode/",
        "node_modules/",
        "build/",
        ".idea/",
        "__pycache__",
        "dist/",
    ],
    "CONTEXT_FILE_RATIO": 0.9,
    "ACTIVE_MODEL_IS_LOCAL": False,
    "ACTIVE_EMBED_IS_LOCAL": False,
    "OUTPUT_ACCEPTANCE_RETRIES": 1,
    "USE_CGRAG": True,
    "PRINT_CGRAG": False,
    "COMMIT_TO_GIT": False,
    "MODELS_PATH": "~/.local/share/dir-assistant/models/",
    "EMBED_MODEL": "",
    "LLM_MODEL": "",
    "LLAMA_CPP_OPTIONS": {
        "n_ctx": 10000,
        "verbose": False,
    },
    "LLAMA_CPP_EMBED_OPTIONS": {
        "n_ctx": 8192,
        "n_batch": 512,
        "verbose": False,
        "rope_scaling_type": 2,
        "rope_freq_scale": 0.75,
    },
    "LLAMA_CPP_COMPLETION_OPTIONS": {
        "frequency_penalty": 1.1,
    },
    "LITELLM_MODEL": "gemini/gemini-1.5-flash-latest",
    "LITELLM_CONTEXT_SIZE": 500000,
    "LITELLM_MODEL_USES_SYSTEM_MESSAGE": False,
    "LITELLM_PASS_THROUGH_CONTEXT_SIZE": False,
    "LITELLM_EMBED_MODEL": "gemini/text-embedding-004",
    "LITELLM_EMBED_CHUNK_SIZE": 2048,
    "LITELLM_EMBED_REQUEST_DELAY": 0,
    "LITELLM_API_KEYS": {
        "GEMINI_API_KEY": "",
        "OPENAI_API_KEY": "",
        "ANTHROPIC_API_KEY": "",
    },
}


def get_file_path(path, filename):
    expanded_path = expanduser(path)
    makedirs(expanded_path, exist_ok=True)
    return join(expanded_path, filename)


def save_config(config_dict):
    with open(get_file_path(CONFIG_PATH, CONFIG_FILENAME), "w") as config_file:
        toml.dump(config_dict, config_file)


def check_defaults(config_dict, defaults_dict):
    for key, value in defaults_dict.items():
        if key not in config_dict.keys():
            config_dict[key] = value
    return config_dict


def load_config():
    config_object = Dynaconf(
        settings_files=[get_file_path(CONFIG_PATH, CONFIG_FILENAME)]
    )
    config_dict = config_object.as_dict()
    # If the config file is malformed, insert the DIR_ASSISTANT key
    if "DIR_ASSISTANT" not in config_dict.keys():
        config_dict["DIR_ASSISTANT"] = {}
    # Check for missing config options (maybe after a version upgrade)
    for key, value in CONFIG_DEFAULTS.items():
        if key not in config_dict["DIR_ASSISTANT"].keys():
            config_dict["DIR_ASSISTANT"][key] = value
    save_config(config_dict)
    # Set OpenAI API key
    for key, value in config_dict["DIR_ASSISTANT"]["LITELLM_API_KEYS"].items():
        if key.endswith("_API_KEY"):
            environ[key] = value
    return config_dict


def config(args, config_dict):
    # List the current configuration
    config_file_path = get_file_path(CONFIG_PATH, CONFIG_FILENAME)
    print(f"Configuration file: {config_file_path}\n")
    print(toml.dumps(config_dict))


def config_open(args):
    config_file_path = get_file_path(CONFIG_PATH, CONFIG_FILENAME)
    editor = (
        getenv("VISUAL") or getenv("EDITOR") or "nano"
    )  # Default to nano if EDITOR not set
    run([editor, config_file_path])
