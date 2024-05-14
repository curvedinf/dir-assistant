import argparse
import os
import json

from llama_cpp import Llama

from colorama import Fore, Style

from index import create_file_index
from model_runners import LlamaCppRunner, LiteLLMRunner


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
    active_model_is_local = config['DIR_ASSISTANT_ACTIVE_MODEL_IS_LOCAL']
    lite_llm_model = config['DIR_ASSISTANT_LITELLM_MODEL']
    lite_llm_context_size = config['DIR_ASSISTANT_LITELLM_CONTEXT_SIZE']
    lite_llm_model_uses_system_message = config['DIR_ASSISTANT_LITELLM_MODEL_USES_SYSTEM_MESSAGE']
    index_cache_file = os.path.join(dir_assistant_root, 'index-cache.sqlite')
    use_cgrag = config['DIR_ASSISTANT_USE_CGRAG']

    if config['DIR_ASSISTANT_EMBED_MODEL'] == "":
        print("You must specify an embedding model in config.json. See readme for more information. Exiting...")
        exit(1)

    ignore_paths = args.ignore if args.ignore else []
    ignore_paths.extend(config['DIR_ASSISTANT_GLOBAL_IGNORES'])

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
    index, chunks = create_file_index(embed, ignore_paths, llama_cpp_embed_chunk_size, index_cache_file)

    # Set up the system instructions
    system_instructions = f"{llama_cpp_instructions}\n\nThe user will ask questions relating \
to files they will provide. Do your best to answer questions related to the these files. When \
the user refers to files, always assume they want to know about the files they provided."

    # Initialize the LLM model
    if active_model_is_local:
        print("Loading local LLM model...")
        if config['DIR_ASSISTANT_LLM_MODEL'] == "":
            print("You must specify an LLM model in config.json. See readme for more information. Exiting...")
            exit(1)
        llm = LlamaCppRunner(
            model_path=llm_model_file,
            llama_cpp_options=llama_cpp_options,
            system_instructions=system_instructions,
            embed=embed,
            index=index,
            chunks=chunks,
            context_file_ratio=context_file_ratio,
            use_cgrag=use_cgrag
        )
    else:
        print("Loading remote LLM model...")
        if lite_llm_model == "":
            print("You must specify a LiteLLM model in config.json. See readme for more information. Exiting...")
            exit(1)
        llm = LiteLLMRunner(
            lite_llm_model=lite_llm_model,
            lite_llm_model_uses_system_message=lite_llm_model_uses_system_message,
            lite_llm_context_size=lite_llm_context_size,
            system_instructions=system_instructions,
            embed=embed,
            index=index,
            chunks=chunks,
            context_file_ratio=context_file_ratio,
            use_cgrag=use_cgrag
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
