from copy import deepcopy
from json import dumps
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
        lite_llm_pass_through_context_size,
        cgrag_lite_llm_completion_options,
        cgrag_lite_llm_context_size,
        cgrag_lite_llm_pass_through_context_size,
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
            artifact_excludable_factor,
            artifact_cosine_cutoff,
            artifact_cosine_cgrag_cutoff,
            api_context_cache_ttl,
            rag_optimizer_weights,
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
        self.cgrag_completion_options = cgrag_lite_llm_completion_options
        self.cgrag_context_size = cgrag_lite_llm_context_size
        self.cgrag_pass_through_context_size = cgrag_lite_llm_pass_through_context_size
        self.no_color = no_color
        if self.chat_mode and self.verbose:
            if self.no_color:
                print(f"LiteLLM completion options: {self.completion_options}")
                print(f"LiteLLM context size: {self.context_size}")
                print(
                    f"LiteLLM CGRAG completion options: {self.cgrag_completion_options}"
                )
                print(f"LiteLLM CGRAG context size: {self.cgrag_context_size}")
            else:
                print(
                    f"{Fore.LIGHTBLACK_EX}LiteLLM completion options: {self.completion_options}{Style.RESET_ALL}"
                )
                print(
                    f"{Fore.LIGHTBLACK_EX}LiteLLM context size: {self.context_size}{Style.RESET_ALL}"
                )
                print(
                    f"{Fore.LIGHTBLACK_EX}LiteLLM CGRAG completion options: {self.cgrag_completion_options}{Style.RESET_ALL}"
                )
                print(
                    f"{Fore.LIGHTBLACK_EX}LiteLLM CGRAG context size: {self.cgrag_context_size}{Style.RESET_ALL}"
                )

    def call_completion(self, chat_history, is_cgrag_call=False):
        # Clean "tokens" from chat history. It causes an error for mistral.
        chat_history_cleaned = deepcopy(chat_history)
        for message in chat_history_cleaned:
            if "tokens" in message:
                del message["tokens"]
        # Hardcoded retry settings
        max_retries = 3
        retry_delay_seconds = 1
        current_retry = 0
        options = (
            self.cgrag_completion_options if is_cgrag_call else self.completion_options
        )
        context_size = self.cgrag_context_size if is_cgrag_call else self.context_size
        pass_through_context = (
            self.cgrag_pass_through_context_size
            if is_cgrag_call
            else self.pass_through_context_size
        )
        while current_retry <= max_retries:
            try:
                if self.verbose:
                    print(
                        f"Calling completion with chat history ({len(chat_history_cleaned)} messages, {len(dumps(chat_history_cleaned, indent=4))} characters):"
                    )
                if pass_through_context:
                    return completion(
                        **options,
                        messages=chat_history_cleaned,
                        stream=True,
                        num_ctx=context_size,
                    )
                else:
                    return completion(
                        **options,
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
