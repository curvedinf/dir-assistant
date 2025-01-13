import sys

from colorama import Fore, Style
from litellm import completion, token_counter

from dir_assistant.assistant.git_assistant import GitAssistant


class LiteLLMAssistant(GitAssistant):
    def __init__(
        self,
        lite_llm_model,
        lite_llm_model_uses_system_message,
        lite_llm_context_size,
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
        )
        self.lite_llm_model = lite_llm_model
        self.context_size = lite_llm_context_size
        self.pass_through_context_size = lite_llm_pass_through_context_size
        self.lite_llm_model_uses_system_message = lite_llm_model_uses_system_message
        print(
            f"{Fore.LIGHTBLACK_EX}LiteLLM context size: {self.context_size}{Style.RESET_ALL}"
        )

    def initialize_history(self):
        super().initialize_history()
        if not self.lite_llm_model_uses_system_message:
            self.chat_history[0]["role"] = "user"

    def call_completion(self, chat_history):
        if self.pass_through_context_size:
            return completion(
                model=self.lite_llm_model,
                messages=chat_history,
                stream=True,
                timeout=600,
                num_ctx=self.context_size,
            )
        else:
            return completion(
                model=self.lite_llm_model,
                messages=chat_history,
                stream=True,
                timeout=600,
            )

    def run_completion_generator(
        self, completion_output, output_message, write_to_stdout
    ):
        for chunk in completion_output:
            delta = chunk["choices"][0]["delta"]
            if "content" in delta and delta["content"] != None:
                output_message["content"] += delta["content"]
                if write_to_stdout:
                    sys.stdout.write(delta["content"])
                    sys.stdout.flush()
        return output_message

    def count_tokens(self, text):
        return token_counter(
            model=self.lite_llm_model, messages=[{"user": "role", "content": text}]
        )
