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
        hide_thinking,
        thinking_start_pattern,
        thinking_end_pattern,
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

    def call_completion(self, chat_history):
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
        for i, relevant_chunk in enumerate(relevant_chunks, start=1):
            # Note: relevant_chunk["tokens"] is created with the embedding model, not the LLM, so it will
            # not be accurate for the purposes of maximizing the context of the LLM.
            chunk_total_tokens += self.count_tokens(
                relevant_chunk["text"] + "\n\n", role="user"
            )  # Assuming RAG text is like user content for token counting
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
            "tokens": self.embed.count_tokens(
                final_content
            ),  # This uses embed's token counter
        }

    def add_user_history(self, temp_content, final_content):
        self.chat_history.append(self.create_user_history(temp_content, final_content))

    def cull_history(self):
        self.cull_history_list(self.chat_history)

    def find_truncation_point(self, text, target_tokens, role="user"):
        # Helper to find how much of 'text' fits into 'target_tokens'
        low = 0
        high = len(text)
        best_fit_text = ""

        if self.count_tokens("", role=role) > target_tokens:
            return ""

        while low <= high:
            mid = (low + high) // 2
            substring = text[:mid]
            tokens = self.count_tokens(substring, role=role)
            if tokens <= target_tokens:
                best_fit_text = substring
                low = mid + 1
            else:
                high = mid - 1
        return best_fit_text

    def cull_history_list(self, history_list):
        current_total_tokens = sum(
            self.count_tokens(message["content"], role=message["role"])
            for message in history_list
        )

        # Phase 1: Pop older messages (all but the last one ideally) if oversized
        while current_total_tokens > self.context_size and len(history_list) > 1:
            popped_message = history_list.pop(0)
            current_total_tokens -= self.count_tokens(
                popped_message["content"], role=popped_message["role"]
            )
            self.write_debug_message(
                f"Context too large. Dropped older message (role: {popped_message['role']}) to free up space."
            )

        # Phase 2: If still oversized and only one message remains (the latest prompt), truncate it.
        if current_total_tokens > self.context_size and len(history_list) == 1:
            last_message = history_list[0]
            original_content = last_message["content"]
            original_tokens = self.count_tokens(
                original_content, role=last_message["role"]
            )

            # The available tokens for this last message is based on the file ratio times the context size
            available_tokens_for_last_message = self.context_size - (
                self.context_size * self.context_file_ratio
            )

            if original_tokens > available_tokens_for_last_message:
                self.write_error_message(
                    f"\nLatest prompt is too large ({original_tokens} tokens) for history context ({available_tokens_for_last_message} tokens). Truncating it."
                )
                truncated_content = self.find_truncation_point(
                    original_content,
                    available_tokens_for_last_message,
                    role=last_message["role"],
                )
                last_message["content"] = truncated_content
                new_tokens_for_last_message = self.count_tokens(
                    truncated_content, role=last_message["role"]
                )
                last_message["tokens"] = (
                    new_tokens_for_last_message  # Update field if used, though culling relies on self.count_tokens
                )
                current_total_tokens = (
                    new_tokens_for_last_message  # As it's the only message
                )

                if len(truncated_content) < len(original_content):
                    self.write_debug_message(
                        f"Latest message truncated to fit. Original length: {len(original_content)} chars, new length: {len(truncated_content)} chars. New tokens: {new_tokens_for_last_message}"
                    )
                elif not truncated_content and original_content:  # Content became empty
                    self.write_error_message(
                        f"Latest message (role: {last_message['role']}) was too large and had to be completely truncated to fit context. Original content: '{original_content[:50]}...'. This may lead to unexpected behavior."
                    )
                else:  # No effective truncation or content was already minimal
                    self.write_debug_message(
                        f"Latest message (role: {last_message['role']}) was too large but truncation logic couldn't shorten it effectively or content was minimal. Final tokens: {new_tokens_for_last_message}"
                    )

        # Phase 3: Role-based culling (original logic, now guarded and uses role for token counting if resizes occur)
        if history_list:
            if history_list[0]["role"] == "system":
                while len(history_list) > 1 and history_list[1]["role"] == "assistant":
                    popped_msg = history_list.pop(1)
                    # current_total_tokens -= self.count_tokens(popped_msg["content"], role=popped_msg["role"]) # Optional: keep total tokens accurate
                    self.write_debug_message(
                        f"Removed leading assistant message (role: {popped_msg['role']}) after system prompt."
                    )
            else:
                while history_list and history_list[0]["role"] == "assistant":
                    popped_msg = history_list.pop(0)
                    # current_total_tokens -= self.count_tokens(popped_msg["content"], role=popped_msg["role"]) # Optional
                    self.write_debug_message(
                        f"Removed leading assistant message (role: {popped_msg['role']})."
                    )

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
        output_history = self.create_empty_history(
            role="assistant"
        )  # Set role for assistant
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
        output_history["content"] = self.remove_thinking_message(
            output_history["content"]
        )
        if self.chat_mode:
            if not self.no_color:
                sys.stdout.write(f"{self.get_color_suffix()}")
            sys.stdout.write("\n\n")
            sys.stdout.flush()
        # Add the completion to the chat history
        output_history["tokens"] = self.count_tokens(
            output_history["content"], role="assistant"
        )
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

    def remove_thinking_message(self, output):
        # If hide thinking is enabled, remove the thinking message from any string
        if self.hide_thinking:
            thinking_start_parts = output.split(self.thinking_start_pattern)
            if len(thinking_start_parts) > 1:
                thinking_end_parts = thinking_start_parts[1].split(
                    self.thinking_end_pattern
                )
                if len(thinking_end_parts) > 1:
                    # This should be the content between <think> and </think>
                    # The request implies removing the thinking block.
                    # To remove it and keep text before and after:
                    # return thinking_start_parts[0] + thinking_end_parts[1]
                    # The current behavior seems to return the content *inside* the thinking tags.
                    # Let's clarify. The prompt says "remove the thinking message".
                    # This usually means remove <think>...</think> itself.
                    # Current code returns thinking_end_parts[0] which is *inside* the tags.
                    # To remove the block:
                    return thinking_start_parts[0] + thinking_end_parts[1]
        # If any condition for hide thinking fails, return the full output
        return output

    def run_one_off_completion(self, prompt):
        one_off_history = self.create_one_off_prompt_history(prompt)
        completion_generator = self.call_completion(one_off_history)
        output = self.run_completion_generator(
            completion_generator,
            self.create_empty_history(role="assistant"),
            False,  # Set role for assistant
        )["content"]
        return self.remove_thinking_message(output)
