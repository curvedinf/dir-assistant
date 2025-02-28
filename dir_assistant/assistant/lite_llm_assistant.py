import sys
from copy import deepcopy

from colorama import Fore, Style
from litellm import completion, token_counter

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
            self.chat_history[0]["role"] = "user"

    def call_completion(self, chat_history):
        # Clean "tokens" from chat history. It causes an error for mistral.
        chat_history_cleaned = deepcopy(chat_history)
        for message in chat_history_cleaned:
            if "tokens" in message:
                del message["tokens"]

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

    def run_completion_generator(
        self, completion_output, output_message, write_to_stdout
    ):
        for chunk in completion_output:
            delta = chunk["choices"][0]["delta"]
            if "content" in delta and delta["content"] != None:
                output_message["content"] += delta["content"]

                if write_to_stdout:
                    if not self.no_color and self.chat_mode:
                        sys.stdout.write(
                            self.get_color_prefix(Style.BRIGHT, Fore.WHITE)
                        )
                    sys.stdout.write(delta["content"])
                    if not self.no_color and self.chat_mode:
                        sys.stdout.write(self.get_color_suffix())
                    sys.stdout.flush()
        return output_message

    def count_tokens(self, text):
        return token_counter(
            model=self.completion_options["model"], messages=[{"user": "role", "content": text}]
        )
