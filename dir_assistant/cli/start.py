import os
import sys

import litellm
from colorama import Fore, Style
from prompt_toolkit import prompt
from prompt_toolkit.history import FileHistory
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.keys import Keys

from dir_assistant.assistant.file_watcher import start_file_watcher
from dir_assistant.assistant.index import create_file_index
from dir_assistant.assistant.lite_llm_assistant import LiteLLMAssistant
from dir_assistant.assistant.lite_llm_embed import LiteLlmEmbed
from dir_assistant.assistant.llama_cpp_assistant import LlamaCppAssistant
from dir_assistant.assistant.llama_cpp_embed import LlamaCppEmbed
from dir_assistant.cli.config import (
    HISTORY_FILENAME,
    STORAGE_PATH,
    VERSION,
    get_file_path,
)

litellm.suppress_debug_info = True

MODELS_PATH = os.path.expanduser("~/.local/share/dir-assistant/models")


def display_startup_art(commit_to_git, no_color=False):
    sys.stdout.write(
        f"""{Style.RESET_ALL if no_color else Style.BRIGHT}{Style.RESET_ALL if no_color else Fore.GREEN}
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
    color_prefix = Style.RESET_ALL if no_color else f"{Style.BRIGHT}{Fore.BLUE}"
    print(f"{color_prefix}Type 'exit' to quit the conversation.")
    if commit_to_git:
        print(f"{color_prefix}Type 'undo' to roll back the last commit.")
    print("")


def run_single_prompt(args, config_dict):
    llm = initialize_llm(args, config_dict, chat_mode=False)
    llm.initialize_history()
    response = llm.run_stream_processes(args.single_prompt, True)

    # Only print the final response
    sys.stdout.write(response)


def initialize_llm(args, config_dict, chat_mode=True):
    # Check if we're working with the full config dict or just DIR_ASSISTANT section
    config = (
        config_dict["DIR_ASSISTANT"] if "DIR_ASSISTANT" in config_dict else config_dict
    )

    # Main settings
    active_model_is_local = config["ACTIVE_MODEL_IS_LOCAL"]
    active_embed_is_local = config["ACTIVE_EMBED_IS_LOCAL"]
    context_file_ratio = config["CONTEXT_FILE_RATIO"]
    system_instructions = f"""{config["SYSTEM_INSTRUCTIONS"]}
The user is currently working in the following directory (CWD): {os.getcwd()}"""

    # Llama.cpp settings
    llm_model_file = get_file_path(config["MODELS_PATH"], config["LLM_MODEL"])
    embed_model_file = get_file_path(config["MODELS_PATH"], config["EMBED_MODEL"])
    llama_cpp_options = config["LLAMA_CPP_OPTIONS"]
    llama_cpp_embed_options = config["LLAMA_CPP_EMBED_OPTIONS"]
    llama_cpp_completion_options = config["LLAMA_CPP_COMPLETION_OPTIONS"]

    # LiteLLM settings
    lite_llm_context_size = config["LITELLM_CONTEXT_SIZE"]
    lite_llm_embed_context_size = config["LITELLM_EMBED_CONTEXT_SIZE"]
    lite_llm_completion_options = config["LITELLM_COMPLETION_OPTIONS"]
    lite_llm_embed_completion_options = config["LITELLM_EMBED_COMPLETION_OPTIONS"]
    lite_llm_model_uses_system_message = config["LITELLM_MODEL_USES_SYSTEM_MESSAGE"]
    lite_llm_pass_through_context_size = config["LITELLM_PASS_THROUGH_CONTEXT_SIZE"]
    lite_llm_embed_request_delay = float(config["LITELLM_EMBED_REQUEST_DELAY"])

    # Assistant settings
    use_cgrag = config["USE_CGRAG"]
    print_cgrag = config["PRINT_CGRAG"]
    output_acceptance_retries = config["OUTPUT_ACCEPTANCE_RETRIES"]
    commit_to_git = config["COMMIT_TO_GIT"]
    verbose = config["VERBOSE"] or args.verbose
    no_color = config["NO_COLOR"] or args.no_color

    # Check for basic missing model configs
    if active_model_is_local:
        if config["LLM_MODEL"] == "":
            print(
                """You must specify LLM_MODEL. Use 'dir-assistant config open' and \
    see readme for more information. Exiting..."""
            )
            exit(1)
    elif "model" not in lite_llm_completion_options or not lite_llm_completion_options["model"]:
        print(
            """You must specify LITELLM_COMPLETION_OPTIONS.model. Use 'dir-assistant config open' and see readme \
for more information. Exiting..."""
        )
        exit(1)

    # Check for basic missing embedding model configs
    if active_embed_is_local:
        if config["EMBED_MODEL"] == "":
            print(
                """You must specify EMBED_MODEL. Use 'dir-assistant config open' and \
see readme for more information. Exiting..."""
            )
            exit(1)
    elif "model" not in lite_llm_embed_completion_options or not lite_llm_embed_completion_options["model"]:
        print(
            """You must specify LITELLM_EMBED_COMPLETION_OPTIONS.model. Use 'dir-assistant config open' and \
see readme for more information. Exiting..."""
        )
        exit(1)

    ignore_paths = args.ignore if args.ignore else []
    ignore_paths.extend(config["GLOBAL_IGNORES"])

    extra_dirs = args.dirs if args.dirs else []

    # Initialize the embedding model
    if verbose and chat_mode:
        if not no_color:
            sys.stdout.write(f"{Fore.LIGHTBLACK_EX}")
        sys.stdout.write(f"Loading embedding model...\n")
        if not no_color:
            sys.stdout.write(f"{Style.RESET_ALL}")
        sys.stdout.flush()

    if active_embed_is_local:
        embed = LlamaCppEmbed(
            model_path=embed_model_file, embed_options=llama_cpp_embed_options
        )
        embed_chunk_size = embed.get_chunk_size()
    else:
        embed = LiteLlmEmbed(
            lite_llm_embed_completion_options=lite_llm_embed_completion_options,
            lite_llm_embed_context_size=lite_llm_embed_context_size,
            delay=lite_llm_embed_request_delay,
        )
        embed_chunk_size = lite_llm_embed_context_size

    # Create the file index
    if verbose or chat_mode:
        if not no_color:
            sys.stdout.write(f"{Fore.LIGHTBLACK_EX}")
        sys.stdout.write(f"Creating file embeddings and index...\n")
        if not no_color:
            sys.stdout.write(f"{Style.RESET_ALL}")
        sys.stdout.flush()

    index, chunks = create_file_index(
        embed, ignore_paths, embed_chunk_size, extra_dirs, verbose
    )

    # Set up the system instructions
    system_instructions_full = f"{system_instructions}\n\nThe user will ask questions relating \
    to files they will provide. Do your best to answer questions related to the these files. When \
    the user refers to files, always assume they want to know about the files they provided."

    # Initialize the LLM model
    if active_model_is_local:
        if verbose and chat_mode:
            if not no_color:
                sys.stdout.write(f"{Fore.LIGHTBLACK_EX}")
            sys.stdout.write(f"Loading local LLM model...\n")
            if not no_color:
                sys.stdout.write(f"{Style.RESET_ALL}")
            sys.stdout.flush()

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
            verbose=verbose,
            no_color=no_color,
            chat_mode=chat_mode,
        )
    else:
        if verbose and chat_mode:
            if not no_color:
                sys.stdout.write(f"{Fore.LIGHTBLACK_EX}")
            sys.stdout.write(f"Loading remote LLM model...\n")
            if not no_color:
                sys.stdout.write(f"{Style.RESET_ALL}")
            sys.stdout.flush()

        llm = LiteLLMAssistant(
            lite_llm_completion_options,
            lite_llm_context_size,
            lite_llm_model_uses_system_message,
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
            verbose=verbose,
            no_color=no_color,
            chat_mode=chat_mode,
        )

    return llm


def start(args, config_dict):
    single_prompt = args.single_prompt

    if single_prompt:
        # For single prompt mode, many options are ignored
        config_dict["NO_COLOR"] = True
        config_dict["VERBOSE"] = False
        config_dict["PRINT_CGRAG"] = False
        config_dict["COMMIT_TO_GIT"] = False

    llm = initialize_llm(args, config_dict, chat_mode=not single_prompt)
    llm.initialize_history()

    # If in single prompt mode, run the prompt and exit
    if single_prompt:
        llm.stream_chat(single_prompt)
        sys.stdout.write("\n")
        sys.stdout.flush()
        exit(0)

    # Get variables needed for file watcher and startup art
    is_full_config = "DIR_ASSISTANT" in config_dict
    config = config_dict["DIR_ASSISTANT"] if is_full_config else config_dict

    ignore_paths = args.ignore if args.ignore else []
    ignore_paths.extend(config["GLOBAL_IGNORES"])
    commit_to_git = config["COMMIT_TO_GIT"]
    embed = llm.embed
    active_embed_is_local = config["ACTIVE_EMBED_IS_LOCAL"]
    embed_chunk_size = (
        config["LITELLM_EMBED_CONTEXT_SIZE"]
        if not active_embed_is_local
        else embed.get_chunk_size()
    )

    # Start file watcher. It is running in another thread after this.
    watcher = start_file_watcher(
        ".", embed, ignore_paths, embed_chunk_size, llm.update_index_and_chunks
    )

    # Display the startup art
    no_color = llm.no_color
    display_startup_art(commit_to_git, no_color=no_color)

    # Initialize history for prompt input
    history = FileHistory(get_file_path(STORAGE_PATH, HISTORY_FILENAME))

    # Begin the conversation
    while True:
        # Get user input
        color_prefix = "" if no_color else f"{Style.BRIGHT}{Fore.RED}"
        color_suffix = "" if no_color else Style.RESET_ALL
        sys.stdout.write(
            f"{color_prefix}You (Press ALT-Enter, OPT-Enter, or CTRL-O to submit): \n\n{color_suffix}"
        )
        # Configure key bindings for Option-Enter on macOS
        bindings = KeyBindings()

        @bindings.add(Keys.Escape, Keys.Enter)
        @bindings.add("escape", "enter")  # For Option-Enter on macOS
        def _(event):
            event.current_buffer.validate_and_handle()

        user_input = prompt("", multiline=True, history=history, key_bindings=bindings)

        if user_input.strip().lower() == "exit":
            break
        elif user_input.strip().lower() == "undo":
            os.system("git reset --hard HEAD~1")
            color_prefix = "" if args.no_color else Style.BRIGHT
            print(
                f"\n{color_prefix}Rolled back to the previous commit.{color_suffix}\n\n"
            )
            continue
        else:
            llm.stream_chat(user_input)
