import json
import os

# Get user inputs
dir_assistant_model = input("Enter the gguf model filepath relative to dir-assistant/models: ")
dir_assistant_llama_cpp_options = input("Enter any options for llama.cpp to run with or press enter for a sane default: ")
if dir_assistant_llama_cpp_options == "":
    dir_assistant_llama_cpp_options = {
        "n_ctx": 0,
        "verbose": False,
    }
else:
    dir_assistant_llama_cpp_options = json.loads(dir_assistant_llama_cpp_options)
dir_assistant_llama_cpp_instructions = input("Enter the system instructions for your model or press enter for a sane default: ")
if dir_assistant_llama_cpp_instructions == "":
    dir_assistant_llama_cpp_instructions = "You are a helpful AI assistant. Do your best to answer questions related to files below:\n\n"

# Create the config dictionary
config = {
    "DIR_ASSISTANT_MODEL": dir_assistant_model,
    "DIR_ASSISTANT_LLAMA_CPP_OPTIONS": dir_assistant_llama_cpp_options,
    "DIR_ASSISTANT_LLAMA_CPP_INSTRUCTIONS": dir_assistant_llama_cpp_instructions,
    "DIR_ASSISTANT_GLOBAL_IGNORES": ['.git/', '.vscode/', 'node_modules/', 'build/', '.idea/']
}

# Write to config.json file
dir_assistant_root = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(dir_assistant_root, "config.json"), "w") as config_file:
    json.dump(config, config_file, indent=2)

print("Configuration saved to config.json.")
print('To enable gpu support add "n_gpu_layers": -1 to DIR_ASSISTANT_LLAMA_CPP_OPTIONS')
print("For more options view https://llama-cpp-python.readthedocs.io/en/latest/api-reference/#llama_cpp.Llama")