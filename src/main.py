import argparse
import os
import json
import sys
import mimetypes

import numpy as np
from faiss import IndexFlatL2
from llama_cpp import Llama

from colorama import Fore, Style


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
   / /\ \  \___  \\___ \  | |  \___ \   | | / /\ \ | . ` |  | |   
  / ____ \ ____) |___) |_| |_ ____) |  | |/ ____ \| |\  |  | |   
 /_/    \_\_____/_____/|_____|_____/   |_/_/    \_\_| \_|  |_|   
                                                                 
                                                                 
""" + Style.RESET_ALL)
    print(Style.BRIGHT + Fore.BLUE + "Type 'exit' to quit the conversation.\n\n" + Style.RESET_ALL)

def is_text_file(filepath):
    textchars = bytearray({7,8,9,10,12,13,27} | set(range(0x20, 0x100)) - {0x7f})
    is_binary_string = lambda bytes: bool(bytes.translate(None, textchars))
    return not is_binary_string(open(filepath, 'rb').read(1024))

def get_text_files(directory='.', ignore_paths=[]):
    text_files = []
    for root, dirs, files in os.walk(directory):
        dirs[:] = [d for d in dirs if os.path.join(root, d) not in ignore_paths]
        for i, filename in enumerate(files, start=1):
            filepath = os.path.join(root, filename)
            if os.path.isfile(filepath) and not any(ignore_path in filepath for ignore_path in ignore_paths) and is_text_file(filepath):
                text_files.append(filepath)
    return text_files

def get_files_with_contents(directory='.', ignore_paths=[]):
    files = get_text_files(directory, ignore_paths)
    files_with_contents = []
    for i, filepath in enumerate(files, start=1):
        try:
            with open(filepath, 'r') as file:
                contents = file.read()
        except UnicodeDecodeError:
            print(f"Skipping {filepath} because it is not a text file.")
        files_with_contents.append({
            "filepath": os.path.abspath(filepath),
            "contents": contents
        })
    return files_with_contents

def count_tokens(embed, text):
    return len(embed.tokenize(bytes(text, 'utf-8')))

def create_file_index(embed, files_with_contents, embed_chunk_size):
    # Split the files into chunks
    chunks = []
    for i, file_info in enumerate(files_with_contents, start=1):
        print(f'Indexing file {i}/{len(files_with_contents)}: {file_info["filepath"]}')
        filepath = file_info["filepath"]
        contents = file_info["contents"]
        lines = contents.split('\n')
        current_chunk = ""
        start_line_number = 1
        for line_number, line in enumerate(lines, start=start_line_number):
            chunk_header = f"@%@%@%@%@%@%\n\nUser file '{filepath}' lines {start_line_number}-{line_number}:\n\n"
            chunk_add_candidate = current_chunk + line + '\n'
            chunk_tokens = count_tokens(embed, chunk_header + chunk_add_candidate)
            if chunk_tokens > embed_chunk_size:
                chunks.append({"tokens": chunk_tokens, "text": chunk_header + current_chunk})
                current_chunk = ""
                start_line_number = line_number  # Update start_line_number
            else:
                current_chunk = chunk_add_candidate
        if current_chunk:  # Add the remaining content as the last chunk
            chunk_header = f"@%@%@%@%@%@%\n\nUser file '{filepath}' lines {start_line_number}-{len(lines)}:\n\n"
            chunks.append({"tokens": chunk_tokens, "text": chunk_header + current_chunk})

    # Create the embeddings
    print("File embeddings created. Total chunks:", len(chunks))
    print("Max size of an embedding chunk:", embed_chunk_size)

    embeddings = np.array([embed.create_embedding(chunk['text'])['data'][0]['embedding'] for chunk in chunks])
    index = IndexFlatL2(embeddings.shape[1])
    index.add(embeddings)
    return index, chunks

def search_index(embed, index, query, all_chunks):
    query_embedding = embed.create_embedding([query])['data'][0]['embedding']
    distances, indices = index.search(np.array([query_embedding]), 100)
    relevant_chunks = [all_chunks[i] for i in indices[0] if i != -1]
    return relevant_chunks

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
        print("No files found to index. Exiting...")
        exit()

    # Initialize the LLM model
    print("Loading LLM model...")
    llm = Llama(
        model_path=llm_model_file,
        **llama_cpp_options
    )
    llama_cpp_llm_context_size = llm.context_params.n_ctx

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
    system_instructions = (f"{llama_cpp_instructions}\n\nA set of the user's files are pasted below. Do your best to \
answer questions related to the these files. When the user is referring to files, always assume it is in context of \
the files below: \n\n")
    system_instructions_tokens = count_tokens(embed, system_instructions)

    chat_history = [{"role": "system", "content": None}]

    # Display the startup art
    display_startup_art()

    # Begin the conversation
    while True:
        # Get user input
        user_input = input(Style.BRIGHT + Fore.RED + 'You: \n\n' + Style.RESET_ALL)
        if user_input.lower() == 'exit':
            break
        print(Style.BRIGHT + Fore.GREEN + '\nAssistant: \n' + Style.RESET_ALL)
        sys.stdout.write(Style.BRIGHT + Fore.WHITE + '\r(thinking...)' + Style.RESET_ALL)
        sys.stdout.flush()
        # Get the LLM completion
        chat_history.append({"role": "user", "content": user_input, "tokens": count_tokens(embed, user_input)})

        # Get the relevant chunks and concatenate them up to half the LLM context size
        relevant_chunks = search_index(embed, index, user_input, chunks)
        relevant_full_text = ""
        chunk_total_tokens = 0
        for i, relevant_chunk in enumerate(relevant_chunks, start=1):
            chunk_total_tokens += relevant_chunk['tokens']
            if chunk_total_tokens + system_instructions_tokens >= llama_cpp_llm_context_size * context_file_ratio:
                break
            relevant_full_text += relevant_chunk['text'] + "\n\n"

        # Run the completion
        chat_history[0]["content"] = system_instructions + relevant_full_text
        output = llm.create_chat_completion(
            messages=chat_history
        )["choices"][0]["message"]

        # Add the completion to the chat history and remove old history if too large
        chat_history.append(output)
        chat_history[-1]["tokens"] = count_tokens(embed, output["content"])
        sum_of_tokens = sum([
            message["tokens"] for message in chat_history
            if message["role"] != "system"
        ])
        if sum_of_tokens > llama_cpp_llm_context_size - llama_cpp_llm_context_size * context_file_ratio:
            chat_history = chat_history.pop(1) # First user message

        # Display chat history
        sys.stdout.write(Style.BRIGHT + Fore.WHITE + '\r' + output["content"] + Style.RESET_ALL + '\n\n')
        sys.stdout.flush()