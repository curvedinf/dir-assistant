import sys

import numpy as np
from colorama import Fore, Style

from dir_assistant.assistant.index import search_index


class BaseAssistant:
    """
    A base class for LLM assistants that enables inclusion of local files in the LLM context. Files
    are collected recursively from the current directory.
    """

    def __init__(
        self,
        system_instructions,
        embed,
        index,
        chunks,
        context_file_ratio,
        output_acceptance_retries,
        verbose,
        no_color,
        chat_mode,
    ):
        self.system_instructions = system_instructions
        self.embed = embed
        self.index = index
        self.chunks = chunks
        self.context_file_ratio = context_file_ratio
        self.context_size = 8192
        self.output_acceptance_retries = output_acceptance_retries
        self.no_color = no_color
        self.verbose = verbose
        self.chat_mode = chat_mode

    def initialize_history(self):
        # This inititialization occurs separately from the constructor because child classes need to initialize
        # before count_tokens can be called.
        system_instructions_tokens = self.count_tokens(self.system_instructions)
        self.chat_history = [
            {
                "role": "system",
                "content": self.system_instructions,
                "tokens": system_instructions_tokens,
            }
        ]

    def call_completion(self, chat_history):
        # unimplemented on base class
        raise NotImplementedError

    def run_completion_generator(
        self, completion_output, output_message, write_to_stdout
    ):
        # unimplemented on base class
        raise NotImplementedError

    def count_tokens(self, text):
        # unimplemented on base class
        raise NotImplementedError

    def build_relevant_full_text(self, user_input):
        relevant_chunks = search_index(self.embed, self.index, user_input, self.chunks)
        relevant_full_text = ""
        chunk_total_tokens = 0
        for i, relevant_chunk in enumerate(relevant_chunks, start=1):
            # Note: relevant_chunk["tokens"] is created with the embedding model, not the LLM, so it will
            # not be accurate for the purposes of maximizing the context of the LLM.
            chunk_total_tokens += self.count_tokens(relevant_chunk["text"] + "\n\n")
            if chunk_total_tokens >= self.context_size * self.context_file_ratio:
                break
            relevant_full_text += relevant_chunk["text"] + "\n\n"
        return relevant_full_text

    def get_color_prefix(self, style=None, fore=None):
        if self.no_color:
            return ""
        result = ""
        if style:
            result += style
        if fore:
            result += fore
        return result

    def get_color_suffix(self):
        return "" if self.no_color else Style.RESET_ALL

    def write_assistant_thinking_message(self):
        if self.chat_mode:
            color_prefix = self.get_color_prefix(Style.BRIGHT, Fore.GREEN)
            color_suffix = self.get_color_suffix()
            sys.stdout.write(f"{color_prefix}\nAssistant: \n\n{color_suffix}")
            sys.stdout.write(
                f"{self.get_color_prefix(Style.BRIGHT, Fore.WHITE)}\r(thinking...){color_suffix}"
            )
            sys.stdout.flush()

    def write_error_message(self, message):
        if self.chat_mode:
            color_prefix = self.get_color_prefix(Style.BRIGHT, Fore.RED)
            color_suffix = self.get_color_suffix()
            sys.stdout.write(f"{color_prefix}{message}{color_suffix}\n")
            sys.stdout.flush()

    def write_debug_message(self, message):
        if self.verbose and self.chat_mode:
            color_prefix = self.get_color_prefix(Style.BRIGHT, Fore.YELLOW)
            color_suffix = self.get_color_suffix()
            sys.stdout.write(f"{color_prefix}Debug: {message}{color_suffix}\n")
            sys.stdout.flush()

    def create_user_history(self, temp_content, final_content):
        return {
            "role": "user",
            "content": temp_content,
            "tokens": self.embed.count_tokens(final_content),
        }

    def add_user_history(self, temp_content, final_content):
        self.chat_history.append(self.create_user_history(temp_content, final_content))

    def cull_history(self):
        self.cull_history_list(self.chat_history)

    def cull_history_list(self, history_list):
        sum_of_tokens = sum(
            [self.count_tokens(message["content"]) for message in history_list]
        )
        while sum_of_tokens > self.context_size:
            history_list.pop(0)
            sum_of_tokens = sum(
                [self.count_tokens(message["content"]) for message in history_list]
            )

        # Some LLMs require the first message to be from the user
        if history_list[0]["role"] == "system":
            while len(history_list) > 1 and history_list[1]["role"] == "assistant":
                history_list.pop(1)
        else:
            while len(history_list) > 0 and history_list[0]["role"] == "assistant":
                history_list.pop(0)

    def create_empty_history(self, role="user"):
        return {"role": role, "content": "", "tokens": 0}

    def create_one_off_prompt_history(self, prompt):
        return [
            {
                "role": "user",
                "content": prompt,
                "tokens": self.count_tokens(prompt),
            }
        ]

    def create_prompt(self, user_input):
        return user_input

    def run_pre_stream_processes(self, user_input):
        self.write_assistant_thinking_message()

    def run_stream_processes(self, user_input):
        # Returns a string of the assistant's response
        prompt = self.create_prompt(user_input)
        relevant_full_text = self.build_relevant_full_text(prompt)
        return self.run_basic_chat_stream(prompt, relevant_full_text)

    def run_post_stream_processes(self, user_input, stream_output):
        # Returns whether the output should be accepted
        return True

    def run_accepted_output_processes(self, user_input, stream_output):
        # Run processes that should be run if the output is accepted
        if self.chat_mode and self.verbose:
            sys.stdout.write(f"Response accepted, continuing...\n\n")

    def run_bad_output_processes(self, user_input, stream_output):
        # Run processes that should be run if the output is bad
        if self.chat_mode:
            sys.stdout.write(f"Response rejected, ignoring...\n\n")
            sys.stdout.flush()

    def stream_chat(self, user_input):
        # Main function for streaming assistant chat to the user.
        retries = 0
        accepted = False
        stream_output = ""
        while retries < self.output_acceptance_retries:
            self.run_pre_stream_processes(user_input)
            stream_output = self.run_stream_processes(user_input)
            accepted = self.run_post_stream_processes(user_input, stream_output)
            if accepted:
                break
            retries += 1
        if accepted:
            self.run_accepted_output_processes(user_input, stream_output)
        else:
            self.run_bad_output_processes(user_input, stream_output)

    def run_basic_chat_stream(self, user_input, relevant_full_text):
        # Add the user input to the chat history
        user_content = relevant_full_text + user_input
        self.add_user_history(user_content, user_input)

        # Remove old messages from the chat history if too large for context
        self.cull_history()

        # Get the generator from of the completion
        completion_generator = self.call_completion(self.chat_history)

        # Replace the RAG output with the user input. This reduces the size of the history for future prompts.
        self.chat_history[-1]["content"] = user_input

        # Display chat history
        output_history = self.create_empty_history()

        if self.chat_mode:
            if not self.no_color:
                sys.stdout.write(f"{self.get_color_prefix(Style.BRIGHT, Fore.WHITE)}")
            sys.stdout.write(f"\r{' ' * 36}\r")
            if not self.no_color:
                sys.stdout.write(f"{self.get_color_suffix()}")
            sys.stdout.flush()

        output_history = self.run_completion_generator(
            completion_generator, output_history, True
        )

        if self.chat_mode:
            if not self.no_color:
                sys.stdout.write(f"{self.get_color_suffix()}")
            sys.stdout.write("\n\n")
            sys.stdout.flush()

        # Add the completion to the chat history
        output_history["tokens"] = self.count_tokens(output_history["content"])
        self.chat_history.append(output_history)
        return output_history["content"]

    def update_index_and_chunks(self, file_path, new_chunks, new_embeddings):
        # Remove old chunks and embeddings for this file
        self.chunks = [chunk for chunk in self.chunks if chunk["filepath"] != file_path]
        self.chunks.extend(new_chunks)

        # Find indices of old embeddings
        old_embedding_indices = [
            i for i, chunk in enumerate(self.chunks) if chunk["filepath"] == file_path
        ]

        if old_embedding_indices:
            # Convert list to numpy array
            old_embedding_indices = np.array(old_embedding_indices, dtype=np.int64)

            # Remove old embeddings from the index
            self.index.remove_ids(old_embedding_indices)

        # Add new embeddings to the index
        if new_embeddings:
            self.index.add(np.array(new_embeddings))

    def run_one_off_completion(self, prompt):
        one_off_history = self.create_one_off_prompt_history(prompt)
        completion_generator = self.call_completion(one_off_history)
        return self.run_completion_generator(
            completion_generator, self.create_empty_history(), False
        )["content"]
