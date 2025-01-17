import os
import sys

from colorama import Fore, Style
from prompt_toolkit import prompt
from prompt_toolkit.history import InMemoryHistory
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.keys import Keys

from dir_assistant.assistant.file_watcher import start_file_watcher
from dir_assistant.assistant.index import create_file_index
from dir_assistant.assistant.lite_llm_assistant import LiteLLMAssistant
from dir_assistant.assistant.lite_llm_embed import LiteLlmEmbed
from dir_assistant.assistant.llama_cpp_assistant import LlamaCppAssistant
from dir_assistant.assistant.llama_cpp_embed import LlamaCppEmbed
from dir_assistant.cli.config import get_file_path, load_config

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

def run_single_prompt(args, config_dict):
    llm = initialize_llm(args, config_dict)
    llm.initialize_history()
    response = llm.run_stream_processes(args.single_prompt, True)
    
    # Only print the final response
    print(response)

def get_config_overrides(config_dict):
    """Get configuration overrides from both environment variables and command line arguments"""
    overrides = {}
    
    # Check if we're working with the full config dict or just DIR_ASSISTANT section
    is_full_config = "DIR_ASSISTANT" in config_dict
    config = config_dict["DIR_ASSISTANT"] if is_full_config else config_dict
    
    # Process all environment variables that match config keys
    for key in os.environ:
        if key in config:  # Only process if it's a valid config key
            env_value = os.environ[key]
            overrides[key] = convert_value(env_value)
    
    return overrides

def convert_value(value_str):
    """Convert string values to appropriate Python types"""
    # Handle boolean values
    if value_str.lower() in ('true', 'false'):
        return value_str.lower() == 'true'
    # Handle integer values
    elif value_str.isdigit():
        return int(value_str)
    # Handle float values
    elif value_str.replace('.', '').isdigit():
        return float(value_str)
    # Keep as string if no other type matches
    return value_str

def parse_config_override(override_str):
    """Parse a key=value config override string"""
    try:
        key, value = override_str.split('=', 1)
        return key.strip(), convert_value(value.strip())
    except ValueError:
        raise ValueError(f"Invalid config override format: {override_str}. Use KEY=VALUE format.")

def initialize_llm(args, config_dict):
    # Check if we're working with the full config dict or just DIR_ASSISTANT section
    is_full_config = "DIR_ASSISTANT" in config_dict
    config = config_dict["DIR_ASSISTANT"] if is_full_config else config_dict
    
    # Apply any environment variable overrides to config
    overrides = get_config_overrides(config_dict)
    
    # Update config with overrides
    for key, value in overrides.items():
        if args.verbose:
            print(f"Debug: Applying config override {key}={value}")
        config[key] = value
    
    # Main settings
    active_model_is_local = config["ACTIVE_MODEL_IS_LOCAL"]
    active_embed_is_local = config["ACTIVE_EMBED_IS_LOCAL"]
    context_file_ratio = config["CONTEXT_FILE_RATIO"]
    system_instructions = config["SYSTEM_INSTRUCTIONS"]

    # Llama.cpp settings
    llm_model_file = get_file_path(config["MODELS_PATH"], config["LLM_MODEL"])
    embed_model_file = get_file_path(
        config["MODELS_PATH"], config["EMBED_MODEL"]
    )
    llama_cpp_options = config["LLAMA_CPP_OPTIONS"]
    llama_cpp_embed_options = config["LLAMA_CPP_EMBED_OPTIONS"]
    llama_cpp_completion_options = config["LLAMA_CPP_COMPLETION_OPTIONS"]

    # LiteLLM settings
    lite_llm_model = config["LITELLM_MODEL"]
    lite_llm_context_size = config["LITELLM_CONTEXT_SIZE"]
    lite_llm_model_uses_system_message = config["LITELLM_MODEL_USES_SYSTEM_MESSAGE"]
    lite_llm_pass_through_context_size = config["LITELLM_PASS_THROUGH_CONTEXT_SIZE"]
    lite_llm_embed_model = config["LITELLM_EMBED_MODEL"]
    lite_llm_embed_chunk_size = config["LITELLM_EMBED_CHUNK_SIZE"]
    lite_llm_embed_request_delay = float(config["LITELLM_EMBED_REQUEST_DELAY"])

    # Assistant settings
    use_cgrag = config["USE_CGRAG"]
    print_cgrag = config["PRINT_CGRAG"]
    output_acceptance_retries = config["OUTPUT_ACCEPTANCE_RETRIES"]
    commit_to_git = config["COMMIT_TO_GIT"]

    # Check for basic missing model configs
    if active_model_is_local:
        if config["LLM_MODEL"] == "":
            print(
                """You must specify LLM_MODEL. Use 'dir-assistant config open' and \
    see readme for more information. Exiting..."""
            )
            exit(1)
    elif lite_llm_model == "":
        print(
            """You must specify LITELLM_MODEL. Use 'dir-assistant config open' and see readme \
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
    elif lite_llm_embed_model == "":
        print(
            """You must specify LITELLM_EMBED_MODEL. Use 'dir-assistant config open' and \
see readme for more information. Exiting..."""
        )
        exit(1)

    ignore_paths = args.ignore if args.ignore else []
    ignore_paths.extend(config["GLOBAL_IGNORES"])

    extra_dirs = args.dirs if args.dirs else []

    # Initialize the embedding model
    if args.verbose:
        print(f"{Fore.LIGHTBLACK_EX}Loading embedding model...{Style.RESET_ALL}")
    if active_embed_is_local:
        embed = LlamaCppEmbed(
            model_path=embed_model_file, embed_options=llama_cpp_embed_options
        )
        embed_chunk_size = embed.get_chunk_size()
    else:
        embed = LiteLlmEmbed(
            lite_llm_embed_model=lite_llm_embed_model,
            chunk_size=lite_llm_embed_chunk_size,
            delay=lite_llm_embed_request_delay,
        )
        embed_chunk_size = lite_llm_embed_chunk_size

    # Create the file index
    if args.verbose:
        print(f"{Fore.LIGHTBLACK_EX}Creating file embeddings and index...{Style.RESET_ALL}")
    index, chunks = create_file_index(embed, ignore_paths, embed_chunk_size, extra_dirs, args.verbose)

    # Set up the system instructions
    system_instructions_full = f"{system_instructions}\n\nThe user will ask questions relating \
    to files they will provide. Do your best to answer questions related to the these files. When \
    the user refers to files, always assume they want to know about the files they provided."

    # Initialize the LLM model
    if active_model_is_local:
        if args.verbose:
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
        if args.verbose:
            sys.stdout.write(
                f"{Fore.LIGHTBLACK_EX}Loading remote LLM model...{Style.RESET_ALL}"
            )
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
            verbose=args.verbose,
        )

    return llm

def start(args, config_dict):
    llm = initialize_llm(args, config_dict)
    llm.initialize_history()

    # Get variables needed for file watcher and startup art
    is_full_config = "DIR_ASSISTANT" in config_dict
    config = config_dict["DIR_ASSISTANT"] if is_full_config else config_dict
    
    ignore_paths = args.ignore if args.ignore else []
    ignore_paths.extend(config["GLOBAL_IGNORES"])
    commit_to_git = config["COMMIT_TO_GIT"]
    embed = llm.embed
    active_embed_is_local = config["ACTIVE_EMBED_IS_LOCAL"]
    embed_chunk_size = config["LITELLM_EMBED_CHUNK_SIZE"] if not active_embed_is_local else embed.get_chunk_size()

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
            f"{Style.BRIGHT}{Fore.RED}You (Press ALT-Enter, OPT-Enter, or CTRL-O to submit): \n\n{Style.RESET_ALL}"
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
            print(
                f"\n{Style.BRIGHT}Rolled back to the previous commit.{Style.RESET_ALL}\n\n"
            )
            continue
        else:
            llm.stream_chat(user_input)
