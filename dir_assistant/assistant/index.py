import hashlib
import json
import os
import sys

import numpy as np
from faiss import IndexFlatIP, IndexFlatL2, normalize_L2
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


def get_files_with_contents(directory, ignore_paths, cache_db, embed_config, verbose):
    text_files = get_text_files(directory, ignore_paths)
    files_with_contents = []
    with SqliteDict(cache_db, autocommit=True) as cache:
        for filepath in text_files:
            file_stat = os.stat(filepath)
            cache_key = f"{embed_config}-{filepath}"
            file_info = cache.get(cache_key)
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
                cache[cache_key] = file_info
                files_with_contents.append(file_info)
    return files_with_contents


def create_file_index(
    embed,
    ignore_paths,
    embed_chunk_size,
    extra_dirs=[],
    verbose=False,
    index_concurrent_files=1,
    index_max_files_per_minute=60,
    index_chunk_workers=1,
    index_max_chunk_requests_per_minute=60,
):
    config_str = json.dumps(embed.get_config(), sort_keys=True)
    embed_config = hashlib.sha256(config_str.encode("utf-8")).hexdigest()
    cache_db = get_file_path(CACHE_PATH, INDEX_CACHE_FILENAME)
    # Start with current directory
    files_with_contents = get_files_with_contents(
        ".", ignore_paths, cache_db, embed_config, verbose
    )
    # Add files from additional folders
    for folder in extra_dirs:
        if os.path.exists(folder):
            folder_files = get_files_with_contents(
                folder, ignore_paths, cache_db, embed_config, verbose
            )
            files_with_contents.extend(folder_files)
        else:
            if verbose:
                sys.stdout.write(
                    f"Warning: Additional folder {folder} does not exist\n"
                )
                sys.stdout.flush()
    if not files_with_contents:
        if verbose:
            sys.stdout.write(
                f"Warning: No text files found, creating first-file.txt...\n"
            )
            sys.stdout.flush()
        with open("first-file.txt", "w") as file:
            file.write(
                "Dir-assistant requires a file to be initialized, so this one was created because "
                "the directory was empty."
            )
        files_with_contents = get_files_with_contents(
            ".", ignore_paths, cache_db, verbose
        )
    with weave() as w:

        @w.do(
            files_with_contents,
            workers=index_concurrent_files,
            limit_per_minute=index_max_files_per_minute,
        )
        def process_file_concurrently(item):
            with SqliteDict(cache_db, autocommit=True) as cache:
                filepath = item["filepath"]
                cache_key = f"{embed_config}-{filepath}_chunks"
                cached_chunks = cache.get(cache_key)
                if cached_chunks and cached_chunks["mtime"] == item["mtime"]:
                    if verbose:
                        sys.stdout.write(f"Using cached embeddings for {filepath}\n")
                        sys.stdout.flush()
                    return cached_chunks["chunks"], cached_chunks["embeddings"]
                contents = item["contents"]
                file_chunks, file_embeddings = process_file(
                    embed,
                    filepath,
                    contents,
                    embed_chunk_size,
                    verbose,
                    index_chunk_workers,
                    index_max_chunk_requests_per_minute,
                )
                cache[cache_key] = {
                    "chunks": file_chunks,
                    "embeddings": file_embeddings,
                    "mtime": item["mtime"],
                }
                return file_chunks, file_embeddings

    # w.result.process_file_concurrently is a list of (chunks, embeddings) tuples
    processed_results = w.result.process_file_concurrently
    # Separate the chunks and embeddings from the processed results
    all_chunks = flatten([res[0] for res in processed_results if res])
    all_embeddings = flatten([res[1] for res in processed_results if res])
    if verbose:
        sys.stdout.write("Creating index from embeddings...\n")
        sys.stdout.flush()
    if not all_embeddings:
        # Handle case with no embeddings to avoid error on np.array
        return None, []
    embeddings = np.array(all_embeddings).astype("float32")
    # Big change -- embeddings are now normalized if not already
    normalize_L2(embeddings)
    # Big change -- use inner product (dot product) instead of L2 distance
    index = IndexFlatIP(embeddings.shape[1])
    index.add(embeddings)
    return index, all_chunks


def process_file(
    embed,
    filepath,
    contents,
    embed_chunk_size,
    verbose=False,
    index_chunk_workers=1,
    index_max_chunk_requests_per_minute=60,
):
    lines = contents.split("\n")
    raw_chunks = []
    current_chunk = ""
    start_line_number = 1
    for line_number, line in enumerate(lines, start=1):
        line_content = line
        while line_content:
            proposed_chunk = current_chunk + line_content + "\n"
            chunk_header = f"---------------\n\nUser file '{filepath}' lines {start_line_number}-{line_number}:\n\n"
            proposed_text = chunk_header + proposed_chunk
            chunk_tokens = embed.count_tokens(proposed_text)
            if chunk_tokens <= embed_chunk_size:
                current_chunk = proposed_chunk
                break
            else:
                if current_chunk == "":
                    split_point = find_split_point(
                        embed, line_content, embed_chunk_size, chunk_header
                    )
                    current_chunk = line_content[:split_point] + "\n"
                    line_content = line_content[split_point:]
                else:
                    raw_chunks.append(
                        {
                            "text": chunk_header + current_chunk,
                            "filepath": filepath,
                        }
                    )
                    current_chunk = ""
                    start_line_number = line_number
                    line_content = line_content.strip()
                    if not line_content:
                        break
    if current_chunk:
        chunk_header = f"---------------\n\nUser file '{filepath}' lines {start_line_number}-{len(lines)}:\n\n"
        raw_chunks.append(
            {
                "text": chunk_header + current_chunk,
                "filepath": filepath,
            }
        )
    if verbose:
        sys.stdout.write(f"Creating embeddings for {filepath}\n")
        sys.stdout.flush()
    with weave() as w:

        @w.do(
            raw_chunks,
            workers=index_chunk_workers,
            limit_per_minute=index_max_chunk_requests_per_minute,
        )
        def create_embedding_concurrently(item):
            embedding = embed.create_embedding(item["text"])
            return item, embedding

    processed_chunks = []
    embeddings_list = []
    for chunk_info, embedding in w.result.create_embedding_concurrently:
        chunk_info["tokens"] = embed.count_tokens(chunk_info["text"])
        processed_chunks.append(chunk_info)
        embeddings_list.append(embedding)
    return processed_chunks, embeddings_list


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


import sys

import numpy as np


def search_index(embed, index, query, all_chunks, max_k=1000, max_distance=2.0):
    """
    Searches the FAISS index for vectors within a given distance and limits the results.
    """
    query_embedding = embed.create_embedding(query)
    query_vector = np.array([query_embedding]).astype("float32")
    normalize_L2(query_vector)

    try:
        lims, distances, indices = index.range_search(query_vector, max_distance)
    except (AssertionError, RuntimeError) as e:
        sys.stderr.write(
            f"Error during index search: {e}. Did you change the embedding model? "
            f"Try running 'dir_assistant clear'.\n"
        )
        raise e

    # Slice both indices and distances to get the results for the first query
    start, end = lims[0], lims[1]
    result_indices = indices[start:end]
    result_distances = distances[start:end]

    # Use zip to correctly pair each chunk index with its distance
    relevant_chunks = [
        (all_chunks[int(idx)], dist)
        for idx, dist in zip(result_indices, result_distances)
        if idx != -1
    ]

    # Apply the max_k limit to the final list of results
    return relevant_chunks[:max_k]


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
