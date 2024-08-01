import argparse

from dir_assistant.platform_setup import platform
from dir_assistant.config import config, load_config, config_open
from dir_assistant.start import start

def main():
	# Handle command line arguments
    parser = argparse.ArgumentParser(description="Chat with your current directory's files using a local or API LLM.")

    parser.add_argument(
        '-i'
        '--ignore',
        type=str,
        nargs='+',
        help='A list of space-separated filepaths to ignore.'
    )

    mode_subparsers = parser.add_subparsers(dest='mode', help='Dir-assistant run mode')

    # Start
    main_parser = mode_subparsers.add_parser(
        'start',
        help='Run dir-assistant in regular mode (Default if no subcommand is specified.)'
    )
    main_parser.add_argument(
        '-i'
        '--ignore',
        type=str,
        nargs='+',
        help='A list of space-separated filepaths to ignore.'
    )

    # Platform
    setup_parser = mode_subparsers.add_parser(
        'platform',
        help='Setup dir-assistant for a given hardware platform.',
        formatter_class=argparse.RawTextHelpFormatter
    )
    setup_parser.add_argument(
        'selection',
        type=str,
        choices=['cpu', 'cuda', 'rocm', 'metal', 'sycl', 'vulkan'],
        help='''The hardware acceleration platform to compile llama-cpp-python
for. System dependencies are required. Refer to 
https://github.com/abetlen/llama-cpp-python for system
dependency information.

cpu       - OpenBLAS (Most compatible)
cuda      - Nvidia
rocm      - AMD
metal     - Apple
sycl      - Intel
vulkan    - Vulkan'''
    )

    config_parser = mode_subparsers.add_parser('config', help='Print current configuration.')
    config_subparsers = config_parser.add_subparsers(dest='config_mode', help='Config subcommands.')

    config_open_parser = config_subparsers.add_parser('open', help='Open the configuration file in an editor.')


    args = parser.parse_args()

    config_dict = load_config()

    # Run the user's selected mode
    if args.mode == 'start' or args.mode is None:
        start(args, config_dict['DIR_ASSISTANT'])

    elif args.mode == 'platform':
        platform(args, config_dict['DIR_ASSISTANT'])

    elif args.mode == 'config':
        if args.config_mode == 'open':
            config_open(args, config_dict)
        else:
            config(args, config_dict)

    else:
        parser.print_help()


if __name__ == '__main__':
    main()
