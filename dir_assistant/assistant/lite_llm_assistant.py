from copy import deepcopy
from time import sleep

from colorama import Fore, Style
from litellm import completion
from litellm import exceptions as litellm_exceptions
from litellm import token_counter

from dir_assistant.assistant.git_assistant import GitAssistant


class LiteLLMAssistant(GitAssistant):
    def __init__(
        self,
        lite_llm_completion_options,
        lite_llm_context_size,
        lite_llm_model_uses_system_message,
        lite_llm_pass_through_context_size,
        system_instructions,
        embed,
        index,
        chunks,
        context_file_ratio,
        output_acceptance_retries,
        use_cgrag,
        print_cgrag,
        commit_to_git,
        verbose,
        no_color,
        chat_mode,
        hide_thinking,
        thinking_start_pattern,
        thinking_end_pattern,
    ):
        super().__init__(
            system_instructions,
            embed,
            index,
            chunks,
            context_file_ratio,
            output_acceptance_retries,
            use_cgrag,
            print_cgrag,
            commit_to_git,
            verbose,
            no_color,
            chat_mode,
            hide_thinking,
            thinking_start_pattern,
            thinking_end_pattern,
        )
        self.completion_options = lite_llm_completion_options
        self.context_size = lite_llm_context_size
        self.pass_through_context_size = lite_llm_pass_through_context_size
        self.lite_llm_model_uses_system_message = lite_llm_model_uses_system_message
        self.no_color = no_color
        if self.chat_mode and self.verbose:
            if self.no_color:
                print(f"LiteLLM context size: {self.context_size}")
            else:
                print(
                    f"{Fore.LIGHTBLACK_EX}LiteLLM context size: {self.context_size}{Style.RESET_ALL}"
                )

    def initialize_history(self):
        super().initialize_history()
        if not self.lite_llm_model_uses_system_message:
            if self.chat_history and self.chat_history[0]["role"] == "system":
                self.chat_history[0]["role"] = "user"

    def call_completion(self, chat_history):
        # Clean "tokens" from chat history. It causes an error for mistral.
        chat_history_cleaned = deepcopy(chat_history)
        for message in chat_history_cleaned:
            if "tokens" in message:
                del message["tokens"]
        # Hardcoded retry settings
        max_retries = 3
        retry_delay_seconds = 1
        current_retry = 0
        while current_retry <= max_retries:
            try:
                if self.pass_through_context_size:
                    return completion(
                        **self.completion_options,
                        messages=chat_history_cleaned,
                        stream=True,
                        num_ctx=self.context_size,
                    )
                else:
                    return completion(
                        **self.completion_options,
                        messages=chat_history_cleaned,
                        stream=True,
                    )
            except litellm_exceptions.APIConnectionError as e:
                current_retry += 1
                if current_retry > max_retries:
                    self.write_error_message(
                        f"API Connection Error after {max_retries} retries: {e}"
                    )
                    raise
                self.write_debug_message(
                    f"API Connection Error (attempt {current_retry}/{max_retries}): {e}. Retrying in {retry_delay_seconds}s..."
                )
                sleep(retry_delay_seconds)
            except Exception as e:  # Catch other potential litellm exceptions
                self.write_error_message(f"LiteLLM completion error: {e}")
                raise
        # This line should ideally not be reached if the loop logic is correct (always returns or raises).
        # Added for robustness in case of unforeseen loop exit.
        raise Exception(
            f"[dir-assistant] LiteLLMAssistant Error: Completion failed "
            "after exhausting retries or due to an unhandled state."
        )

    def count_tokens(self, text, role="user"):
        valid_roles = ["system", "user", "assistant"]
        role_to_pass = role
        if role not in valid_roles:
            self.write_debug_message(
                f"count_tokens received invalid role '{role}', defaulting to 'user'."
            )
            role_to_pass = "user"

        return token_counter(
            model=self.completion_options["model"],
            messages=[{"role": role_to_pass, "content": text}],
        )
