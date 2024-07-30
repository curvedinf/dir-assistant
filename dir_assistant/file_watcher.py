from logging import info
from traceback import print_exc

from colorama import Fore, Style
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileSystemEvent
from dir_assistant.index import process_file, get_text_files


class FileChangeHandler(FileSystemEventHandler):
    def __init__(self, embed, ignore_paths, embed_chunk_size, llm_updated_index_callback):
        self.embed = embed
        self.ignore_paths = ignore_paths
        self.embed_chunk_size = embed_chunk_size
        self.llm_updated_index_callback = llm_updated_index_callback

    def reindex_file(self, file_path):
        if file_path in (None, ''):
            return
        if file_path in get_text_files('.', self.ignore_paths):
            try:
                with open(file_path, 'r') as file:
                    contents = file.read()
                chunks, embeddings = process_file(self.embed, file_path, contents, self.embed_chunk_size)
                # Update the index and chunks
                self.llm_updated_index_callback(file_path, chunks, embeddings)
            except FileNotFoundError:
                info(f"{Fore.LIGHTBLACK_EX}Error updating file {file_path}: File not found{Style.RESET_ALL}")
            except Exception as e:
                print_exc()

    def on_any_event(self, event):
        if event.is_directory or event.event_type == 'opened' or event.event_type == 'closed':
            return
        self.reindex_file(event.src_path)
        self.reindex_file(event.dest_path)


def start_file_watcher(directory, embed, ignore_paths, embed_chunk_size, llm_updated_index_callback):
    event_handler = FileChangeHandler(
        embed,
        ignore_paths,
        embed_chunk_size,
        llm_updated_index_callback
    )
    observer = Observer()
    observer.schedule(event_handler, directory, recursive=True)
    observer.start()
    return observer
