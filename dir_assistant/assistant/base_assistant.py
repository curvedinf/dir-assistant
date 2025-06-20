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
        artifact_metadata,
        context_file_ratio,
        artifact_excludable_factor,
        api_context_cache_ttl,
        output_acceptance_retries,
        verbose,
        no_color,
        chat_mode,
        hide_thinking,
        thinking_start_pattern,
        thinking_end_pattern,
    ):
        self.system_instructions = system_instructions
        self.embed = embed
        self.index = index
        self.chunks = chunks
        self.artifact_metadata = artifact_metadata
        self.context_file_ratio = context_file_ratio
        self.artifact_excludable_factor = artifact_excludable_factor
        self.api_context_cache_ttl = api_context_cache_ttl
        self.context_size = 8192
        self.output_acceptance_retries = output_acceptance_retries
        self.no_color = no_color
        self.verbose = verbose
        self.chat_mode = chat_mode
        self.hide_thinking = hide_thinking
        self.thinking_start_pattern = thinking_start_pattern
        self.thinking_end_pattern = thinking_end_pattern

    def initialize_history(self):
        # This inititialization occurs separately from the constructor because child classes need to initialize
        # before count_tokens can be called.
        system_instructions_tokens = self.count_tokens(
            self.system_instructions, role="system"
        )
        self.chat_history = [
            {
                "role": "system",
                "content": self.system_instructions,
                "tokens": system_instructions_tokens,
            }
        ]

    def call_completion(self, chat_history, is_cgrag_call=False):
        # unimplemented on base class
        raise NotImplementedError

    def run_completion_generator(
        self, completion_output, output_message, write_to_stdout
    ):
        # unimplemented on base class
        raise NotImplementedError

    def count_tokens(self, text, role="user"):
        # unimplemented on base class
        raise NotImplementedError

    def build_relevant_full_text(self, user_input):
        relevant_chunks = search_index(self.embed, self.index, user_input, self.chunks)
        relevant_full_text = ""
        chunk_total_tokens = 0
        for i, (relevant_chunk, dist) in enumerate(relevant_chunks, start=1):
            # Note: relevant_chunk["tokens"] is created with the embedding model, not the LLM, so it will
            # not be accurate for the purposes of maximizing the context of the LLM.
            chunk_total_tokens += self.count_tokens(
                relevant_chunk["text"] + "\n\n", role="user"
            )  # Assuming RAG text is like user content for token counting
            if chunk_total_tokens >= self.context_size * self.context_file_ratio:
                break
            relevant_full_text += relevant_chunk["text"] + "\n\n"
        return relevant_full_text

    def get_color_prefix(self, brightness, color):
        if self.no_color:
            return ""
        return f"{brightness}{color}"

    def get_color_suffix(self):
        if self.no_color:
            return ""
        return Style.RESET_ALL

    def write_error_message(self, message):
        sys.stderr.write(
            f"{self.get_color_prefix(Style.BRIGHT, Fore.RED)}{message}{self.get_color_suffix()}\n"
        )
        sys.stderr.flush()

    def write_debug_message(self, message):
        if self.verbose:
            sys.stdout.write(
                f"{self.get_color_prefix(Style.BRIGHT, Fore.YELLOW)}{message}{self.get_color_suffix()}\n"
            )
            sys.stdout.flush()

    def create_user_history(self, prompt, context, tokens=0):
        if tokens == 0:
            tokens = self.count_tokens(prompt, role="user") + self.count_tokens(
                context, role="user"
            )
        return {"role": "user", "content": f"{context}{prompt}", "tokens": tokens}

    def create_assistant_history(self, response_text):
        tokens = self.count_tokens(response_text, role="assistant")
        return {"role": "assistant", "content": response_text, "tokens": tokens}

    def create_empty_history(self):
        return {"role": "assistant", "content": "", "tokens": 0}

    def cull_history_list(self, history_list):
        total_tokens = sum(h["tokens"] for h in history_list)
        while total_tokens > self.context_size:
            # Don't remove the system prompt
            if len(history_list) > 1:
                removed = history_list.pop(1)
                total_tokens -= removed["tokens"]
            else:
                break
        return history_list

    def create_prompt(self, user_input):
        return f"""{user_input}
"""

    def remove_thinking_message(self, content):
        start_pattern = self.thinking_start_pattern
        end_pattern = self.thinking_end_pattern
        if self.hide_thinking:
            return content
        start_index = content.find(start_pattern)
        while start_index != -1:
            end_index = content.find(end_pattern, start_index)
            if end_index != -1:
                content = content[:start_index] + content[end_index + len(end_pattern) :]
            else:
                # Malformed, just remove the start pattern
                content = content[:start_index]
            start_index = content.find(start_pattern)
        return content

    def run_basic_chat_stream(self, prompt, relevant_full_text, one_off=False):
        prompt_history = self.create_user_history(
            prompt, relevant_full_text, self.count_tokens(relevant_full_text)
        )
        self.chat_history.append(prompt_history)
        self.cull_history_list(self.chat_history)
        self.write_assistant_thinking_message()
        completion_generator = self.call_completion(self.chat_history)
        output_history = self.create_empty_history()
        output_history = self.run_completion_generator(
            completion_generator, output_history, not self.hide_thinking
        )
        output_history["content"] = self.remove_thinking_message(
            output_history["content"]
        )
        # Commit to git if enabled
        if hasattr(self, 'commit_to_git') and self.commit_to_git and not one_off:
            self.run_git_commit(prompt, output_history["content"])
        self.chat_history.append(output_history)
        final_response = output_history["content"].strip()
        sys.stdout.write("\n\n")
        sys.stdout.flush()
        return final_response

    def update_index_and_chunks(self, index, chunks):
        self.index = index
        self.chunks = chunks
        if self.chat_mode:
            sys.stdout.write(
                f"\n{self.get_color_prefix(Style.BRIGHT, Fore.YELLOW)}"
                f"File changes detected. Index has been updated."
                f"{self.get_color_suffix()}\n"
            )
            sys.stdout.write(
                f"{self.get_color_prefix(Style.BRIGHT, Fore.RED)}You (Press ALT-Enter, OPT-Enter, or CTRL-O to submit): \n\n{self.get_color_suffix()}"
            )
            sys.stdout.flush()

    def stream_chat(self, user_input):
        if not self.chat_history:
            self.initialize_history()
        self.run_stream_processes(user_input)

