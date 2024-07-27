import argparse
import os

from config import check_config_file
from platform_setup import platform
from config import config
from start import start


if __name__ == '__main__':
    # Handle command line arguments
    parser = argparse.ArgumentParser(description="Chat with your current directory's files using a local or API LLM.")

    parser.add_argument(
        '-i'
        '--ignore',
        type=str,
        nargs='+',
        help='A list of space-separated filepaths to ignore.'
    )

    subparsers = parser.add_subparsers(dest='mode', help='Subcommand help')

    main_parser = subparsers.add_parser(
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

    setup_parser = subparsers.add_parser(
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

    config_parser = subparsers.add_parser('config', help='Configure dir-assistant settings.')
    config_parser.add_argument('option', help='Some option to configure.')

    args = parser.parse_args()

    # Always create the config file if it doesn't exist
    check_config_file()

    # Run the user's selected mode
    if args.mode == 'start' or args.mode is None:
        start(args)

    elif args.mode == 'platform':
        platform(args)

    elif args.mode == 'config':
        config(args)

    else:
        parser.print_help()