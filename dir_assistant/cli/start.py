import os
import sys
from colorama import Fore, Style
from llama_cpp import Llama
from prompt_toolkit import prompt
from prompt_toolkit.history import InMemoryHistory
from dir_assistant.assistant.file_watcher import start_file_watcher
from dir_assistant.assistant.index import create_file_index
from dir_assistant.assistant.lite_llm_assistant import LiteLLMAssistant
from dir_assistant.assistant.llama_cpp_assistant import LlamaCppAssistant
from dir_assistant.assistant.llama_cpp_embed import LlamaCppEmbed
from dir_assistant.cli.config import get_file_path

MODELS_PATH = os.path.expanduser("~/.local/share/dir-assistant/models")

def display_startup_art(commit_to_git):
    sys.stdout.write(
        f"""{Style.BRIGHT}{Fore.GREEN}
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
{Style.RESET_ALL}\n\n"""
    )
    sys.stdout.write(
        f"{Style.BRIGHT}{Fore.BLUE}Type 'exit' to quit the conversation.\n"
    )
    if commit_to_git:
        sys.stdout.write(
            f"{Style.BRIGHT}{Fore.BLUE}Type 'undo' to roll back the last commit.\n"
        )
    sys.stdout.write("\n")

def start(args, config_dict):
    # Load settings
    llm_model_file = get_file_path(config_dict["MODELS_PATH"], config_dict["LLM_MODEL"])
    embed_model_file = get_file_path(
        config_dict["MODELS_PATH"], config_dict["EMBED_MODEL"]
    )
    context_file_ratio = config_dict["CONTEXT_FILE_RATIO"]
    system_instructions = config_dict["SYSTEM_INSTRUCTIONS"]
    llama_cpp_options = config_dict["LLAMA_CPP_OPTIONS"]
    llama_cpp_embed_options = config_dict["LLAMA_CPP_EMBED_OPTIONS"]
    llama_cpp_completion_options = config_dict["LLAMA_CPP_COMPLETION_OPTIONS"]
    active_model_is_local = config_dict["ACTIVE_MODEL_IS_LOCAL"]
    lite_llm_model = config_dict["LITELLM_MODEL"]
    lite_llm_context_size = config_dict["LITELLM_CONTEXT_SIZE"]
    lite_llm_model_uses_system_message = config_dict[
        "LITELLM_MODEL_USES_SYSTEM_MESSAGE"
    ]
    lite_llm_pass_through_context_size = config_dict[
        "LITELLM_PASS_THROUGH_CONTEXT_SIZE"
    ]
    use_cgrag = config_dict["USE_CGRAG"]
    print_cgrag = config_dict["PRINT_CGRAG"]
    output_acceptance_retries = config_dict["OUTPUT_ACCEPTANCE_RETRIES"]
    commit_to_git = config_dict["COMMIT_TO_GIT"]

    if config_dict["EMBED_MODEL"] == "":
        print(
            """You must specify EMBED_MODEL. Use 'dir-assistant config open' and \
see readme for more information. Exiting..."""
        )
        exit(1)
    if active_model_is_local:
        if config_dict["LLM_MODEL"] == "":
            print(
                """You must specify LLM_MODEL.  Use 'dir-assistant config open' and \
    see readme for more information. Exiting..."""
            )
            exit(1)
    elif lite_llm_model == "":
        print(
            """You must specify LITELLM_MODEL. Use 'dir-assistant config open' and see readme \
for more information. Exiting..."""
        )
        exit(1)

    ignore_paths = args.i__ignore if args.i__ignore else []
    ignore_paths.extend(config_dict["GLOBAL_IGNORES"])

    # Initialize the embedding model
    print(f"{Fore.LIGHTBLACK_EX}Loading embedding model...{Style.RESET_ALL}")
    embed = LlamaCppEmbed(
        model_path=embed_model_file, embed_options=llama_cpp_embed_options
    )
    embed_chunk_size = embed.get_chunk_size()

    # Create the file index
    print(f"{Fore.LIGHTBLACK_EX}Creating file embeddings and index...{Style.RESET_ALL}")
    index, chunks = create_file_index(embed, ignore_paths, embed_chunk_size)

    # Set up the system instructions
    system_instructions_full = f"{system_instructions}\n\nThe user will ask questions relating \
    to files they will provide. Do your best to answer questions related to the these files. When \
    the user refers to files, always assume they want to know about the files they provided."

    # Initialize the LLM model
    if active_model_is_local:
        print(f"{Fore.LIGHTBLACK_EX}Loading local LLM model...{Style.RESET_ALL}")
        llm = LlamaCppAssistant(
            llm_model_file,
            llama_cpp_options,
            system_instructions_full,
            embed,
            index,
            chunks,
            context_file_ratio,
            output_acceptance_retries,
            use_cgrag,
            print_cgrag,
            commit_to_git,
            llama_cpp_completion_options,
        )
    else:
        sys.stdout.write(f"{Fore.LIGHTBLACK_EX}Loading remote LLM model...{Style.RESET_ALL}")
        llm = LiteLLMAssistant(
            lite_llm_model,
            lite_llm_model_uses_system_message,
            lite_llm_context_size,
            lite_llm_pass_through_context_size,
            system_instructions,
            embed,
            index,
            chunks,
            context_file_ratio,
            output_acceptance_retries,
            use_cgrag,
            print_cgrag,
            commit_to_git,
        )

    # Start file watcher
    watcher = start_file_watcher(
        ".", embed, ignore_paths, embed_chunk_size, llm.update_index_and_chunks
    )

    # Display the startup art
    display_startup_art(commit_to_git)

    # Initialize history for prompt input
    history = InMemoryHistory()

    # Begin the conversation
    while True:
        # Get user input
        sys.stdout.write(
            f"{Style.BRIGHT}{Fore.RED}You (Press ALT-Enter to submit): \n\n{Style.RESET_ALL}"
        )
        user_input = prompt("", multiline=True, history=history)

        if user_input.strip().lower() == "exit":
            break
        elif user_input.strip().lower() == "undo":
            os.system('git reset --hard HEAD~1')
            print(f"\n{Style.BRIGHT}Rolled back to the previous commit.{Style.RESET_ALL}\n\n")
            continue
        else:
            llm.stream_chat(user_input)