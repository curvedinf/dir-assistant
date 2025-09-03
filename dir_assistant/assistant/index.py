import os
import sys

import numpy as np
from faiss import IndexFlatL2
from sqlitedict import SqliteDict
from wove import flatten, weave

from dir_assistant.cli.config import (
    CACHE_PATH,
    HISTORY_FILENAME,
    INDEX_CACHE_FILENAME,
    PREFIX_CACHE_FILENAME,
    PROMPT_HISTORY_FILENAME,
    STORAGE_PATH,
    get_file_path,
)

TEXT_CHARS = bytearray({7, 8, 9, 10, 12, 13, 27} | set(range(0x20, 0x100)) - {0x7F})


def is_text_file(filepath):
    return not bool(open(filepath, "rb").read(1024).translate(None, TEXT_CHARS))


def get_text_files(directory=".", ignore_paths=[]):
    text_files = []
    for root, dirs, files in os.walk(directory):
        dirs[:] = [d for d in dirs if os.path.join(root, d) not in ignore_paths]
        for i, filename in enumerate(files, start=1):
            filepath = os.path.join(root, filename)
            if (
                os.path.isfile(filepath)
                and not any(ignore_path in filepath for ignore_path in ignore_paths)
                and is_text_file(filepath)
            ):
                text_files.append(filepath)
    return text_files


def get_files_with_contents(directory, ignore_paths, cache_db, verbose):
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
                    if verbose:
                        sys.stdout.write(
                            f"Skipping {filepath} because it is not a text file.\n"
                        )
                        sys.stdout.flush()
                file_info = {
                    "filepath": os.path.abspath(filepath),
                    "contents": contents,
                    "mtime": file_stat.st_mtime,
                }
                cache[filepath] = file_info
                files_with_contents.append(file_info)
    return files_with_contents


def _process_file_task(file_info, cache_db, embed, embed_chunk_size, verbose):
    with SqliteDict(cache_db, autocommit=True) as cache:
        filepath = file_info["filepath"]
        cached_chunks = cache.get(f"{filepath}_chunks")

        if cached_chunks and cached_chunks["mtime"] == file_info["mtime"]:
            if verbose:
                sys.stdout.write(f"Using cached embeddings for {filepath}\n")
                sys.stdout.flush()
            return cached_chunks["chunks"], cached_chunks["embeddings"]

        contents = file_info["contents"]
        file_chunks, file_embeddings = process_file(
            embed, filepath, contents, embed_chunk_size, verbose
        )
        cache[f"{filepath}_chunks"] = {
            "chunks": file_chunks,
            "embeddings": file_embeddings,
            "mtime": file_info["mtime"],
        }
        return file_chunks, file_embeddings


def create_file_index(
    embed,
    ignore_paths,
    embed_chunk_size,
    config_dict,
    extra_dirs=[],
    verbose=False,
):
    cache_db = get_file_path(CACHE_PATH, INDEX_CACHE_FILENAME)
    files_with_contents = get_files_with_contents(".", ignore_paths, cache_db, verbose)

    for folder in extra_dirs:
        if os.path.exists(folder):
            folder_files = get_files_with_contents(
                folder, ignore_paths, cache_db, verbose
            )
            files_with_contents.extend(folder_files)
        elif verbose:
            sys.stdout.write(f"Warning: Additional folder {folder} does not exist\n")
            sys.stdout.flush()

    if not files_with_contents:
        if verbose:
            sys.stdout.write("Warning: No text files found, creating first-file.txt...\n")
            sys.stdout.flush()
        with open("first-file.txt", "w") as file:
            file.write(
                "Dir-assistant requires a file to be initialized, so this one was created because "
                "the directory was empty."
            )
        files_with_contents = get_files_with_contents(
            ".", ignore_paths, cache_db, verbose
        )

    workers = config_dict["INDEX_WORKERS"]
    limit_per_minute = config_dict["INDEX_MAX_REQUESTS_PER_MINUTE"]

    with weave() as w:

        @w.do(
            files_with_contents,
            workers=workers if workers > 0 else None,
            limit_per_minute=limit_per_minute if limit_per_minute > 0 else None,
        )
        def processed_files(item):
            return _process_file_task(
                item, cache_db, embed, embed_chunk_size, verbose
            )

    results = w.result.processed_files
    if not results:
        return None, []

    chunks, embeddings_list = zip(*results)
    chunks = flatten(chunks)
    embeddings_list = flatten(embeddings_list)

    if verbose:
        sys.stdout.write("Creating index from embeddings...\n")
        sys.stdout.flush()

    embeddings = np.array(embeddings_list)
    if embeddings.size == 0:
        return None, []

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
        sys.stdout.write(f"Creating embeddings for {filepath}\n")
        sys.stdout.flush()
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
                    # Add this line to prevent infinite loops
                    line_content = (
                        line_content.strip()
                    )  # Ensure there is actually some remaining string
                    if not line_content:
                        break
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
    low = 0
    high = len(line_content)
    while low < high:
        mid = (low + high) // 2
        if embed.count_tokens(header + line_content[:mid] + "\n") < max_size:
            low = mid + 1
        else:
            high = mid
    return low - 1


def search_index(embed, index, query, all_chunks):
    query_embedding = embed.create_embedding(query)
    try:
        distances, indices = index.search(
            np.array([query_embedding]), 100
        )  # 819,200 tokens max with default embedding
    except AssertionError as e:
        sys.stderr.write(
            f"Assertion error during index search. Did you change your embedding model? "
            f"Run 'dir_assistant clear' and try again.'\n"
        )
        raise e
    relevant_chunks = [
        (all_chunks[index], distances[0][iter]) for iter, index in enumerate(indices[0]) if index != -1
    ]
    return relevant_chunks


def clear(args, config_dict):
    files = [
        get_file_path(CACHE_PATH, INDEX_CACHE_FILENAME),
        get_file_path(STORAGE_PATH, HISTORY_FILENAME),
        get_file_path(CACHE_PATH, PREFIX_CACHE_FILENAME),
        get_file_path(CACHE_PATH, PROMPT_HISTORY_FILENAME),
    ]
    for file in files:
        if os.path.exists(file):
            os.remove(file)
            sys.stdout.write(f"Deleted {file}\n")
        else:
            sys.stdout.write(f"{file} does not exist.\n")
