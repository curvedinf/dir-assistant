import json
import os

# Get user inputs
dir_assistant_active_model_is_local = input(
    "Do you want to use a Local LLM model? (otherwise use an API) (y/n): "
).lower() == "y"

if dir_assistant_active_model_is_local:
    dir_assistant_llm_model = input("Enter the gguf filepath for your LLM model relative to dir-assistant/models: ")
    dir_assistant_litellm_model = "gemini/gemini-1.0-pro-latest"
    dir_assistant_litellm_context_size = 32000
    dir_assistant_litellm_model_uses_system_message = False
    local_llm_on_gpu = input("Would you like your model to run on your GPU? (y/n): ").lower() == "y"
else:
    dir_assistant_llm_model = ""
    dir_assistant_litellm_model = input(
        "Enter the LiteLLM identifier of the model (https://docs.litellm.ai/docs/providers) or press enter for gemini 1.0 pro: "
    )
    if dir_assistant_litellm_model == "":
        dir_assistant_litellm_model = "gemini/gemini-1.0-pro-latest"
    dir_assistant_litellm_context_size = input("Enter the context size for your API model in tokens or press enter for 32000: ")
    if dir_assistant_litellm_context_size == "":
        dir_assistant_litellm_context_size = 32000
    else:
        dir_assistant_litellm_context_size = int(dir_assistant_litellm_context_size)
    dir_assistant_litellm_model_uses_system_message = input("Does your API model use a system message? (most do not) (y/n): ").lower() == "y"
    local_llm_on_gpu = False
dir_assistant_embed_model = input("Enter the gguf filepath for your EMBEDDING model relative to dir-assistant/models: ")
dir_assistant_llama_cpp_instructions = input("Enter the system instructions for your model or press enter for a sane default: ")
if dir_assistant_llama_cpp_instructions == "":
    dir_assistant_llama_cpp_instructions = "You are a helpful AI assistant."

dir_assistant_llama_cpp_options = {
    "n_ctx": 0,
    "verbose": False,
}
if local_llm_on_gpu:
    dir_assistant_llama_cpp_options["n_gpu_layers"] = -1
dir_assistant_llama_cpp_embed_options = {
    "n_ctx": 8192,
    "n_batch": 8192,
    "verbose": False,
    "rope_scaling_type": 2,
    "rope_freq_scale": 0.75
}

# Create the config dictionary
config = {
    "DIR_ASSISTANT_LLM_MODEL": dir_assistant_llm_model,
    "DIR_ASSISTANT_EMBED_MODEL": dir_assistant_embed_model,
    "DIR_ASSISTANT_LLAMA_CPP_OPTIONS": dir_assistant_llama_cpp_options,
    "DIR_ASSISTANT_LLAMA_CPP_EMBED_OPTIONS": dir_assistant_llama_cpp_embed_options,
    "DIR_ASSISTANT_LLAMA_CPP_INSTRUCTIONS": dir_assistant_llama_cpp_instructions,
    "DIR_ASSISTANT_GLOBAL_IGNORES": ['.git/', '.vscode/', 'node_modules/', 'build/', '.idea/', '__pycache__'],
    "DIR_ASSISTANT_CONTEXT_FILE_RATIO": 0.5,
    "DIR_ASSISTANT_ACTIVE_MODEL_IS_LOCAL": dir_assistant_active_model_is_local,
    "DIR_ASSISTANT_LITELLM_MODEL": dir_assistant_litellm_model,
    "DIR_ASSISTANT_LITELLM_CONTEXT_SIZE": dir_assistant_litellm_context_size,
    "DIR_ASSISTANT_LITELLM_MODEL_USES_SYSTEM_MESSAGE": dir_assistant_litellm_model_uses_system_message,
    "DIR_ASSISTANT_USE_CGRAG": True,
    "DIR_ASSISTANT_PRINT_CGRAG": False,
}

# Write to config.json file
dir_assistant_root = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(dir_assistant_root, "config.json"), "w") as config_file:
    json.dump(config, config_file, indent=2)

print("- Configuration saved to config.json.")
