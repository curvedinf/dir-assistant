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
        artifact_cosine_cutoff,
        artifact_cosine_cgrag_cutoff,
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
        self.artifact_cosine_cutoff = artifact_cosine_cutoff
        self.artifact_cosine_cgrag_cutoff = artifact_cosine_cgrag_cutoff
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
        self.artifact_metadata = (
            self.cache_manager.compute_artifact_metadata_from_history()
        )
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

    def build_relevant_full_text(self, user_input, cutoff):
        """
        Identifies relevant text chunks, pre-culs a candidate pool based on token
        limits, optimizes the pool for caching, and builds the final context string.
        """
        # Compute dynamic max_k
        estimated_minimal_token_count = 100
        max_k = int(
            self.context_size * self.context_file_ratio // estimated_minimal_token_count
        )
        # 1. Get an initial list of nearest neighbors from the search index.
        k_nearest_neighbors = search_index(
            self.embed,
            self.index,
            user_input,
            self.chunks,
            max_k=max_k,
            max_distance=cutoff,
        )
        # 2. Pre-cull candidates to create a token-aware pool for the optimizer.
        # This is the primary change: culling before optimizing.
        candidate_pool = []
        total_candidate_tokens = 0
        # Create a candidate pool larger than the final context to give the
        # optimizer room to swap artifacts. Increased ratio to 3.0 for fuller context.
        optimizer_candidate_pool_ratio = 3.0
        optimizer_pool_limit = (
            self.context_size * self.context_file_ratio * optimizer_candidate_pool_ratio
        )
        for neighbor in k_nearest_neighbors:
            chunk_text = neighbor[0].get("text", "") + "\n\n"
            chunk_tokens = self.count_tokens(chunk_text, role="user")
            # Stop adding candidates when the pool reaches the desired token limit.
            if (
                total_candidate_tokens + chunk_tokens > optimizer_pool_limit
                and candidate_pool
            ):
                break
            # The optimizer will need the distance, so we keep the full neighbor object.
            candidate_pool.append(neighbor)
            total_candidate_tokens += chunk_tokens
        # 3. Gather historical and cache metadata for the optimizer.
        # This logic is preserved from the original implementation.
        prompt_history = self.cache_manager.get_prompt_history()
        prefix_cache_metadata = self.cache_manager.get_non_expired_prefixes()
        historical_artifact_metadata = (
            self.cache_manager.compute_artifact_metadata_from_history()
        )
        combined_artifact_metadata = {}
        all_artifacts = {chunk["text"] for chunk in self.chunks} | set(
            historical_artifact_metadata.keys()
        )
        for artifact in all_artifacts:
            filepath = next(
                (
                    chunk["filepath"]
                    for chunk in self.chunks
                    if chunk["text"] == artifact
                ),
                None,
            )
            last_modified = (
                self.artifact_metadata.get(filepath, {}).get("last_modified", 0)
                if filepath
                else 0
            )
            hist_meta = historical_artifact_metadata.get(
                artifact, {"frequency": 0, "positions": []}
            )
            combined_artifact_metadata[artifact] = {
                "frequency": hist_meta["frequency"],
                "positions": hist_meta["positions"],
                "last_modified_timestamp": last_modified,
            }
        if self.verbose and self.chat_mode:
            print(f"Computed max_k: {max_k}")
            print(f"K nearest count: {len(k_nearest_neighbors)}")
            print(f"Pre-culled candidates for optimizer: {len(candidate_pool)}")
            print(f"Prompt history: {len(prompt_history)}")
            print(f"Prefix cache metadata: {len(prefix_cache_metadata)}")
        # 4. Run the optimizer on the pre-culled candidate pool.
        # The optimizer input is now the smaller, more relevant candidate list.
        optimizer_input = [
            (chunk.get("text", ""), distance) for chunk, distance in candidate_pool
        ]
        optimized_artifacts, matched_prefix = (
            self.rag_optimizer.optimize_rag_for_caching(
                k_nearest_neighbors_with_distances=optimizer_input,
                prompt_history=prompt_history,
                artifact_metadata=combined_artifact_metadata,
                prefix_cache_metadata=prefix_cache_metadata,
            )
        )
        if self.verbose and self.chat_mode:
            print(f"Optimized artifacts before final cull: {len(optimized_artifacts)}")
            print(f"Matched prefix size: {len(matched_prefix.split())}")
        self.last_matched_prefix = matched_prefix
        self.last_optimized_artifacts = optimized_artifacts
        # 5. Build the final text, performing a strict culling on the *optimized* list.
        # This final loop ensures the hard context limit is never exceeded.
        relevant_full_text = ""
        final_artifacts_in_context = []
        chunk_total_tokens = 0
        target_tokens = self.context_size * self.context_file_ratio
        # An efficient lookup map is better than iterating with next() repeatedly.
        chunk_map = {c["text"]: c for c in self.chunks}
        for artifact in optimized_artifacts:
            chunk = chunk_map.get(artifact)
            if not chunk:
                continue
            chunk_text = chunk["text"] + "\n\n"
            chunk_tokens = self.count_tokens(chunk_text, role="user")
            if chunk_total_tokens + chunk_tokens > target_tokens:
                break  # The context is full.
            relevant_full_text += chunk_text
            chunk_total_tokens += chunk_tokens
            final_artifacts_in_context.append(artifact)
        # If still under target after optimization, add more from original candidates sorted by distance
        if chunk_total_tokens < target_tokens:
            remaining_candidates = []
            for neighbor in k_nearest_neighbors:
                art_id = neighbor[0].get("text", "")
                if art_id not in final_artifacts_in_context:
                    remaining_candidates.append(neighbor)
            # Sort remaining by distance (assuming k_nearest_neighbors is sorted by relevance)
            remaining_candidates.sort(key=lambda x: x[1])  # Sort by distance
            for neighbor in remaining_candidates:
                chunk = neighbor[0]
                chunk_text = chunk["text"] + "\n\n"
                chunk_tokens = self.count_tokens(chunk_text, role="user")
                if chunk_total_tokens + chunk_tokens > target_tokens:
                    break
                relevant_full_text += chunk_text
                chunk_total_tokens += chunk_tokens
                final_artifacts_in_context.append(chunk["text"])
        self.last_optimized_artifacts = final_artifacts_in_context
        if self.verbose and self.chat_mode:
            print(f"Total tokens in relevant_full_text: {chunk_total_tokens}")
            print(f"Context fully filled: {chunk_total_tokens >= target_tokens}")
        return relevant_full_text

    def get_color_prefix(self, brightness, color):
        if self.no_color:
            return ""
        return f"{brightness}{color}"

    def get_color_suffix(self):
        if self.no_color:
            return ""
        return Style.RESET_ALL

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
        return f"""If this is the final part of this prompt, this is the actual request to respond to. All information
above should be considered supplementary to this request to help answer it.
User request:
<---------------------------->
{user_input}
<---------------------------->
Perform the user request above.
"""

    def remove_thinking_message(self, content):
        start_pattern = self.thinking_start_pattern
        end_pattern = self.thinking_end_pattern
        if not self.hide_thinking:
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

    def run_pre_stream_processes(self, user_input):
        self.write_assistant_thinking_message()

    def run_stream_processes(self, user_input, one_off=False):
        prompt = self.create_prompt(user_input)
        relevant_full_text = self.build_relevant_full_text(
            user_input, self.artifact_cosine_cutoff
        )
        return self.run_basic_chat_stream(prompt, relevant_full_text, one_off)

    def run_post_stream_processes(self, user_input, stream_output):
        return True

    def run_accepted_output_processes(self, user_input, stream_output):
        if self.chat_mode and self.verbose:
            sys.stdout.write(f"Response accepted, continuing...\n\n")

    def run_bad_output_processes(self, user_input, stream_output):
        if self.chat_mode:
            sys.stdout.write(f"Response rejected, ignoring...\n\n")
            sys.stdout.flush()

    def stream_chat(self, user_input):
        if not hasattr(self, "chat_history") or not self.chat_history:
            self.initialize_history()
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

    def run_basic_chat_stream(self, prompt, relevant_full_text, one_off=False):
        prompt_history = self.create_user_history(
            prompt, relevant_full_text, self.count_tokens(relevant_full_text)
        )
        self.chat_history.append(prompt_history)
        self.cull_history_list(self.chat_history)
        completion_generator = self.call_completion(self.chat_history)
        output_history = self.create_empty_history()
        if self.chat_mode:
            sys.stdout.write(f"\r{' ' * 36}\r")
            sys.stdout.flush()
        output_history = self.run_completion_generator(
            completion_generator, output_history, self.chat_mode
        )
        output_history["content"] = self.remove_thinking_message(
            output_history["content"]
        )
        if not one_off:
            if self.last_matched_prefix:
                self.cache_manager.update_prefix_hit(self.last_matched_prefix)
            # Add the full sequence of artifacts as a new potential prefix
            if self.last_optimized_artifacts:
                self.cache_manager.update_prefix_hit(self.last_optimized_artifacts)
            self.cache_manager.add_prompt_to_history(
                prompt, self.last_optimized_artifacts
            )
        self.chat_history.append(output_history)
        final_response = output_history["content"].strip()
        if self.chat_mode:
            sys.stdout.write("\n\n")
            sys.stdout.flush()
        return final_response

    def update_index_and_chunks(self, file_path, new_chunks, new_embeddings):
        # Find indices of all chunks from the old file
        indices_to_remove = {
            i for i, chunk in enumerate(self.chunks) if chunk["filepath"] == file_path
        }
        if indices_to_remove:
            # Remove from faiss index. The IDs are the original indices.
            self.index.remove_ids(np.array(list(indices_to_remove), dtype=np.int64))
            # Rebuild python list of chunks without the removed items.
            self.chunks = [
                chunk
                for i, chunk in enumerate(self.chunks)
                if i not in indices_to_remove
            ]
        # Add new chunks and embeddings
        self.chunks.extend(new_chunks)
        if new_embeddings:
            self.index.add(np.array(new_embeddings, dtype=np.float32))
        if self.chat_mode and self.verbose:
            sys.stdout.write(
                f"\n{self.get_color_prefix(Style.BRIGHT, Fore.YELLOW)}"
                f"File changes detected. Index has been updated."
                f"{self.get_color_suffix()}\n"
            )
            sys.stdout.write(
                f"{self.get_color_prefix(Style.BRIGHT, Fore.RED)}You (Press ALT-Enter, OPT-Enter, or CTRL-O to submit): \n\n{self.get_color_suffix()}"
            )
            sys.stdout.flush()

    def run_completion_generator(
        self, completion_output, output_message, write_to_stdout
    ):
        thinking_context = self.create_thinking_context(write_to_stdout)
        has_printed = False
        for chunk in completion_output:
            delta = chunk["choices"][0]["delta"]
            if "content" in delta and delta["content"] is not None:
                output_message["content"] += delta["content"]
                if (
                    self.is_done_thinking(thinking_context, output_message["content"])
                    and write_to_stdout
                ):
                    if not has_printed:
                        sys.stdout.write(f"\r{' ' * 36}\r")
                        has_printed = True
                    if not self.no_color and self.chat_mode:
                        sys.stdout.write(
                            self.get_color_prefix(Style.BRIGHT, Fore.WHITE)
                        )
                    extra_delta_after_thinking = self.get_extra_delta_after_thinking(
                        thinking_context, write_to_stdout
                    )
                    if extra_delta_after_thinking is not None:
                        sys.stdout.write(extra_delta_after_thinking)
                    sys.stdout.write(delta["content"])
                    if not self.no_color and self.chat_mode:
                        sys.stdout.write(self.get_color_suffix())
                    sys.stdout.flush()
        if not has_printed and write_to_stdout and output_message["content"]:
            sys.stdout.write(f"\r{' ' * 36}\r")
            if not self.no_color and self.chat_mode:
                sys.stdout.write(self.get_color_prefix(Style.BRIGHT, Fore.WHITE))
            content_to_print = self.remove_thinking_message(output_message["content"])
            sys.stdout.write(content_to_print)
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
            False,
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
            if len(content) > len(self.thinking_start_pattern) + 20:
                context["thinking_start_finished"] = True
                if self.thinking_start_pattern not in content:
                    context["thinking_end_finished"] = True
                    context["delta_after_thinking_finished"] = content
            return False
        elif not context["thinking_end_finished"]:
            if self.thinking_end_pattern in content:
                context["thinking_end_finished"] = True
                delta_after_thinking_finished_parts = content.split(
                    self.thinking_end_pattern
                )
                context["delta_after_thinking_finished"] = (
                    delta_after_thinking_finished_parts[-1]
                )
            return False
        return True

    def get_extra_delta_after_thinking(self, context, write_to_stdout):
        if context["delta_after_thinking_finished"] is not None:
            output = context["delta_after_thinking_finished"]
            context["delta_after_thinking_finished"] = None
            return output
        return None
