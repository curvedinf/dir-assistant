import argparse
import os
import json
import sys

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

def is_text_file(filepath):
    try:
        with open(filepath, 'tr') as file:
            file.read()
            return True
    except:
        return False

def get_text_files(directory='.', ignore_paths=[]):
    text_files = []
    for root, dirs, files in os.walk(directory):
        dirs[:] = [d for d in dirs if os.path.join(root, d) not in ignore_paths]
        for filename in files:
            filepath = os.path.join(root, filename)
            if os.path.isfile(filepath) and not any(ignore_path in filepath for ignore_path in ignore_paths) and is_text_file(filepath):
                text_files.append(filepath)
    return text_files

def get_files_with_contents(directory='.', ignore_paths=[]):
    files = get_text_files(directory, ignore_paths)
    files_with_contents = []
    for filepath in files:
        with open(filepath, 'r') as file:
            contents = file.read()
        files_with_contents.append({
            "filepath": os.path.abspath(filepath),
            "contents": contents
        })
    return files_with_contents

def create_file_index(embed, files_with_contents, embed_chunk_size):
    chunks = []
    for file_info in files_with_contents:
        filepath = file_info["filepath"]
        contents = file_info["contents"]
        lines = contents.split('\n')
        current_chunk = ""
        start_line_number = 1
        for line_number, line in enumerate(lines, start=start_line_number):
            line_size = len(line) + 1  # Adding 1 for the newline character
            if len(current_chunk) + line_size > embed_chunk_size:
                chunk_header = f"User file '{filepath}' lines {start_line_number}-{line_number-1}:\n\n"
                chunks.append(chunk_header + current_chunk)
                current_chunk = ""
                start_line_number = line_number  # Update start_line_number
            current_chunk += line + '\n'
        if current_chunk:  # Add the remaining content as the last chunk
            chunk_header = f"User file '{filepath}' lines {start_line_number}-{len(lines)}:\n\n"
            chunks.append(chunk_header + current_chunk)

    embeddings = np.array(embed.create_embedding(chunks))
    index = IndexFlatL2(embeddings.shape[1])
    index.add(embeddings)
    return index, chunks

def search_index(embed, index, query, all_chunks):
    query_embedding = embed.create_embedding([query])[0]
    distances, indices = index.search(np.array([query_embedding]), 100)
    relevant_chunks = [all_chunks[i] for i in indices[0]]
    return relevant_chunks

def concatenate_file_info(files_with_contents):
    concatenated_info = ""
    for file_info in files_with_contents:
        concatenated_info += f"User file '{file_info['filepath']}':\n\n```\n{file_info['contents']}\n```\n\n"
    return concatenated_info

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
llama_cpp_instructions = config['DIR_ASSISTANT_LLAMA_CPP_INSTRUCTIONS']
llama_cpp_options = config['DIR_ASSISTANT_LLAMA_CPP_OPTIONS']
llama_cpp_embed_options = config['DIR_ASSISTANT_LLAMA_CPP_OPTIONS']
llama_cpp_embed_chunk_size = llama_cpp_embed_options['n_ctx']

# Initialize the LLM model
llm = Llama(
    model_path=llm_model_file,
    **llama_cpp_options
)

# Initialize the embedding model
embed = Llama(
    model_path=embed_model_file,
    embedding=True,
    pooling_type=1, # Mean
    **llama_cpp_embed_options
)

# Set up the system instructions
ignore_paths = args.ignore if args.ignore else []
ignore_paths.extend(config['DIR_ASSISTANT_GLOBAL_IGNORES'])
files_with_contents = get_files_with_contents('.', ignore_paths)

# Display the files
print("Files found:")
for file_info in files_with_contents:
    print(file_info['filepath'])
print("")

# Create the file index
print("Creating file embeddings...")
index, chunks = create_file_index(embed, files_with_contents, llama_cpp_embed_chunk_size)

# Set up the system instructions
system_instructions = f"{llama_cpp_instructions}\n\nDo your best to answer questions related to the files below:\n\n"

chat_history = [{"role": "system", "content": None}]

if __name__ == '__main__':
    display_startup_art()
    print(Style.BRIGHT + Fore.BLUE + "Type 'exit' to quit the conversation.\n\n" + Style.RESET_ALL)
    while True:
        # Get user input
        user_input = input(Style.BRIGHT + Fore.RED + 'You: \n\n' + Style.RESET_ALL)
        if user_input.lower() == 'exit':
            break
        print(Style.BRIGHT + Fore.GREEN + '\nAssistant: \n' + Style.RESET_ALL)
        sys.stdout.write(Style.BRIGHT + Fore.WHITE + '\r(thinking...)' + Style.RESET_ALL)
        sys.stdout.flush()
        # Get the LLM completion
        chat_history.append({"role": "user", "content": user_input})

        relevant_files = search_index(embed, index, user_input, files_with_contents)
        relevant_full_text = concatenate_file_info(relevant_files)

        chat_history[0]["content"] = system_instructions + relevant_full_text
        output = llm.create_chat_completion(
            messages=chat_history
        )["choices"][0]["message"]
        chat_history.append(output)

        # Display chat history
        sys.stdout.write(Style.BRIGHT + Fore.WHITE + '\r' + output["content"] + Style.RESET_ALL + '\n\n')
        sys.stdout.flush()