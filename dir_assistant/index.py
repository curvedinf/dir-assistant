import os

import numpy as np
from colorama import Fore, Style
from faiss import IndexFlatL2
from sqlitedict import SqliteDict

from dir_assistant.config import get_file_path

INDEX_CACHE_FILENAME = 'index_cache.sqlite'
INDEX_CACHE_PATH = '~/.cache/dir-assistant'


def count_tokens(embed, text):
    return len(embed.tokenize(bytes(text, 'utf-8')))


TEXT_CHARS = bytearray({7, 8, 9, 10, 12, 13, 27} | set(range(0x20, 0x100)) - {0x7f})
def is_text_file(filepath):
    return not bool(open(filepath, 'rb').read(1024).translate(None, TEXT_CHARS))


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


def get_files_with_contents(directory, ignore_paths, cache_db):
    text_files = get_text_files(directory, ignore_paths)
    files_with_contents = []
    with SqliteDict(cache_db, autocommit=True) as cache:
        for filepath in text_files:
            file_stat = os.stat(filepath)
            file_info = cache.get(filepath)
            if file_info and file_info['mtime'] == file_stat.st_mtime:
                files_with_contents.append(file_info)
            else:
                try:
                    with open(filepath, 'r') as file:
                        contents = file.read()
                except UnicodeDecodeError:
                    print(f"{Fore.LIGHTBLACK_EX}Skipping {filepath} because it is not a text file.{Style.RESET_ALL}")
                file_info = {
                    "filepath": os.path.abspath(filepath),
                    "contents": contents,
                    "mtime": file_stat.st_mtime
                }
                cache[filepath] = file_info
                files_with_contents.append(file_info)
    return files_with_contents


def create_file_index(embed, ignore_paths, embed_chunk_size):
    cache_db = get_file_path(INDEX_CACHE_PATH, INDEX_CACHE_FILENAME)

    print(f"{Fore.LIGHTBLACK_EX}Finding files to index...{Style.RESET_ALL}")
    files_with_contents = get_files_with_contents('.', ignore_paths, cache_db)
    chunks = []
    embeddings_list = []
    with SqliteDict(cache_db, autocommit=True) as cache:
        for file_info in files_with_contents:
            filepath = file_info['filepath']
            cached_chunks = cache.get(f"{filepath}_chunks")
            if cached_chunks and cached_chunks['mtime'] == file_info['mtime']:
                print(f"{Fore.LIGHTBLACK_EX}Using cached embeddings for {filepath}{Style.RESET_ALL}")
                chunks.extend(cached_chunks['chunks'])
                embeddings_list.extend(cached_chunks['embeddings'])
                continue

            contents = file_info['contents']
            file_chunks, file_embeddings = process_file(embed, filepath, contents, embed_chunk_size)
            chunks.extend(file_chunks)
            embeddings_list.extend(file_embeddings)
            cache[f"{filepath}_chunks"] = {
                'chunks': file_chunks,
                'embeddings': file_embeddings,
                'mtime': file_info['mtime']
            }

    print(f"{Fore.LIGHTBLACK_EX}Creating index from embeddings...{Style.RESET_ALL}")
    embeddings = np.array(embeddings_list)
    index = IndexFlatL2(embeddings.shape[1])
    index.add(embeddings)
    return index, chunks


def process_file(embed, filepath, contents, embed_chunk_size):
    lines = contents.split('\n')
    current_chunk = ''
    start_line_number = 1
    chunks = []
    embeddings_list = []

    print(f'{Fore.LIGHTBLACK_EX}Creating embeddings for {filepath}{Style.RESET_ALL}')
    for line_number, line in enumerate(lines, start=1):
        # Process each line individually if needed
        line_content = line
        while line_content:
            proposed_chunk = current_chunk + line_content + '\n'
            chunk_header = f"---------------\n\nUser file '{filepath}' lines {start_line_number}-{line_number}:\n\n"
            proposed_text = chunk_header + proposed_chunk
            chunk_tokens = count_tokens(embed, proposed_text)

            if chunk_tokens <= embed_chunk_size:
                current_chunk = proposed_chunk
                break  # The line fits in the current chunk, break out of the inner loop
            else:
                # Split line if too large for a new chunk
                if current_chunk == '':
                    split_point = find_split_point(embed, line_content, embed_chunk_size, chunk_header)
                    current_chunk = line_content[:split_point] + '\n'
                    line_content = line_content[split_point:]
                else:
                    # Save the current chunk as it is, and start a new one
                    chunks.append({
                        "tokens": count_tokens(embed, chunk_header + current_chunk),
                        "text": chunk_header + current_chunk,
                        "filepath": filepath,
                    })
                    embedding = embed.create_embedding(chunk_header + current_chunk)['data'][0]['embedding']
                    embeddings_list.append(embedding)
                    current_chunk = ''
                    start_line_number = line_number  # Next chunk starts from this line
                    # Do not break; continue processing the line

    # Add the remaining content as the last chunk
    if current_chunk:
        chunk_header = f"---------------\n\nUser file '{filepath}' lines {start_line_number}-{len(lines)}:\n\n"
        chunks.append({
            "tokens": count_tokens(embed, chunk_header + current_chunk),
            "text": chunk_header + current_chunk,
            "filepath": filepath,
        })
        embedding = embed.create_embedding(chunk_header + current_chunk)['data'][0]['embedding']
        embeddings_list.append(embedding)

    return chunks, embeddings_list


def find_split_point(embed, line_content, max_size, header):
    for split_point in range(1, len(line_content)):
        if count_tokens(embed, header + line_content[:split_point] + '\n') >= max_size:
            return split_point - 1
    return len(line_content)


def search_index(embed, index, query, all_chunks):
    query_embedding = embed.create_embedding([query])['data'][0]['embedding']
    distances, indices = index.search(np.array([query_embedding]), 100)
    relevant_chunks = [all_chunks[i] for i in indices[0] if i != -1]
    return relevant_chunks
