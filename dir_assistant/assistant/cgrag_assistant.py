import copy
import sys

from colorama import Fore, Style

from dir_assistant.assistant.base_assistant import BaseAssistant


class CGRAGAssistant(BaseAssistant):
    def __init__(
        self,
        system_instructions,
        embed,
        index,
        chunks,
        context_file_ratio,
        output_acceptance_retries,
        use_cgrag,
        print_cgrag,
    ):
        super().__init__(
            system_instructions,
            embed,
            index,
            chunks,
            context_file_ratio,
            output_acceptance_retries,
        )
        self.use_cgrag = use_cgrag
        self.print_cgrag = print_cgrag

    def write_assistant_thinking_message(self):
        # Disable CGRAG if the fileset is smaller than 4x the LLM context
        # total_tokens = sum(chunk['tokens'] for chunk in self.chunks)

        # Display the assistant thinking message
        if self.use_cgrag and self.print_cgrag:
            sys.stdout.write(
                f"{Style.BRIGHT}{Fore.BLUE}\nCGRAG Guidance: \n\n{Style.RESET_ALL}"
            )
        else:
            sys.stdout.write(
                f"{Style.BRIGHT}{Fore.GREEN}\nAssistant: \n\n{Style.RESET_ALL}"
            )
        if self.use_cgrag:
            sys.stdout.write(
                f"{Style.BRIGHT}{Fore.WHITE}\r(generating contextual guidance...){Style.RESET_ALL}"
            )
        else:
            sys.stdout.write(
                f"{Style.BRIGHT}{Fore.WHITE}\r(thinking...){Style.RESET_ALL}"
            )
        sys.stdout.flush()

    def print_cgrag_output(self, cgrag_output):
        if self.print_cgrag:
            sys.stdout.write(Style.BRIGHT + Fore.WHITE + "\r" + (" " * 36))
            sys.stdout.write(
                Style.BRIGHT + Fore.WHITE + f"\r{cgrag_output}\n\n" + Style.RESET_ALL
            )
            sys.stdout.write(
                Style.BRIGHT + Fore.GREEN + "Assistant: \n\n" + Style.RESET_ALL
            )
        else:
            sys.stdout.write(Style.BRIGHT + Fore.WHITE + "\r" + (" " * 36))
        sys.stdout.write("\r(thinking...)" + Style.RESET_ALL)

    def create_cgrag_prompt(self, base_prompt):
        return f"""What information related to the included files is important to answering the following 
user prompt?

User prompt: '{base_prompt}'

Respond with only a list of information and concepts. Include in the list all information and concepts necessary to
answer the prompt, including those in the included files and those which the included files do not contain. Your
response will be used to create an LLM embedding that will be used in a RAG to find the appropriate files which are 
needed to answer the user prompt. There may be many files not currently included which have more relevant information, 
so your response must include the most important concepts and information required to accurately answer the user 
prompt. Keep the list length to around 20 items. If the prompt is referencing code, list specific class, 
function, and variable names as applicable to answering the user prompt.
"""

    def run_stream_processes(self, user_input, write_to_stdout):
        if self.use_cgrag:
            relevant_full_text = self.build_relevant_full_text(user_input)
            cgrag_prompt = self.create_cgrag_prompt(user_input)
            cgrag_content = relevant_full_text + cgrag_prompt
            cgrag_history = copy.deepcopy(self.chat_history)
            cgrag_prompt_history = self.create_user_history(
                cgrag_content, cgrag_content
            )
            cgrag_history.append(cgrag_prompt_history)
            self.cull_history_list(cgrag_history)
            cgrag_generator = self.call_completion(cgrag_history)
            output_history = self.create_empty_history()
            output_history = self.run_completion_generator(
                cgrag_generator, output_history, False
            )
            relevant_full_text = self.build_relevant_full_text(
                output_history["content"]
            )
            self.print_cgrag_output(output_history["content"])
            sys.stdout.flush()
        else:
            relevant_full_text = self.build_relevant_full_text(user_input)
        prompt = self.create_prompt(user_input)
        return self.run_basic_chat_stream(prompt, relevant_full_text, write_to_stdout)
