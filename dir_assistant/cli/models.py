import os
from platform import system
from subprocess import run

from dir_assistant.cli.config import get_file_path, save_config

MODELS_DEFAULT_EMBED = "nomic-embed-text-v1.5.Q5_K_M.gguf"
MODELS_DEFAULT_LLM = "QwQ-LCoT-7B-Instruct-Q4_0.gguf"
MODELS_DEFAULT_EMBED_URL = f"https://huggingface.co/nomic-ai/nomic-embed-text-v1.5-GGUF/resolve/main/{MODELS_DEFAULT_EMBED}?download=true"
MODELS_DEFAULT_LLM_URL = f"https://huggingface.co/bartowski/QwQ-LCoT-7B-Instruct-GGUF/resolve/main/{MODELS_DEFAULT_LLM}?download=true"


def open_directory(path):
    system_name = system()
    if system_name == "Windows":
        os.startfile(path)
    elif system_name == "Darwin":  # macOS
        run(["open", path])
    elif system_name == "Linux":
        run(["xdg-open", path])
    else:
        raise OSError(f"Unsupported operating system: {system_name}")


def models_print(args, config_dict):
    models_path = get_file_path(config_dict["DIR_ASSISTANT"]["MODELS_PATH"], "")
    print(f"Models directory: {models_path}")


def models_open(args, config_dict):
    models_path = get_file_path(config_dict["DIR_ASSISTANT"]["MODELS_PATH"], "")
    open_directory(models_path)


def models_download_embed(args, config_dict):
    model_path = get_file_path(
        config_dict["DIR_ASSISTANT"]["MODELS_PATH"], MODELS_DEFAULT_EMBED
    )
    run(["wget", "-O", model_path, MODELS_DEFAULT_EMBED_URL])
    config_dict["DIR_ASSISTANT"]["ACTIVE_EMBED_IS_LOCAL"] = True
    config_dict["DIR_ASSISTANT"]["EMBED_MODEL"] = MODELS_DEFAULT_EMBED
    save_config(config_dict)


def models_download_llm(args, config_dict):
    model_path = get_file_path(
        config_dict["DIR_ASSISTANT"]["MODELS_PATH"], MODELS_DEFAULT_LLM
    )
    run(["wget", "-O", model_path, MODELS_DEFAULT_LLM_URL])
    config_dict["DIR_ASSISTANT"]["ACTIVE_MODEL_IS_LOCAL"] = True
    config_dict["DIR_ASSISTANT"]["LLM_MODEL"] = MODELS_DEFAULT_LLM
    save_config(config_dict)
