import os
import json

from llama_cpp import Llama

from colorama import Fore, Style
from prompt_toolkit import prompt

from index import create_file_index
from model_runners import LlamaCppRunner, LiteLLMRunner
from file_watcher import start_file_watcher


def display_startup_art():
    print(f"""{Style.BRIGHT}{Fore.GREEN}

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


{Style.RESET_ALL}""")
    print(f"{Style.BRIGHT}{Fore.BLUE}Type 'exit' to quit the conversation.\n\n{Style.RESET_ALL}")


def start(args):
    # Get the directory from the environment variable
    dir_assistant_root = os.environ['DIR_ASSISTANT_ROOT']

    # Path to the config.json file
    config_path = os.path.join(dir_assistant_root, 'config.json')

    # Open and read the config.json file
    with open(config_path, 'r') as config_file:
        config = json.load(config_file)

    print(f"{Fore.LIGHTBLACK_EX}Configuration loaded: {config}{Style.RESET_ALL}")

    llm_model_file = os.path.join(dir_assistant_root, 'models', config.get('DIR_ASSISTANT_LLM_MODEL', ''))
    embed_model_file = os.path.join(dir_assistant_root, 'models', config.get('DIR_ASSISTANT_EMBED_MODEL', ''))
    context_file_ratio = config.get('DIR_ASSISTANT_CONTEXT_FILE_RATIO', 0.5)
    llama_cpp_instructions = config.get('DIR_ASSISTANT_LLAMA_CPP_INSTRUCTIONS', 'You are a helpful AI assistant.')
    llama_cpp_options = config.get('DIR_ASSISTANT_LLAMA_CPP_OPTIONS', {})
    llama_cpp_embed_options = config.get('DIR_ASSISTANT_LLAMA_CPP_EMBED_OPTIONS', {})
    active_model_is_local = config.get('DIR_ASSISTANT_ACTIVE_MODEL_IS_LOCAL', False)
    lite_llm_model = config.get('DIR_ASSISTANT_LITELLM_MODEL', 'gemini/gemini-1.5-flash-latest')
    lite_llm_context_size = config.get('DIR_ASSISTANT_LITELLM_CONTEXT_SIZE', 500000)
    lite_llm_model_uses_system_message = config.get('DIR_ASSISTANT_LITELLM_MODEL_USES_SYSTEM_MESSAGE', False)
    lite_llm_pass_through_context_size = config.get('DIR_ASSISTANT_LITELLM_PASS_THROUGH_CONTEXT_SIZE', False)
    use_cgrag = config.get('DIR_ASSISTANT_USE_CGRAG', True)
    print_cgrag = config.get('DIR_ASSISTANT_PRINT_CGRAG', False)

    index_cache_file = os.path.join(dir_assistant_root, 'index-cache.sqlite')

    if embed_model_file == '':
        print("You must specify an embedding model in config.json. See readme for more information. Exiting...")
        exit(1)

    if active_model_is_local and llm_model_file == '':
        print("You must specify an local LLM model in config.json. See readme for more information. Exiting...")
        exit(1)

    ignore_paths = args.i__ignore if args.i__ignore else []
    ignore_paths.extend(config['DIR_ASSISTANT_GLOBAL_IGNORES'])

    # Initialize the embedding model
    print(f"{Fore.LIGHTBLACK_EX}Loading embedding model...{Style.RESET_ALL}")
    embed = Llama(
        model_path=embed_model_file,
        embedding=True,
        # pooling_type=2,  # CLS
        **llama_cpp_embed_options
    )
    llama_cpp_embed_chunk_size = embed.context_params.n_ctx

    # Create the file index
    print(f"{Fore.LIGHTBLACK_EX}Creating file embeddings and index...{Style.RESET_ALL}")
    index, chunks = create_file_index(embed, ignore_paths, llama_cpp_embed_chunk_size)

    # Set up the system instructions
    system_instructions = f"{llama_cpp_instructions}\n\nThe user will ask questions relating \
    to files they will provide. Do your best to answer questions related to the these files. When \
    the user refers to files, always assume they want to know about the files they provided."

    # Initialize the LLM model
    if active_model_is_local:
        print(f"{Fore.LIGHTBLACK_EX}Loading local LLM model...{Style.RESET_ALL}")
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
            use_cgrag=use_cgrag,
            print_cgrag=print_cgrag
        )
    else:
        print(f"{Fore.LIGHTBLACK_EX}Loading remote LLM model...{Style.RESET_ALL}")
        if lite_llm_model == "":
            print("You must specify a LiteLLM model in config.json. See readme for more information. Exiting...")
            exit(1)
        llm = LiteLLMRunner(
            lite_llm_model=lite_llm_model,
            lite_llm_model_uses_system_message=lite_llm_model_uses_system_message,
            lite_llm_context_size=lite_llm_context_size,
            lite_llm_pass_through_context_size=lite_llm_pass_through_context_size,
            system_instructions=system_instructions,
            embed=embed,
            index=index,
            chunks=chunks,
            context_file_ratio=context_file_ratio,
            use_cgrag=use_cgrag,
            print_cgrag=print_cgrag
        )

    # Start file watcher
    watcher = start_file_watcher(
        '.',
        embed,
        ignore_paths,
        llama_cpp_embed_chunk_size,
        index_cache_file,
        llm.update_index_and_chunks
    )

    # Display the startup art
    display_startup_art()

    # Begin the conversation
    while True:
        # Get user input
        print(f'{Style.BRIGHT}{Fore.RED}You (Press ALT-Enter to submit): \n{Style.RESET_ALL}')
        user_input = prompt('', multiline=True)
        if user_input.strip().lower() == 'exit':
            break
        llm.stream_chat(user_input)