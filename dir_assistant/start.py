import os

from llama_cpp import Llama

from colorama import Fore, Style
from prompt_toolkit import prompt

from dir_assistant.index import create_file_index
from dir_assistant.model_runners import LlamaCppRunner, LiteLLMRunner
from dir_assistant.file_watcher import start_file_watcher
from dir_assistant.config import get_file_path


MODELS_PATH = os.path.expanduser('~/.local/share/dir-assistant/models')


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


def start(args, config_dict):
    # Load settings
    llm_model_file = get_file_path(MODELS_PATH, config_dict['LLM_MODEL'])
    embed_model_file = get_file_path(MODELS_PATH, config_dict['EMBED_MODEL'])
    context_file_ratio = config_dict['CONTEXT_FILE_RATIO']
    llama_cpp_instructions = config_dict['LLAMA_CPP_INSTRUCTIONS']
    llama_cpp_options = config_dict['LLAMA_CPP_OPTIONS']
    llama_cpp_embed_options = config_dict['LLAMA_CPP_EMBED_OPTIONS']
    active_model_is_local = config_dict['ACTIVE_MODEL_IS_LOCAL']
    lite_llm_model = config_dict['LITELLM_MODEL']
    lite_llm_context_size = config_dict['LITELLM_CONTEXT_SIZE']
    lite_llm_model_uses_system_message = config_dict['LITELLM_MODEL_USES_SYSTEM_MESSAGE']
    lite_llm_pass_through_context_size = config_dict['LITELLM_PASS_THROUGH_CONTEXT_SIZE']
    use_cgrag = config_dict['USE_CGRAG']
    print_cgrag = config_dict['PRINT_CGRAG']

    if embed_model_file == '':
        print("You must specify an embedding model in config.json. See readme for more information. Exiting...")
        exit(1)

    if active_model_is_local and llm_model_file == '':
        print("You must specify an local LLM model in config.json. See readme for more information. Exiting...")
        exit(1)

    ignore_paths = args.i__ignore if args.i__ignore else []
    ignore_paths.extend(config_dict['GLOBAL_IGNORES'])

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
        if config_dict['LLM_MODEL'] == "":
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