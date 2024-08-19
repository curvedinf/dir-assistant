import sys

from colorama import Fore, Style
from litellm import completion

from dir_assistant.assistant.base_assistant import BaseAssistant


class LiteLLMAssistant(BaseAssistant):
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
        use_cgrag,
        print_cgrag,
    ):
        super().__init__(
            system_instructions,
            embed,
            index,
            chunks,
            context_file_ratio,
            use_cgrag,
            print_cgrag,
        )
        self.lite_llm_model = lite_llm_model
        self.context_size = lite_llm_context_size
        self.pass_through_context_size = lite_llm_pass_through_context_size
        print(
            f"{Fore.LIGHTBLACK_EX}LiteLLM context size: {self.context_size}{Style.RESET_ALL}"
        )
        if not lite_llm_model_uses_system_message:
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

    def write_chunks(self, completion_output, output_message, write_to_stdout=True):
        for chunk in completion_output:
            delta = chunk["choices"][0]["delta"]
            if "content" in delta and delta["content"] != None:
                output_message["content"] += delta["content"]
                if write_to_stdout:
                    sys.stdout.write(delta["content"])
                    sys.stdout.flush()
        return output_message
