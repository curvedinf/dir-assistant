import argparse
import os
import json

from llama_cpp import Llama

from colorama import Fore, Style

from index import get_files_with_contents, create_file_index, search_index
from model_runners import LlamaCppRunner


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
   / /\ \  \___ \\\___ \  | |  \___ \   | | / /\ \ | . ` |  | |   
  / ____ \ ____) |___) |_| |_ ____) |  | |/ ____ \| |\  |  | |   
 /_/    \_\_____/_____/|_____|_____/   |_/_/    \_\_| \_|  |_|   
                                                                 
                                                                 
""" + Style.RESET_ALL)
    print(Style.BRIGHT + Fore.BLUE + "Type 'exit' to quit the conversation.\n\n" + Style.RESET_ALL)


if __name__ == '__main__':
    # Setup argparse for command line arguments
    parser = argparse.ArgumentParser(description='Process some integers.')
    parser.add_argument('--ignore', metavar='N', type=str, nargs='+',
                        help='A list of file paths to ignore')
    args = parser.parse_args()

    # Get the directory from the environment variable
    dir_assistant_root = os.environ['DIR_ASSISTANT_ROOT']

    # Path to the config.json file
    config_path = os.path.join(dir_assistant_root, 'config.json')

    # Open and read the config.json file
    with open(config_path, 'r') as config_file:
        config = json.load(config_file)

    print("Configuration loaded:", config)

    llm_model_file = os.path.join(dir_assistant_root, 'models', config['DIR_ASSISTANT_LLM_MODEL'])
    embed_model_file = os.path.join(dir_assistant_root, 'models', config['DIR_ASSISTANT_EMBED_MODEL'])
    context_file_ratio = config['DIR_ASSISTANT_CONTEXT_FILE_RATIO']
    llama_cpp_instructions = config['DIR_ASSISTANT_LLAMA_CPP_INSTRUCTIONS']
    llama_cpp_options = config['DIR_ASSISTANT_LLAMA_CPP_OPTIONS']
    llama_cpp_embed_options = config['DIR_ASSISTANT_LLAMA_CPP_EMBED_OPTIONS']

    # Find the files to index
    print("Finding files to index...")
    ignore_paths = args.ignore if args.ignore else []
    ignore_paths.extend(config['DIR_ASSISTANT_GLOBAL_IGNORES'])
    files_with_contents = get_files_with_contents('.', ignore_paths)
    if len(files_with_contents) == 0:
        print("No files found to index. Running anyway...")

    # Initialize the embedding model
    print("Loading embedding model...")
    embed = Llama(
        model_path=embed_model_file,
        embedding=True,
        pooling_type=2,  # CLS
        **llama_cpp_embed_options
    )
    llama_cpp_embed_chunk_size = embed.context_params.n_ctx

    # Create the file index
    print("Creating file embeddings and index...")
    index, chunks = create_file_index(embed, files_with_contents, llama_cpp_embed_chunk_size)

    # Set up the system instructions
    system_instructions = (f"{llama_cpp_instructions}\n\nThe user will ask questions relating \
    to files they will provide. Do your best to answer questions related to the these files. When \
    the user refers to files, always assume they want to know about the files they provided.")

    # Initialize the LLM model
    print("Loading local LLM model...")
    llm = LlamaCppRunner(
        model_path=llm_model_file,
        llama_cpp_options=llama_cpp_options,
        system_instructions=system_instructions,
        embed=embed,
        index=index,
        chunks=chunks,
        context_file_ratio=context_file_ratio
    )

    # Display the startup art
    display_startup_art()

    # Begin the conversation
    while True:
        # Get user input
        user_input = input(Style.BRIGHT + Fore.RED + 'You: \n\n' + Style.RESET_ALL)
        if user_input.lower() == 'exit':
            break
        llm.stream_chat(user_input)
