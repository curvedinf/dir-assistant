import copy
import sys

import numpy as np
from colorama import Style, Fore
from llama_cpp import Llama
from litellm import completion

from dir_assistant.index import search_index, count_tokens

class BaseRunner:
    def __init__(
            self,
            system_instructions,
            embed,
            index,
            chunks,
            context_file_ratio,
            use_cgrag,
            print_cgrag
    ):
        self.embed = embed
        self.index = index
        self.chunks = chunks
        self.context_file_ratio = context_file_ratio
        self.use_cgrag = use_cgrag
        self.print_cgrag = print_cgrag
        system_instructions_tokens = count_tokens(embed, system_instructions)
        self.chat_history = [{
            "role": "system",
            "content": system_instructions,
            "tokens": system_instructions_tokens
        }]
        self.context_size = 8192

    def call_completion(self, chat_history):
        # unimplemented on base class
        return []

    def write_chunks(self, completion_output, output_message):
        # unimplemented on base class
        return output_message

    def build_relevant_full_text(self, relevant_chunks):
        relevant_full_text = ""
        chunk_total_tokens = 0
        for i, relevant_chunk in enumerate(relevant_chunks, start=1):
            chunk_total_tokens += relevant_chunk['tokens']
            if chunk_total_tokens >= self.context_size * self.context_file_ratio:
                break
            relevant_full_text += relevant_chunk['text'] + "\n\n"
        return relevant_full_text

    def stream_chat(self, user_input):
        # Display the assistant thinking message
        if self.print_cgrag:
            sys.stdout.write(f'{Style.BRIGHT}{Fore.BLUE}\nCGRAG Guidance: \n\n{Style.RESET_ALL}')
        else:
            sys.stdout.write(f'{Style.BRIGHT}{Fore.GREEN}\nAssistant: \n\n{Style.RESET_ALL}')
        if self.use_cgrag:
            sys.stdout.write(f'{Style.BRIGHT}{Fore.WHITE}\r(generating contextual guidance...){Style.RESET_ALL}')
        else:
            sys.stdout.write(f'{Style.BRIGHT}{Fore.WHITE}\r(thinking...){Style.RESET_ALL}')
        sys.stdout.flush()

        relevant_chunks = search_index(self.embed, self.index, user_input, self.chunks)
        relevant_full_text = self.build_relevant_full_text(relevant_chunks)
        if self.use_cgrag:
            cgrag_prompt = f"""What information related to the included files is important to answering the following 
user prompt?

User prompt: '{user_input}'

Respond with only a list of information and concepts. Include in the list all information and concepts necessary to
answer the prompt, including those in the included files and those which the included files do not contain. Your
response will be used to create an LLM embedding that will be used in a RAG to find the appropriate files which are 
needed to answer the user prompt. There may be many files not currently included which have more relevant information, 
so your response must include the most important concepts and information required to accurately answer the user 
prompt. It is okay if the list is very long or short, but err on the side of a longer list so the RAG has more 
information to work with. If the prompt is referencing code, list specific class, function, and variable names.
"""
            cgrag_content = relevant_full_text + cgrag_prompt
            cgrag_history = copy.deepcopy(self.chat_history)
            cgrag_history.append({
                "role": "user",
                "content": cgrag_content,
                "tokens": count_tokens(self.embed, cgrag_content)
            })
            sum_of_tokens = sum([message["tokens"] for message in cgrag_history])
            while sum_of_tokens > self.context_size:
                cgrag_history.pop(0)
                sum_of_tokens = sum([message["tokens"] for message in cgrag_history])
            cgrag_output = self.call_completion(cgrag_history)
            output_message = {"role": "assistant", "content": "", "tokens": 0}
            output_message = self.write_chunks(cgrag_output, output_message, False)
            relevant_chunks = search_index(self.embed, self.index, output_message["content"], self.chunks)
            relevant_full_text = self.build_relevant_full_text(relevant_chunks)
            if self.print_cgrag:
                sys.stdout.write(Style.BRIGHT + Fore.WHITE + '\r' + (' '*36))
                sys.stdout.write(Style.BRIGHT + Fore.WHITE + f'\r{output_message["content"]}\n' + Style.RESET_ALL)
                sys.stdout.write(Style.BRIGHT + Fore.GREEN + 'Assistant: \n\n' + Style.RESET_ALL)
            else:
                sys.stdout.write(Style.BRIGHT + Fore.WHITE + '\r' + (' '*36))
            sys.stdout.write('\r(thinking...)' + Style.RESET_ALL)
            sys.stdout.flush()

        # Add the user input to the chat history
        user_content = relevant_full_text + user_input
        self.chat_history.append({
            "role": "user",
            "content": user_content, # content will be replaced with user_input a few lines below
            "tokens": count_tokens(self.embed, user_input) # we will be using user_input in the final history object
        })

        # Remove old messages from the chat history if too large for context
        sum_of_tokens = sum([message["tokens"] for message in self.chat_history])
        while sum_of_tokens > self.context_size:
            self.chat_history.pop(0)
            sum_of_tokens = sum([message["tokens"] for message in self.chat_history])

        completion_output = self.call_completion(self.chat_history)

        # Replace the RAG output with the user input. This reduces the size of the history for future prompts.
        self.chat_history[-1]["content"] = user_input

        # Display chat history
        output_message = {"role": "assistant", "content": "", "tokens": 0}
        sys.stdout.write(Style.BRIGHT + Fore.WHITE + '\r' + (' '*36) + '\r')
        output_message = self.write_chunks(completion_output, output_message)
        sys.stdout.write(Style.RESET_ALL + '\n\n')
        sys.stdout.flush()

        # Add the completion to the chat history
        output_message["tokens"] = count_tokens(self.embed, output_message["content"])
        self.chat_history.append(output_message)

    def update_index_and_chunks(self, file_path, new_chunks, new_embeddings):
        # Remove old chunks and embeddings for this file
        self.chunks = [chunk for chunk in self.chunks if chunk['filepath'] != file_path]
        self.chunks.extend(new_chunks)

        # Find indices of old embeddings
        old_embedding_indices = [i for i, chunk in enumerate(self.chunks) if chunk['filepath'] == file_path]

        if old_embedding_indices:
            # Convert list to numpy array
            old_embedding_indices = np.array(old_embedding_indices, dtype=np.int64)

            # Remove old embeddings from the index
            self.index.remove_ids(old_embedding_indices)

        # Add new embeddings to the index
        if new_embeddings:
            self.index.add(np.array(new_embeddings))


class LlamaCppRunner(BaseRunner):
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
            print_cgrag
    ):
        super().__init__(
            system_instructions,
            embed,
            index,
            chunks,
            context_file_ratio,
            use_cgrag,
            print_cgrag
        )
        self.llm = Llama(
            model_path=model_path,
            **llama_cpp_options
        )
        self.context_size = self.llm.context_params.n_ctx
        print(f"{Fore.LIGHTBLACK_EX}LLM context size: {self.context_size}{Style.RESET_ALL}")

    def call_completion(self, chat_history):
        return self.llm.create_chat_completion(
            messages=chat_history,
            stream=True
        )

    def write_chunks(self, completion_output, output_message, write_to_stdout=True):
        for chunk in completion_output:
            delta = chunk['choices'][0]['delta']
            if "content" in delta:
                output_message["content"] += delta["content"]
                if write_to_stdout:
                    sys.stdout.write(delta["content"])
                    sys.stdout.flush()
        return output_message

class LiteLLMRunner(BaseRunner):
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
            print_cgrag
    ):
        super().__init__(
            system_instructions,
            embed,
            index,
            chunks,
            context_file_ratio,
            use_cgrag,
            print_cgrag
        )
        self.lite_llm_model = lite_llm_model
        self.context_size = lite_llm_context_size
        self.pass_through_context_size = lite_llm_pass_through_context_size
        print(f"{Fore.LIGHTBLACK_EX}LiteLLM context size: {self.context_size}{Style.RESET_ALL}")
        if not lite_llm_model_uses_system_message:
            self.chat_history[0]['role'] = 'user'

    def call_completion(self, chat_history):
        if self.pass_through_context_size:
            return completion(
                model=self.lite_llm_model,
                messages=chat_history,
                stream=True,
                timeout=600,
                num_ctx=self.context_size
            )
        else:
            return completion(
                model=self.lite_llm_model,
                messages=chat_history,
                stream=True,
                timeout=600
            )

    def write_chunks(self, completion_output, output_message, write_to_stdout=True):
        for chunk in completion_output:
            delta = chunk['choices'][0]['delta']
            if "content" in delta and delta["content"] != None:
                output_message["content"] += delta["content"]
                if write_to_stdout:
                    sys.stdout.write(delta["content"])
                    sys.stdout.flush()
        return output_message
