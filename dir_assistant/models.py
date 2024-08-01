from os import chdir
from subprocess import run

from dir_assistant.config import get_file_path, save_config

MODELS_PATH = '~/.local/share/dir-assistant/models/'
MODELS_DEFAULT_EMBED = 'nomic-embed-text-v1.5.Q5_K_M.gguf'
MODELS_DEFAULT_LLM = 'Phi-3.1-mini-128k-instruct-Q5_K_L.gguf'
MODELS_DEFAULT_EMBED_URL = f'https://huggingface.co/nomic-ai/nomic-embed-text-v1.5-GGUF/resolve/main/{MODELS_DEFAULT_EMBED}?download=true'
MODELS_DEFAULT_LLM_URL = f'https://huggingface.co/bartowski/Phi-3.1-mini-128k-instruct-GGUF/resolve/main/{MODELS_DEFAULT_LLM}?download=true'

def models_print(args, config_dict):
    models_path = get_file_path(MODELS_PATH, '')
    print(f"Models directory: {models_path}")


def models_open(args, config_dict):
    models_path = get_file_path(MODELS_PATH, '')
    run(['xdg-open', models_path])

def models_download_embed(args, config_dict):
    models_path = get_file_path(MODELS_PATH, '')
    run(['wget', '-P', models_path, '-O', MODELS_DEFAULT_EMBED, MODELS_DEFAULT_EMBED_URL])
    config_dict['DIR_ASSISTANT']['EMBED_MODEL'] = MODELS_DEFAULT_EMBED
    save_config(config_dict)

def models_download_llm(args, config_dict):
    models_path = get_file_path(MODELS_PATH, '')
    run(['wget', '-P', models_path, '-O', MODELS_DEFAULT_LLM, MODELS_DEFAULT_LLM_URL])
    config_dict['DIR_ASSISTANT']['ACTIVE_MODEL_IS_LOCAL'] = True
    config_dict['DIR_ASSISTANT']['LLM_MODEL'] = MODELS_DEFAULT_LLM
    save_config(config_dict)
