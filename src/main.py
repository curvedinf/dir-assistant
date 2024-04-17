import os
import json
import sys
from llama_cpp import Llama
from colorama import Fore, Style


def display_startup_art():
    print(Style.BRIGHT + Fore.GREEN + """

  _____ _____ _____                                              
 |  __ \_   _|  __ \                                             
 | |  | || | | |__) |                                            
 | |  | || | |  _  /                                             
 | |__| || |_| | \ \                                             
 |_____/_____|_|_ \_\__ _____  _____ _______       _   _ _______ 
     /\    / ____/ ____|_   _|/ ____|__   __|/\   | \ | |__   __|
    /  \  | (___| (___   | | | (___    | |  /  \  |  \| |  | |   
   / /\ \  \___  \\___ \  | |  \___ \   | | / /\ \ | . ` |  | |   
  / ____ \ ____) |___) |_| |_ ____) |  | |/ ____ \| |\  |  | |   
 /_/    \_\_____/_____/|_____|_____/   |_/_/    \_\_| \_|  |_|   
                                                                 
                                                                 
""" + Style.RESET_ALL)

# Get the directory from the environment variable
dir_assistant_root = os.environ['DIR_ASSISTANT_ROOT']

# Path to the config.json file
config_path = os.path.join(dir_assistant_root, 'config.json')

# Open and read the config.json file
with open(config_path, 'r') as config_file:
    config = json.load(config_file)

print("Configuration loaded:", config)

model_file = os.path.join(dir_assistant_root, 'models', config['DIR_ASSISTANT_MODEL'])
llama_cpp_instructions = config['DIR_ASSISTANT_LLAMA_CPP_INSTRUCTIONS']
llama_cpp_options = config['DIR_ASSISTANT_LLAMA_CPP_OPTIONS']

# Initialize the AI model
llm = Llama(
    model_path=model_file,
    verbose=False,
    **llama_cpp_options
)

chat_history = [{"role": "system", "content": llama_cpp_instructions}]

if __name__ == '__main__':
    display_startup_art()
    print(Style.BRIGHT + Fore.BLUE + "Type 'exit' to quit the conversation.\n\n" + Style.RESET_ALL)
    while True:
        # Get user input
        user_input = input(Style.BRIGHT + Fore.RED + 'You       > ' + Style.RESET_ALL)
        if user_input.lower() == 'exit':
            break
        sys.stdout.write('\r' + Style.BRIGHT + Fore.GREEN + 'Assistant > '  + Fore.WHITE + '(thinking...)' + Style.RESET_ALL)
        sys.stdout.flush()
        # Get the LLM completion
        chat_history.append({"role": "user", "content": user_input})
        output = llm.create_chat_completion(
            messages=chat_history
        )["choices"][0]["message"]
        chat_history.append(output)

        # Display chat history
        sys.stdout.write('\r' + Style.BRIGHT + Fore.GREEN + 'Assistant > ' + Fore.WHITE + output["content"] + Style.RESET_ALL + '\n')
        sys.stdout.flush()