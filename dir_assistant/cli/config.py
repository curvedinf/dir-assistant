from os import environ, getenv, makedirs
from os.path import expanduser, join
from subprocess import run

import toml
from dynaconf import Dynaconf

VERSION = "1.4.1"
CONFIG_FILENAME = "config.toml"
CONFIG_PATH = join(expanduser("~"), ".config", "dir-assistant")
STORAGE_PATH = join(expanduser("~"), ".local", "share", "dir-assistant")
INDEX_CACHE_FILENAME = "index_cache.sqlite"
INDEX_CACHE_PATH = join(expanduser("~"), ".cache", "dir-assistant")
HISTORY_FILENAME = "history.pth"  # pth = prompt toolkit history
CONFIG_DEFAULTS = {
    "SYSTEM_INSTRUCTIONS": "You are a helpful AI assistant.",
    "GLOBAL_IGNORES": [
        "node_modules/",
        "build/",
        "dist/",
        ".git/",
        ".vscode/",
        ".idea/",
        "__pycache__",
    ],
    "CONTEXT_FILE_RATIO": 0.9,
    "ACTIVE_MODEL_IS_LOCAL": False,
    "ACTIVE_EMBED_IS_LOCAL": False,
    "OUTPUT_ACCEPTANCE_RETRIES": 1,
    "USE_CGRAG": True,
    "PRINT_CGRAG": False,
    "COMMIT_TO_GIT": False,
    "VERBOSE": False,
    "NO_COLOR": False,
    "MODELS_PATH": join(expanduser("~"), ".local", "share", "dir-assistant", "models"),
    "EMBED_MODEL": "",
    "LLM_MODEL": "",
    "LLAMA_CPP_OPTIONS": {
        "n_ctx": 10_000,
        "verbose": False,
    },
    "LLAMA_CPP_EMBED_OPTIONS": {
        "n_ctx": 8_192,
        "n_batch": 512,
        "verbose": False,
        "rope_scaling_type": 2,
        "rope_freq_scale": 0.75,
    },
    "LLAMA_CPP_COMPLETION_OPTIONS": {
        "frequency_penalty": 1.1,
    },
    "LITELLM_CONTEXT_SIZE": 200_000,
    "LITELLM_EMBED_CONTEXT_SIZE": 2_048,
    "LITELLM_MODEL_USES_SYSTEM_MESSAGE": False,
    "LITELLM_PASS_THROUGH_CONTEXT_SIZE": False,
    "LITELLM_EMBED_REQUEST_DELAY": 0,
    "LITELLM_API_KEYS": {
        "GEMINI_API_KEY": "",
        "OPENAI_API_KEY": "",
        "ANTHROPIC_API_KEY": "",
    },
    # https://docs.litellm.ai/docs/completion/input#input-params-1
    "LITELLM_COMPLETION_OPTIONS": {
        "model": "gemini/gemini-2.0-flash",
        "timeout": 600,
    },
    "LITELLM_EMBED_COMPLETION_OPTIONS": {
        "model": "gemini/text-embedding-004",
        "timeout": 600,
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


def set_environment_overrides(config_dict):
    """Replace config values with environment variable overrides"""

    def _override_config(config_branch, prefix=""):
        for key, value in config_branch.items():
            env_key = f"{prefix}__{key}" if prefix else key
            if isinstance(value, dict):
                config_branch[key] = _override_config(value, prefix=env_key)
            elif env_key in environ:
                config_branch[key] = coerce_setting_string_value(environ[env_key])
        return config_branch

    return _override_config(config_dict)


def coerce_setting_string_value(value_str):
    """Convert string values to appropriate Python types"""
    # Handle boolean values
    if value_str.lower() in ("true", "false"):
        return value_str.lower() == "true"
    # Handle integer values
    elif value_str.isdigit():
        return int(value_str)
    # Handle float values
    elif value_str.replace(".", "").isdigit():
        return float(value_str)
    # Keep as string if no other type matches
    return value_str


def load_config(skip_environment_vars=False):
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

    # Set any env-overridden config values
    config_dict = set_environment_overrides(config_dict)

    # Set LiteLLM API keys only if not already set in environment
    for key, value in config_dict["DIR_ASSISTANT"]["LITELLM_API_KEYS"].items():
        if key.endswith("_API_KEY") and value and key not in environ:
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
