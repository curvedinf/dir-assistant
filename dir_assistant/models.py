from os import chdir
from subprocess import run

from dir_assistant.config import get_file_path

MODELS_PATH = '~/.local/share/dir-assistant/models/'
MODELS_DEFAULT_EMBED_URL = 'https://huggingface.co/nomic-ai/nomic-embed-text-v1.5-GGUF/resolve/main/nomic-embed-text-v1.5.Q5_K_M.gguf?download=true'
MODELS_DEFAULT_LLM_URL = 'https://huggingface.co/bartowski/Phi-3.1-mini-128k-instruct-GGUF/resolve/main/Phi-3.1-mini-128k-instruct-Q5_K_L.gguf?download=true'

def models_cd(args, config_dict):
    models_path = get_file_path(MODELS_PATH, '')
    chdir(models_path)


def models_open(args, config_dict):
    models_path = get_file_path(MODELS_PATH, '')
    run(['xdg-open', models_path])

def models_download_embed(args, config_dict):
    models_path = get_file_path(MODELS_PATH, '')
    run(['wget', '-P', models_path, MODELS_DEFAULT_EMBED_URL])

def models_download_llm(args, config_dict):
    models_path = get_file_path(MODELS_PATH, '')
    run(['wget', '-P', models_path, MODELS_DEFAULT_LLM_URL])
