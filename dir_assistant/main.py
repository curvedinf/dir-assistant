import argparse
import warnings

warnings.filterwarnings("ignore", category=SyntaxWarning)

from dir_assistant.assistant.index import clear
from dir_assistant.cli.config import config, config_open, load_config
from dir_assistant.cli.models import (
    models_download_embed,
    models_download_llm,
    models_open,
    models_print,
)
from dir_assistant.cli.platform_setup import platform
from dir_assistant.cli.setkey import setkey
from dir_assistant.cli.start import start


def main():
    # Setup argument parsing
    parser = argparse.ArgumentParser(
        description="Chat with your current directory's files using a local or API LLM."
    )

    parser.add_argument(
        "-i" "--ignore",
        type=str,
        nargs="+",
        help="A list of space-separated filepaths to ignore.",
    )
    parser.add_argument(
        "-d" "--dirs",
        type=str,
        nargs="+",
        help="A list of space-separated directories to work on. Your current directory will always be used.",
    )

    mode_subparsers = parser.add_subparsers(
        dest="mode", help="Run dir-assistant in regular mode"
    )

    # Start
    start_parser = mode_subparsers.add_parser(
        "start",
        help="Run dir-assistant in regular mode.",
    )
    start_parser.add_argument(
        "-i" "--ignore",
        type=str,
        nargs="+",
        help="A list of space-separated filepaths to ignore.",
    )
    start_parser.add_argument(
        "-d" "--dirs",
        type=str,
        nargs="+",
        help="A list of space-separated directories to work on. Your current directory will always be used.",
    )
    start_subparsers = start_parser.add_subparsers(
        dest="start_mode", help="Operation mode for the config subcommand."
    )
    start_default_parser = start_subparsers.add_parser(
        "", help="Run dir-assistant in regular mode."
    )
    start_regular_parser = start_subparsers.add_parser(
        "regular", help="Run dir-assistant in regular mode."
    )

    # Platform
    setup_parser = mode_subparsers.add_parser(
        "platform",
        help="Setup dir-assistant for a given hardware platform.",
        formatter_class=argparse.RawTextHelpFormatter,
    )
    setup_choices = ["cpu", "cuda", "rocm", "metal", "sycl", "vulkan"]
    setup_parser.add_argument(
        "selection",
        type=str,
        choices=setup_choices,
        help="""The hardware acceleration platform to compile llama-cpp-python \
for. System dependencies may be required. Refer to \
https://github.com/abetlen/llama-cpp-python for system dependency information.

cpu       - OpenBLAS (Most compatible, default)
cuda      - Nvidia
rocm      - AMD
metal     - Apple
sycl      - Intel
vulkan    - Vulkan""",
    )
    setup_parser.add_argument(
        "--pipx",
        action="store_true",
        help="Compatibility option for Ubuntu 24.04. Install using pipx instead of pip.",
    )

    # Config
    config_parser = mode_subparsers.add_parser(
        "config", help="Configuration-related options."
    )
    config_subparsers = config_parser.add_subparsers(
        dest="config_mode", help="Operation mode for the config subcommand."
    )

    config_default_parser = config_subparsers.add_parser(
        "", help="Print the current configuration"
    )
    config_print_parser = config_subparsers.add_parser(
        "print", help="Print the current configuration"
    )
    config_open_parser = config_subparsers.add_parser(
        "open", help="Open the configuration file in an editor."
    )

    # Models
    models_parser = mode_subparsers.add_parser(
        "models",
        help="Download or configure models for dir-assistant.",
    )
    models_subparsers = models_parser.add_subparsers(
        dest="models_mode", help="Operation mode for the model subcommand."
    )

    models_default_parser = models_subparsers.add_parser(
        "", help="Open the models directory in a file browser."
    )
    models_open_parser = models_subparsers.add_parser(
        "open", help="Open the models directory in a file browser."
    )
    models_print_parser = models_subparsers.add_parser(
        "print", help="Print the models directory."
    )
    models_download_embed_parser = models_subparsers.add_parser(
        "download-embed",
        help="Download a local embedding model. (nomic-embed-text-v1.5.Q5_K_M.gguf)",
    )
    models_download_llm_parser = models_subparsers.add_parser(
        "download-llm",
        help="Download a local LLM model. (Phi-3.1-mini-128k-instruct-Q5_K_L.gguf)",
    )

    # Clear
    clear_parser = mode_subparsers.add_parser(
        "clear",
        help="Clear the index cache. (Useful if upgrading to a new version of dir-assistant)",
    )

    # Setkey
    setkey_parser = mode_subparsers.add_parser("setkey", help="""Set an API key.""")
    setkey_parser.add_argument(
        "api_name", type=str, help="The API name (e.g., GEMINI_API_KEY)."
    )
    setkey_parser.add_argument("api_key", type=str, help="The API key to set.")

    # Parse the arguments
    args = parser.parse_args()

    if args.mode != "config" or args.config_mode != "open":
        # Do not load the config file if the user is opening the config file.
        # The toml may be malformed, so we don't want to crash before it is opened.
        config_dict = load_config()

    # Run the user's selected mode
    if args.mode == "start" or args.mode is None:
        start(args, config_dict["DIR_ASSISTANT"])
    elif args.mode == "platform":
        platform(args, config_dict["DIR_ASSISTANT"])
    elif args.mode == "config":
        if args.config_mode == "print" or args.config_mode is None:
            config(args, config_dict)
        elif args.config_mode == "open":
            config_open(args)
        else:
            config_parser.print_help()
    elif args.mode == "models":
        if args.models_mode == "open" or args.models_mode is None:
            models_open(args, config_dict)
        elif args.models_mode == "print":
            models_print(args, config_dict)
        elif args.models_mode == "download-embed":
            models_download_embed(args, config_dict)
        elif args.models_mode == "download-llm":
            models_download_llm(args, config_dict)
        else:
            models_parser.print_help()
    elif args.mode == "clear":
        clear(args, config_dict)
    elif args.mode == "setkey":
        setkey(args, config_dict)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
