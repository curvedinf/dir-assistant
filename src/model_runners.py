import sys

from colorama import Style, Fore
from llama_cpp import Llama
from litellm import completion

from index import search_index, count_tokens


class BaseRunner:
    def __init__(
            self,
            system_instructions,
            embed,
            index,
            chunks,
            context_file_ratio
    ):
        self.embed = embed
        self.index = index
        self.chunks = chunks
        self.context_file_ratio = context_file_ratio
        system_instructions_tokens = count_tokens(embed, system_instructions)
        self.chat_history = [{
            "role": "system",
            "content": system_instructions,
            "tokens": system_instructions_tokens
        }]
        self.context_size = 8192

    def call_completion(self):
        # unimplemented on base class
        return []

    def write_chunks(self, completion_output, output_message):
        # unimplemented on base class
        return output_message

    def stream_chat(self, user_input):
        # Get the relevant chunks and concatenate them. Only use up to the context file ratio of the total tokens
        relevant_chunks = search_index(self.embed, self.index, user_input, self.chunks)
        relevant_full_text = ""
        chunk_total_tokens = 0
        for i, relevant_chunk in enumerate(relevant_chunks, start=1):
            chunk_total_tokens += relevant_chunk['tokens']
            if chunk_total_tokens >= self.context_size * self.context_file_ratio:
                break
            relevant_full_text += relevant_chunk['text'] + "\n\n"

        # Add the user input to the chat history
        user_content = relevant_full_text + user_input
        self.chat_history.append({
            "role": "user",
            "content": user_content,
            "tokens": count_tokens(self.embed, user_input)
        })

        # Remove old messages from the chat history if too large for context
        sum_of_tokens = sum([message["tokens"] for message in self.chat_history])
        while sum_of_tokens > self.context_size:
            self.chat_history = self.chat_history.pop(1)  # First history after the system instructions
            sum_of_tokens = sum([message["tokens"] for message in self.chat_history])

        # Display the assistant thinking message
        print(Style.BRIGHT + Fore.GREEN + '\nAssistant: \n' + Style.RESET_ALL)
        sys.stdout.write(Style.BRIGHT + Fore.WHITE + '\r(thinking...)' + Style.RESET_ALL)
        sys.stdout.flush()

        completion_output = self.call_completion()

        # Remove the files from the last user message
        self.chat_history[-1]["content"] = user_input

        # Display chat history
        output_message = {"role": "assistant", "content": "", "tokens": 0}
        sys.stdout.write(Style.BRIGHT + Fore.WHITE + '\r')
        output_message = self.write_chunks(completion_output, output_message)
        sys.stdout.write(Style.RESET_ALL + '\n\n')
        sys.stdout.flush()

        # Add the completion to the chat history
        output_message["tokens"] = count_tokens(self.embed, output_message["content"])
        self.chat_history.append(output_message)

class LlamaCppRunner(BaseRunner):
    def __init__(
            self,
            model_path,
            llama_cpp_options,
            system_instructions,
            embed,
            index,
            chunks,
            context_file_ratio
    ):
        super().__init__(system_instructions, embed, index, chunks, context_file_ratio)
        self.llm = Llama(
            model_path=model_path,
            **llama_cpp_options
        )
        self.context_size = self.llm.context_params.n_ctx
        print(f"LLM context size: {self.context_size}")

    def call_completion(self):
        return self.llm.create_chat_completion(
            messages=self.chat_history,
            stream=True
        )

    def write_chunks(self, completion_output, output_message):
        for chunk in completion_output:
            delta = chunk['choices'][0]['delta']
            if "content" in delta:
                output_message["content"] += delta["content"]
                sys.stdout.write(delta["content"])
                sys.stdout.flush()
        return output_message

class LiteLLMRunner(BaseRunner):
    def __init__(
            self,
            lite_llm_model,
            lite_llm_model_uses_system_message,
            lite_llm_context_size,
            system_instructions,
            embed,
            index,
            chunks,
            context_file_ratio
    ):
        super().__init__(system_instructions, embed, index, chunks, context_file_ratio)
        self.lite_llm_model = lite_llm_model
        self.context_size = lite_llm_context_size
        print(f"LiteLLM context size: {self.context_size}")
        if not lite_llm_model_uses_system_message:
            self.chat_history[0]['role'] = 'user'

    def call_completion(self):
        return completion(
            model=self.lite_llm_model,
            messages=self.chat_history,
            stream=True
        )

    def write_chunks(self, completion_output, output_message):
        for chunk in completion_output:
            delta = chunk['choices'][0]['delta']
            if "content" in delta and delta["content"] != None:
                output_message["content"] += delta["content"]
                sys.stdout.write(delta["content"])
                sys.stdout.flush()
        return output_message
