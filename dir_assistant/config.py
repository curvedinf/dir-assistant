import os

import toml
from dynaconf import Dynaconf

CONFIG_FILENAME = 'config.toml'
CONFIG_PATH = os.path.expanduser('~/.config/dir-assistant')
CONFIG_DEFAULTS = {
    'LLM_MODEL': '',
    'EMBED_MODEL': '',
    'LLAMA_CPP_OPTIONS': {
        'n_ctx': 0,
        'verbose': False
    },
    'LLAMA_CPP_EMBED_OPTIONS': {
        'n_ctx': 8192,
        'n_batch': 512,
        'verbose': False,
        'rope_scaling_type': 2,
        'rope_freq_scale': 0.75
    },
    'LLAMA_CPP_INSTRUCTIONS': 'You are a helpful AI assistant.',
    'GLOBAL_IGNORES': [
        '.git/',
        '.vscode/',
        'node_modules/',
        'build/',
        '.idea/',
        '__pycache__'
    ],
    'CONTEXT_FILE_RATIO': 0.5,
    'ACTIVE_MODEL_IS_LOCAL': False,
    'LITELLM_MODEL': 'gemini/gemini-1.5-flash-latest',
    'LITELLM_CONTEXT_SIZE': 500000,
    'LITELLM_MODEL_USES_SYSTEM_MESSAGE': False,
    'LITELLM_PASS_THROUGH_CONTEXT_SIZE': False,
    'USE_CGRAG': True,
    'PRINT_CGRAG': False
}


def save_config(config_dict):
    with open(get_file_path(CONFIG_PATH, CONFIG_FILENAME), 'w') as config_file:
        toml.dump(config_dict, config_file)


def load_config():
    config_object = Dynaconf(settings_files=[get_file_path(CONFIG_PATH, CONFIG_FILENAME)])
    if not config_object.as_dict().keys():
        config_object.DIR_ASSISTANT = CONFIG_DEFAULTS
        save_config(config_object.as_dict())
    return config_object.as_dict()


def config(args, config_dict):
    # List the current configuration
    config_file_path = get_file_path(CONFIG_PATH, CONFIG_FILENAME)
    print(f"Configuration file: {config_file_path}\n")
    print(toml.dumps(config_dict))


def get_file_path(path, filename):
    expanded_path = os.path.expanduser(path)
    os.makedirs(expanded_path, exist_ok=True)
    return os.path.join(expanded_path, filename)
