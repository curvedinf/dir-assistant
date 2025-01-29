from os import environ, getenv, makedirs
from os.path import expanduser, join
from subprocess import run

import toml
from dynaconf import Dynaconf

from dir_assistant.cli.start import parse_config_override

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


def get_env_var_overrides(config_dict):
    """Get configuration overrides from both environment variables and command line arguments"""
    overrides = {}

    # Some subcommands have a larger scope config dict, but we only want the DIR_ASSISTANT section
    config_dict = config_dict["DIR_ASSISTANT"] if "DIR_ASSISTANT" in config_dict else config_dict

    # Process all config keys that have matching environment variables
    for key, value in config_dict.items():
        # Env vars have DIR_ASSISTANT__ prepended so there are no collisions in more complex systems
        env_key = f"DIR_ASSISTANT__{key}"
        if env_key in os.environ:  # Only process if it's a valid environment variable
            env_value = os.environ[env_key]
            overrides[key] = coerce_setting_string_value(env_value)
        elif isinstance(value, dict):  # Check if value is a dict-like collection
            for sub_key, sub_value in value.items():
                # Environment vars will be of the form DIR_ASSISTANT__GROUP__KEY
                env_key = f"DIR_ASSISTANT__{key}__{sub_key}"
                if env_key in os.environ:
                    env_value = os.environ[env_key]
                    if key not in overrides:
                        overrides[key] = {}
                    overrides[key][sub_key] = coerce_setting_string_value(env_value)

    return overrides


def coerce_setting_string_value(value_str):
    """Convert string values to appropriate Python types"""
    # Handle boolean values
    if value_str.lower() in ('true', 'false'):
        return value_str.lower() == 'true'
    # Handle integer values
    elif value_str.isdigit():
        return int(value_str)
    # Handle float values
    elif value_str.replace('.', '').isdigit():
        return float(value_str)
    # Keep as string if no other type matches
    return value_str


def parse_config_override(override_str):
    """Parse a key=value config override string"""
    try:
        key, value = override_str.split('=', 1)
        return key.strip(), coerce_setting_string_value(value.strip())
    except ValueError:
        raise ValueError(f"Invalid config override format: {override_str}. Use KEY=VALUE format.")


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

    # Override any config values present in environment variables
    if args.config_overrides:
        for override in args.config_overrides:
            try:
                key, value = parse_config_override(override)
                if key in config_dict:
                    config_dict[key] = value
                else:
                    print(f"Warning: Unknown config key '{key}' ignored")
            except ValueError as e:
                print(f"Warning: {str(e)}")

    # Update config with environment variable overrides
    config_dict.update(get_config_overrides(config_dict))

    # Apply any environment variable overrides to config
    overrides = get_config_overrides(config_dict)

    # Update config with overrides
    for key, value in overrides.items():
        if args.verbose:
            print(f"Debug: Applying config override {key}={value}")
        if key == 'LITELLM_API_KEYS':
            # Update API keys while preserving existing ones
            config[key].update(value)
        else:
            config[key] = value

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
