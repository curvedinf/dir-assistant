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
        artifact_excludable_factor,
        api_context_cache_ttl,
        rag_optimizer_weights,
        output_acceptance_retries,
        use_cgrag,
        print_cgrag,
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
            api_context_cache_ttl,
            rag_optimizer_weights,
            output_acceptance_retries,
            verbose,
            no_color,
            chat_mode,
            hide_thinking,
            thinking_start_pattern,
            thinking_end_pattern,
        )
        self.use_cgrag = use_cgrag
        self.print_cgrag = print_cgrag

    def write_assistant_thinking_message(self):
        # Display the assistant thinking message
        if self.chat_mode:
            if self.use_cgrag and self.print_cgrag:
                sys.stdout.write(
                    f"{self.get_color_prefix(Style.BRIGHT, Fore.BLUE)}\nCGRAG Guidance: \n\n{self.get_color_suffix()}"
                )
            else:
                sys.stdout.write(
                    f"{self.get_color_prefix(Style.BRIGHT, Fore.GREEN)}\nAssistant: \n\n{self.get_color_suffix()}"
                )
            if self.use_cgrag:
                sys.stdout.write(
                    f"{self.get_color_prefix(Style.BRIGHT, Fore.WHITE)}\r"
                    f"(generating contextual guidance...){self.get_color_suffix()}"
                )
            else:
                sys.stdout.write(
                    f"{self.get_color_prefix(Style.BRIGHT, Fore.WHITE)}\r(thinking...){self.get_color_suffix()}"
                )
            if self.print_cgrag:
                sys.stdout.write("\r")
            sys.stdout.flush()

    def print_cgrag_output(self, cgrag_output):
        if self.chat_mode:
            if self.print_cgrag:
                sys.stdout.write(
                    self.get_color_prefix(Style.BRIGHT, Fore.GREEN)
                    + "\n\nAssistant: \n\n"
                    + self.get_color_suffix()
                )
                sys.stdout.write(
                    f"{self.get_color_prefix(Style.BRIGHT, Fore.WHITE)}\r(thinking...){self.get_color_suffix()}"
                )
            else:
                sys.stdout.write(f"\r{' ' * 36}\r")
                sys.stdout.write(
                    f"{self.get_color_prefix(Style.BRIGHT, Fore.WHITE)}(thinking...){self.get_color_suffix()}"
                )
            sys.stdout.flush()

    def create_cgrag_prompt(self, base_prompt):
        return f"""If this is the final part of this prompt, this is the actual request to respond to. All information
above should be considered supplementary to this request to help answer it:

What information related to the included files above is important to answering the following user prompt?

User request (DO NOT ANSWER IT, only list the information needed to answer it):

<---------------------------->
'{base_prompt}'
<---------------------------->

Respond with only a list of information and concepts. Include in the list all information and concepts necessary to
answer the prompt, including those in the included files and those which the included files do not contain. Your
response will be used to create an LLM embedding that will be used in a RAG to find the appropriate files which are 
needed to answer the user prompt. There may be many files not currently included which have more relevant information, 
so your response must include the most important concepts and information required to accurately answer the user 
prompt. Keep the list length to around 20 items. If the prompt is referencing code, list specific class, 
function, and variable names as applicable to answering the user prompt.
"""

    def run_stream_processes(self, user_input, one_off=False):
        if self.use_cgrag:
            cgrag_relevant_full_text = self.build_relevant_full_text(user_input)
            cgrag_prompt = self.create_cgrag_prompt(user_input)
            cgrag_history = copy.deepcopy(self.chat_history)
            cgrag_prompt_history = self.create_user_history(
                cgrag_prompt, cgrag_relevant_full_text
            )
            cgrag_history.append(cgrag_prompt_history)
            self.cull_history_list(cgrag_history)
            cgrag_generator = self.call_completion(cgrag_history, is_cgrag_call=True)
            output_history = self.create_empty_history()
            output_history = self.run_completion_generator(
                cgrag_generator, output_history, self.print_cgrag
            )
            output_history["content"] = self.remove_thinking_message(
                output_history["content"]
            )
            combined_query = f"Original prompt:\n{user_input}\nNeeded information:\n{output_history['content']}"
            relevant_full_text = self.build_relevant_full_text(combined_query)
            self.print_cgrag_output(output_history["content"])
        else:
            relevant_full_text = self.build_relevant_full_text(user_input)
        prompt = self.create_prompt(user_input)
        return self.run_basic_chat_stream(prompt, relevant_full_text, one_off)
