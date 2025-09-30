import os
import sys

from colorama import Fore, Style

try:
    from llama_cpp import Llama
except:
    pass
from dir_assistant.assistant.git_assistant import GitAssistant


class suppress_stdout_stderr(object):
    def __enter__(self):
        self.outnull_file = open(os.devnull, "w")
        self.errnull_file = open(os.devnull, "w")
        self.old_stdout_fileno_undup = sys.stdout.fileno()
        self.old_stderr_fileno_undup = sys.stderr.fileno()
        self.old_stdout_fileno = os.dup(sys.stdout.fileno())
        self.old_stderr_fileno = os.dup(sys.stderr.fileno())
        self.old_stdout = sys.stdout
        self.old_stderr = sys.stderr
        os.dup2(self.outnull_file.fileno(), self.old_stdout_fileno_undup)
        os.dup2(self.errnull_file.fileno(), self.old_stderr_fileno_undup)
        sys.stdout = self.outnull_file
        sys.stderr = self.errnull_file
        return self

    def __exit__(self, *_):
        sys.stdout = self.old_stdout
        sys.stderr = self.old_stderr
        os.dup2(self.old_stdout_fileno, self.old_stdout_fileno_undup)
        os.dup2(self.old_stderr_fileno, self.old_stderr_fileno_undup)
        os.close(self.old_stdout_fileno)
        os.close(self.old_stderr_fileno)
        self.outnull_file.close()
        self.errnull_file.close()


class LlamaCppAssistant(GitAssistant):
    def __init__(
        self,
        model_path,
        llama_cpp_options,
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
        completion_options,
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
        try:
            if self.verbose:
                self.llm = Llama(model_path=model_path, **llama_cpp_options)
            else:
                with suppress_stdout_stderr():
                    self.llm = Llama(model_path=model_path, **llama_cpp_options)
        except NameError:
            sys.stderr.write(
                "You currently have ACTIVE_MODEL_IS_LOCAL set to true but have not installed llama-cpp-python. "
                "Choose one of the following to continue:\n"
                "1) Set ACTIVE_MODEL_IS_LOCAL to false. Open the config file with 'dir-assistant config open'\n"
                "2) Run 'pip install llama-cpp-python' and try again.\n"
            )
            sys.stderr.flush()
            sys.exit(1)
        self.context_size = self.llm.context_params.n_ctx
        self.completion_options = completion_options
        if self.verbose and self.chat_mode:
            if not self.no_color:
                sys.stdout.write(Fore.LIGHTBLACK_EX)
            sys.stdout.write(
                f"{Fore.LIGHTBLACK_EX}LLM context size: {self.context_size}{Style.RESET_ALL}"
            )
            if not self.no_color:
                sys.stdout.write(Fore.RESET)
            sys.stdout.flush()

    def call_completion(self, chat_history, is_cgrag_call=False):
        if self.verbose:
            return self.llm.create_chat_completion(
                messages=chat_history, stream=True, **self.completion_options
            )
        else:
            with suppress_stdout_stderr():
                return self.llm.create_chat_completion(
                    messages=chat_history, stream=True, **self.completion_options
                )

    def count_tokens(
        self, text, role=None
    ):  # Added role=None for signature compatibility
        # Llama.cpp's tokenizer usually doesn't need a role for raw text tokenization.
        # The role is primarily for chat message structuring, which happens before this.
        return len(self.llm.tokenize(bytes(text, "utf-8")))
