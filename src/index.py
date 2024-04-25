import os

import numpy as np
from faiss import IndexFlatL2


def count_tokens(embed, text):
    return len(embed.tokenize(bytes(text, 'utf-8')))


def is_text_file(filepath):
    text_chars = bytearray({7, 8, 9, 10, 12, 13, 27} | set(range(0x20, 0x100)) - {0x7f})
    return not bool(open(filepath, 'rb').read(1024).translate(None, text_chars))


def get_text_files(directory='.', ignore_paths=[]):
    text_files = []
    for root, dirs, files in os.walk(directory):
        dirs[:] = [d for d in dirs if os.path.join(root, d) not in ignore_paths]
        for i, filename in enumerate(files, start=1):
            filepath = os.path.join(root, filename)
            if os.path.isfile(filepath) and not any(
                    ignore_path in filepath for ignore_path in ignore_paths) and is_text_file(filepath):
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
            chunk_header = f"---------------\n\nUser file '{filepath}' lines {start_line_number}-{line_number}:\n\n"
            chunk_add_candidate = current_chunk + line + '\n'
            chunk_tokens = count_tokens(embed, chunk_header + chunk_add_candidate)
            if chunk_tokens > embed_chunk_size:
                chunks.append({"tokens": chunk_tokens, "text": chunk_header + current_chunk})
                current_chunk = ""
                start_line_number = line_number  # Update start_line_number
            else:
                current_chunk = chunk_add_candidate
        if current_chunk:  # Add the remaining content as the last chunk
            chunk_header = f"---------------\n\nUser file '{filepath}' lines {start_line_number}-{len(lines)}:\n\n"
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
