import sys
import numpy as np
from colorama import Fore, Style

from dir_assistant.assistant.cache_manager import CacheManager
from dir_assistant.assistant.index import search_index
from dir_assistant.assistant.rag_optimizer import RagOptimizer
from dir_assistant.cli.config import (
    CACHE_PATH,
    PREFIX_CACHE_FILENAME,
    PROMPT_HISTORY_FILENAME,
    get_file_path,
)


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
        artifact_excludable_factor,
        api_context_cache_ttl,
        rag_optimizer_weights,
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
        self.context_file_ratio = context_file_ratio
        self.artifact_excludable_factor = artifact_excludable_factor
        self.api_context_cache_ttl = api_context_cache_ttl
        self.rag_optimizer_weights = rag_optimizer_weights
        self.context_size = 8192
        self.output_acceptance_retries = output_acceptance_retries
        self.no_color = no_color
        self.verbose = verbose
        self.chat_mode = chat_mode
        self.hide_thinking = hide_thinking
        self.thinking_start_pattern = thinking_start_pattern
        self.thinking_end_pattern = thinking_end_pattern
        self.last_optimized_artifacts = []
        self.last_matched_prefix = ""

        prefix_cache_path = get_file_path(CACHE_PATH, PREFIX_CACHE_FILENAME)
        prompt_history_path = get_file_path(CACHE_PATH, PROMPT_HISTORY_FILENAME)
        self.cache_manager = CacheManager(
            prefix_cache_path=prefix_cache_path,
            prompt_history_path=prompt_history_path,
            api_context_cache_ttl=self.api_context_cache_ttl,
        )
        self.artifact_metadata = self.cache_manager.compute_artifact_metadata_from_history()
        self.rag_optimizer = RagOptimizer(
            weights=self.rag_optimizer_weights,
            artifact_excludable_factor=self.artifact_excludable_factor,
        )

    def close(self):
        """Cleanly close any open resources."""
        self.cache_manager.close()

    def initialize_history(self):
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
        raise NotImplementedError

    def count_tokens(self, text, role="user"):
        raise NotImplementedError

    def build_relevant_full_text(self, user_input):
        k_nearest_neighbors = search_index(
            self.embed, self.index, user_input, self.chunks
        )

        prompt_history = self.cache_manager.get_prompt_history()
        prefix_cache_metadata = self.cache_manager.get_non_expired_prefixes()
        historical_artifact_metadata = (
            self.cache_manager.compute_artifact_metadata_from_history()
        )

        combined_artifact_metadata = {}
        all_artifact_ids = {chunk["text"] for chunk in self.chunks} | set(
            historical_artifact_metadata.keys()
        )

        for artifact_id in all_artifact_ids:
            filepath = next(
                (
                    chunk["filepath"]
                    for chunk in self.chunks
                    if chunk["text"] == artifact_id
                ),
                None,
            )
            last_modified = (
                self.artifact_metadata.get(filepath, {}).get("last_modified", 0)
                if filepath
                else 0
            )
            hist_meta = historical_artifact_metadata.get(
                artifact_id, {"frequency": 0, "positions": []}
            )
            combined_artifact_metadata[artifact_id] = {
                "frequency": hist_meta["frequency"],
                "positions": hist_meta["positions"],
                "last_modified_timestamp": last_modified,
            }

        optimized_artifact_ids, matched_prefix = self.rag_optimizer.optimize_rag_for_caching(
            k_nearest_neighbors_with_distances=k_nearest_neighbors,
            prompt_history=prompt_history,
            artifact_metadata=combined_artifact_metadata,
            prefix_cache_metadata=prefix_cache_metadata,
        )

        self.last_optimized_artifacts = optimized_artifact_ids
        self.last_matched_prefix = matched_prefix

        relevant_full_text = ""
        chunk_total_tokens = 0
        optimized_chunks = [
            next((c for c in self.chunks if c["text"] == aid), None)
            for aid in optimized_artifact_ids
        ]

        for chunk in filter(None, optimized_chunks):
            chunk_text = chunk["text"] + "\n\n"
            chunk_tokens = self.count_tokens(chunk_text, role="user")
            if (
                chunk_total_tokens + chunk_tokens
                > self.context_size * self.context_file_ratio
            ):
                self.last_optimized_artifacts = self.last_optimized_artifacts[:len(relevant_full_text.split("\n\n"))-1]
                break
            relevant_full_text += chunk_text
            chunk_total_tokens += chunk_tokens

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

    def cull_history_list(self, history_list):
        total_tokens = sum(h["tokens"] for h in history_list)
        while total_tokens > self.context_size:
            if len(history_list) > 1:
                removed = history_list.pop(1)
                total_tokens -= removed["tokens"]
            else:
                break
        return history_list

    def create_prompt(self, user_input):
        return f"{user_input}\n"

    def remove_thinking_message(self, content):
        start_pattern = self.thinking_start_pattern
        end_pattern = self.thinking_end_pattern
        if self.hide_thinking:
            return content
        start_index = content.find(start_pattern)
        while start_index != -1:
            end_index = content.find(end_pattern, start_index)
            if end_index != -1:
                content = (
                    content[:start_index] + content[end_index + len(end_pattern) :]
                )
            else:
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

        if not one_off:
            if self.last_matched_prefix:
                self.cache_manager.update_prefix_hit(self.last_matched_prefix)
            self.cache_manager.add_prompt_to_history(prompt, self.last_optimized_artifacts)

        if hasattr(self, "commit_to_git") and self.commit_to_git and not one_off:
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
        if not hasattr(self, "chat_history") or not self.chat_history:
            self.initialize_history()
        self.run_stream_processes(user_input)

    def run_completion_generator(
        self, completion_output, output_message, write_to_stdout
    ):
        thinking_context = self.create_thinking_context(write_to_stdout)
        for chunk in completion_output:
            delta = chunk["choices"][0]["delta"]
            if "content" in delta and delta["content"] != None:
                output_message["content"] += delta["content"]
                if (
                    self.is_done_thinking(thinking_context, output_message["content"])
                    and write_to_stdout
                ):
                    if not self.no_color and self.chat_mode:
                        sys.stdout.write(
                            self.get_color_prefix(Style.BRIGHT, Fore.WHITE)
                        )
                    extra_delta_after_thinking = self.get_extra_delta_after_thinking(
                        thinking_context, write_to_stdout
                    )
                    if extra_delta_after_thinking is not None:
                        # Remove the thinking message from the output now that it's complete and
                        # print the delta after the thinking message
                        sys.stdout.write(f"\r{' ' * 36}\r")
                        sys.stdout.write(extra_delta_after_thinking)
                    sys.stdout.write(delta["content"])
                    if not self.no_color and self.chat_mode:
                        sys.stdout.write(self.get_color_suffix())
                    sys.stdout.flush()
        return output_message
    def run_one_off_completion(self, prompt):
        one_off_history = self.create_one_off_prompt_history(prompt)
        completion_generator = self.call_completion(one_off_history)
        output = self.run_completion_generator(
            completion_generator,
            self.create_empty_history(role="assistant"),
            False,  # Set role for assistant
        )["content"]
        return self.remove_thinking_message(output)
    def create_empty_history(self, role="user"):
        return {"role": role, "content": "", "tokens": 0}
    def create_one_off_prompt_history(self, prompt):
        return [
            {
                "role": "user",
                "content": prompt,
                "tokens": self.count_tokens(prompt, role="user"),
            }
        ]
    def create_thinking_context(self, write_to_stdout):
        # Create a context instead of using member variables in case
        # multiple completions are running in parallel
        if write_to_stdout and self.hide_thinking and self.chat_mode:
            if not self.no_color:
                sys.stdout.write(self.get_color_prefix(Style.BRIGHT, Fore.WHITE))
            sys.stdout.write("(thinking...)")
            if not self.no_color:
                sys.stdout.write(self.get_color_suffix())
            sys.stdout.flush()
        return {
            "thinking_start_finished": not self.hide_thinking,
            "thinking_end_finished": not self.hide_thinking,
            "delta_after_thinking_finished": None,
        }
    def is_done_thinking(self, context, content):
        if not context["thinking_start_finished"]:
            # Before the thinking start pattern is found, do not print output
            if len(content) > len(self.thinking_start_pattern) + 20:
                context["thinking_start_finished"] = True
                if self.thinking_start_pattern not in content:
                    # If the start pattern is not in the output, it's not thinking
                    context["thinking_end_finished"] = True
                    context["delta_after_thinking_finished"] = content
            return False
        elif not context["thinking_end_finished"]:
            # While thinking, do not print output
            if self.thinking_end_pattern in content:
                context["thinking_end_finished"] = True
                delta_after_thinking_finished_parts = content.split(
                    self.thinking_end_pattern
                )
                # Get the last part of the string
                context["delta_after_thinking_finished"] = (
                    delta_after_thinking_finished_parts[-1]
                )
            return False
        return True
    def get_extra_delta_after_thinking(self, context, write_to_stdout):
        # If the thinking is complete, there may be some extra text after the thinking end pattern
        # This function returns that extra text if it exists.
        if context["delta_after_thinking_finished"] is not None:
            output = context["delta_after_thinking_finished"]
            context["delta_after_thinking_finished"] = None
            return output
        return None