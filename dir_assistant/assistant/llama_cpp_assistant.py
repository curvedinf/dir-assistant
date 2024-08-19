import sys

from colorama import Fore, Style
from llama_cpp import Llama

from dir_assistant.assistant.cgrag_assistant import CGRAGAssistant


class LlamaCppAssistant(CGRAGAssistant):
    def __init__(
        self,
        model_path,
        llama_cpp_options,
        system_instructions,
        embed,
        index,
        chunks,
        context_file_ratio,
        use_cgrag,
        print_cgrag,
        completion_options,
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
        self.llm = Llama(model_path=model_path, **llama_cpp_options)
        self.context_size = self.llm.context_params.n_ctx
        self.completion_options = completion_options
        print(
            f"{Fore.LIGHTBLACK_EX}LLM context size: {self.context_size}{Style.RESET_ALL}"
        )

    def call_completion(self, chat_history):
        return self.llm.create_chat_completion(
            messages=chat_history, stream=True, **self.completion_options
        )

    def run_completion_generator(self, completion_output, output_message, write_to_stdout=True):
        for chunk in completion_output:
            delta = chunk["choices"][0]["delta"]
            if "content" in delta:
                output_message["content"] += delta["content"]
                if write_to_stdout:
                    sys.stdout.write(delta["content"])
                    sys.stdout.flush()
        return output_message
