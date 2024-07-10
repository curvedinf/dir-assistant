import threading
import time
from traceback import print_exc

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileSystemEvent
from index import process_file, get_text_files


class FileChangeHandler(FileSystemEventHandler):
    def __init__(self, embed, ignore_paths, embed_chunk_size, index_cache_file, llm_updated_index_callback):
        self.embed = embed
        self.ignore_paths = ignore_paths
        self.embed_chunk_size = embed_chunk_size
        self.index_cache_file = index_cache_file
        self.llm_updated_index_callback = llm_updated_index_callback

    def reindex_file(self, file_path):
        if file_path in (None, ''):
            return
        if file_path in get_text_files('.', self.ignore_paths):
            print("Text File modified: " + file_path)
            try:
                with open(file_path, 'r') as file:
                    contents = file.read()
                chunks, embeddings = process_file(self.embed, file_path, contents, self.embed_chunk_size)
                # Update the index and chunks
                self.llm_updated_index_callback(file_path, chunks, embeddings)
            except FileNotFoundError:
                print(f"Error updating file {file_path}: File not found")
            #except Exception as e:
            #    print(f"Error updating")# file {file_path}: {str(e)}")
            except Exception as e:
                print_exc()

    def on_any_event(self, event):
        if event.is_directory or event.event_type == 'opened' or event.event_type == 'closed':
            return
        print(event.event_type)
        self.reindex_file(event.src_path)
        self.reindex_file(event.dest_path)


def start_file_watcher(directory, embed, ignore_paths, embed_chunk_size, index_cache_file, llm_updated_index_callback):
    event_handler = FileChangeHandler(
        embed,
        ignore_paths,
        embed_chunk_size,
        index_cache_file,
        llm_updated_index_callback
    )
    observer = Observer()
    observer.schedule(event_handler, directory, recursive=True)
    observer.start()
    return observer
