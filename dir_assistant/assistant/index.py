import os
import sys

import numpy as np
from colorama import Fore, Style
from faiss import IndexFlatL2
from sqlitedict import SqliteDict

from dir_assistant.cli.config import HISTORY_FILENAME, STORAGE_PATH, get_file_path

INDEX_CACHE_FILENAME = "index_cache.sqlite"
INDEX_CACHE_PATH = "~/.cache/dir-assistant"


TEXT_CHARS = bytearray({7, 8, 9, 10, 12, 13, 27} | set(range(0x20, 0x100)) - {0x7F})


def is_text_file(filepath):
    return not bool(open(filepath, "rb").read(1024).translate(None, TEXT_CHARS))


def get_text_files(directory=".", ignore_paths=[]):
    text_files = []
    for root, dirs, files in os.walk(directory):
        # Filter out directories that match ignore patterns
        dirs[:] = [d for d in dirs if not any(
            _is_path_ignored(os.path.join(root, d), ignore_path)
            for ignore_path in ignore_paths
        )]
        
        for i, filename in enumerate(files, start=1):
            filepath = os.path.join(root, filename)
            if (
                os.path.isfile(filepath)
                and not any(_is_path_ignored(filepath, ignore_path) for ignore_path in ignore_paths)
                and is_text_file(filepath)
            ):
                text_files.append(filepath)
    return text_files


def _is_path_ignored(filepath, ignore_pattern):
    """
    Check if a filepath matches an ignore pattern.
    Handles both file and directory patterns correctly.

    For the path /src/resources/swagger/swagger-core.js.map and ignore pattern resources/swagger/:
    Path components: ['src', 'resources', 'swagger', 'swagger-core.js.map']
    Ignore pattern components: ['resources', 'swagger']
    """
    # Normalize both paths
    norm_filepath = os.path.normpath(filepath)
    norm_ignore = os.path.normpath(ignore_pattern.rstrip('/'))
    
    # Split paths into components
    filepath_parts = norm_filepath.split(os.sep)
    ignore_parts = norm_ignore.split(os.sep)
    
    # Check if the ignore pattern matches any part of the path
    for i in range(len(filepath_parts) - len(ignore_parts) + 1):
        if filepath_parts[i:i+len(ignore_parts)] == ignore_parts:
            return True
    
    return False


def get_files_with_contents(directory, ignore_paths, cache_db):
    text_files = get_text_files(directory, ignore_paths)
    files_with_contents = []
    with SqliteDict(cache_db, autocommit=True) as cache:
        for filepath in text_files:
            file_stat = os.stat(filepath)
            file_info = cache.get(filepath)
            if file_info and file_info["mtime"] == file_stat.st_mtime:
                files_with_contents.append(file_info)
            else:
                try:
                    with open(filepath, "r") as file:
                        contents = file.read()
                except UnicodeDecodeError:
                    print(
                        f"{Fore.LIGHTBLACK_EX}Skipping {filepath} because it is not a text file.{Style.RESET_ALL}"
                    )
                file_info = {
                    "filepath": os.path.abspath(filepath),
                    "contents": contents,
                    "mtime": file_stat.st_mtime,
                }
                cache[filepath] = file_info
                files_with_contents.append(file_info)
    return files_with_contents


def create_file_index(
    embed, ignore_paths, embed_chunk_size, extra_dirs=[], verbose=False
):
    cache_db = get_file_path(INDEX_CACHE_PATH, INDEX_CACHE_FILENAME)

    # Start with current directory
    files_with_contents = get_files_with_contents(".", ignore_paths, cache_db)

    # Add files from additional folders
    for folder in extra_dirs:
        if os.path.exists(folder):
            folder_files = get_files_with_contents(folder, ignore_paths, cache_db)
            files_with_contents.extend(folder_files)
        else:
            if verbose:
                print(
                    f"{Fore.YELLOW}Warning: Additional folder {folder} does not exist{Style.RESET_ALL}"
                )

    if not files_with_contents:
        if verbose:
            print(
                f"{Fore.YELLOW}Warning: No text files found, creating first-file.txt...{Style.RESET_ALL}"
            )
        with open("first-file.txt", "w") as file:
            file.write(
                "Dir-assistant requires a file to be initialized, so this one was created because "
                "the directory was empty."
            )
        files_with_contents = get_files_with_contents(".", ignore_paths, cache_db)

    chunks = []
    embeddings_list = []
    with SqliteDict(cache_db, autocommit=True) as cache:
        for file_info in files_with_contents:
            filepath = file_info["filepath"]
            cached_chunks = cache.get(f"{filepath}_chunks")
            if cached_chunks and cached_chunks["mtime"] == file_info["mtime"]:
                if verbose:
                    print(
                        f"{Fore.LIGHTBLACK_EX}Using cached embeddings for {filepath}{Style.RESET_ALL}"
                    )
                chunks.extend(cached_chunks["chunks"])
                embeddings_list.extend(cached_chunks["embeddings"])
                continue

            contents = file_info["contents"]
            file_chunks, file_embeddings = process_file(
                embed, filepath, contents, embed_chunk_size, verbose
            )
            chunks.extend(file_chunks)
            embeddings_list.extend(file_embeddings)
            cache[f"{filepath}_chunks"] = {
                "chunks": file_chunks,
                "embeddings": file_embeddings,
                "mtime": file_info["mtime"],
            }

    if verbose:
        print(f"{Fore.LIGHTBLACK_EX}Creating index from embeddings...{Style.RESET_ALL}")
    embeddings = np.array(embeddings_list)
    index = IndexFlatL2(embeddings.shape[1])
    index.add(embeddings)
    return index, chunks


def process_file(embed, filepath, contents, embed_chunk_size, verbose=False):
    lines = contents.split("\n")
    current_chunk = ""
    start_line_number = 1
    chunks = []
    embeddings_list = []

    if verbose:
        print(
            f"{Fore.LIGHTBLACK_EX}Creating embeddings for {filepath}{Style.RESET_ALL}"
        )
    for line_number, line in enumerate(lines, start=1):
        # Process each line individually if needed
        line_content = line
        while line_content:
            proposed_chunk = current_chunk + line_content + "\n"
            chunk_header = f"---------------\n\nUser file '{filepath}' lines {start_line_number}-{line_number}:\n\n"
            proposed_text = chunk_header + proposed_chunk
            chunk_tokens = embed.count_tokens(proposed_text)

            if chunk_tokens <= embed_chunk_size:
                current_chunk = proposed_chunk
                break  # The line fits in the current chunk, break out of the inner loop
            else:
                # Split line if too large for a new chunk
                if current_chunk == "":
                    split_point = find_split_point(
                        embed, line_content, embed_chunk_size, chunk_header
                    )
                    current_chunk = line_content[:split_point] + "\n"
                    line_content = line_content[split_point:]
                else:
                    # Save the current chunk as it is, and start a new one
                    chunks.append(
                        {
                            "tokens": embed.count_tokens(chunk_header + current_chunk),
                            "text": chunk_header + current_chunk,
                            "filepath": filepath,
                        }
                    )
                    embedding = embed.create_embedding(chunk_header + current_chunk)
                    embeddings_list.append(embedding)
                    current_chunk = ""
                    start_line_number = line_number  # Next chunk starts from this line
                    # Do not break; continue processing the line

    # Add the remaining content as the last chunk
    if current_chunk:
        chunk_header = f"---------------\n\nUser file '{filepath}' lines {start_line_number}-{len(lines)}:\n\n"
        chunks.append(
            {
                "tokens": embed.count_tokens(chunk_header + current_chunk),
                "text": chunk_header + current_chunk,
                "filepath": filepath,
            }
        )
        embedding = embed.create_embedding(chunk_header + current_chunk)
        embeddings_list.append(embedding)

    return chunks, embeddings_list


def find_split_point(embed, line_content, max_size, header):
    for split_point in range(1, len(line_content)):
        if embed.count_tokens(header + line_content[:split_point] + "\n") >= max_size:
            return split_point - 1
    return len(line_content)


def search_index(embed, index, query, all_chunks):
    query_embedding = embed.create_embedding(query)
    distances, indices = index.search(
        np.array([query_embedding]), 100
    )  # 819,200 tokens max with default embedding
    relevant_chunks = [all_chunks[i] for i in indices[0] if i != -1]
    return relevant_chunks


def clear(args, config_dict):
    files = [
        get_file_path(INDEX_CACHE_PATH, INDEX_CACHE_FILENAME),
        get_file_path(STORAGE_PATH, HISTORY_FILENAME),
    ]
    for file in files:
        if os.path.exists(file):
            os.remove(file)
            sys.stdout.write(f"Deleted {file}\n")
        else:
            sys.stdout.write(f"{file} does not exist.\n")
