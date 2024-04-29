import os

import numpy as np
from faiss import IndexFlatL2


def count_tokens(embed, text):
    return len(embed.tokenize(bytes(text, 'utf-8')))


text_chars = bytearray({7, 8, 9, 10, 12, 13, 27} | set(range(0x20, 0x100)) - {0x7f})
def is_text_file(filepath):
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
    print("Starting file chunking...")

    for i, file_info in enumerate(files_with_contents, start=1):
        filepath = file_info['filepath']
        contents = file_info['contents']
        lines = contents.split('\n')
        current_chunk = ''
        start_line_number = 1

        print(f'Chunking file {i}/{len(files_with_contents)}: {filepath}')
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
                            "text": chunk_header + current_chunk
                        })
                        current_chunk = ''
                        start_line_number = line_number  # Next chunk starts from this line
                        # Do not break; continue processing the line

        # Add the remaining content as the last chunk
        if current_chunk:
            chunk_header = f"---------------\n\nUser file '{filepath}' lines {start_line_number}-{len(lines)}:\n\n"
            chunks.append({
                "tokens": count_tokens(embed, chunk_header + current_chunk),
                "text": chunk_header + current_chunk
            })

    # Create the embeddings
    print("File embedding chunks created:", len(chunks))
    print("Max size of an embedding chunk:", embed_chunk_size)

    # Create the index
    print("Creating embeddings...")
    embeddings_list = []
    for i, chunk in enumerate(chunks, start=1):
        print(f'Embedding chunk {i}/{len(chunks)}')
        embedding = embed.create_embedding(chunk['text'])['data'][0]['embedding']
        embeddings_list.append(embedding)

    print("Indexing embeddings...")
    embeddings = np.array(embeddings_list)
    index = IndexFlatL2(embeddings.shape[1])
    index.add(embeddings)

    return index, chunks


def find_split_point(embed, line_content, max_size, header):
    for split_point in range(1, len(line_content)):
        if count_tokens(embed, header + line_content[:split_point] + '\n') > max_size:
            return split_point - 1  # Return the last valid split point
    return len(line_content)  # Fallback if the line is smaller than max_size or just one token over


def search_index(embed, index, query, all_chunks):
    query_embedding = embed.create_embedding([query])['data'][0]['embedding']
    distances, indices = index.search(np.array([query_embedding]), 100)
    relevant_chunks = [all_chunks[i] for i in indices[0] if i != -1]
    return relevant_chunks
