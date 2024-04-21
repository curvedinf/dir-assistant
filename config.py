import json
import os

# Get user inputs
dir_assistant_llm_model = input("Enter the gguf filepath for your LLM model relative to dir-assistant/models: ")
dir_assistant_embed_model = input("Enter the gguf filepath for your EMBEDDING model relative to dir-assistant/models: ")
dir_assistant_llama_cpp_instructions = input("Enter the system instructions for your model or press enter for a sane default: ")
if dir_assistant_llama_cpp_instructions == "":
    dir_assistant_llama_cpp_instructions = "You are a helpful AI assistant. Do your best to answer questions related to files below:\n\n"

dir_assistant_llama_cpp_options = {
    "n_ctx": 0,
    "n_batch": 8192,
    "verbose": False,
}
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
}

# Write to config.json file
dir_assistant_root = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(dir_assistant_root, "config.json"), "w") as config_file:
    json.dump(config, config_file, indent=2)

print("- Configuration saved to config.json. Sane default llama.cpp options have been saved there.")
print('- To enable gpu support add "n_gpu_layers": -1 to DIR_ASSISTANT_LLAMA_CPP_OPTIONS!')
print("- For more options view https://llama-cpp-python.readthedocs.io/en/latest/api-reference/#llama_cpp.Llama")
