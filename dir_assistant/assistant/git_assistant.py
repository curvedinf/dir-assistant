import os
import sys
from colorama import Fore, Style
from prompt_toolkit import prompt
from dir_assistant.assistant.cgrag_assistant import CGRAGAssistant

class GitAssistant(CGRAGAssistant):
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
        )
        self.commit_to_git = commit_to_git

    def create_prompt(self, user_input):
        if not self.commit_to_git:
            return user_input
        else:
            # Ask the LLM if a diff commit is appropriate
            should_diff_output = self.run_one_off_completion(
                f"""Does the prompt below request changes to files? 
Respond only with one word: "YES" or "NO". Do not respond with additional words or characters, only "YES" or "NO".
User prompt:
{user_input}
"""
            )
            if "YES" in should_diff_output:
                self.should_diff = True
            elif "NO" in should_diff_output:
                self.should_diff = False
            else:
                self.should_diff = None
            if self.should_diff:
                return f"""User Prompt:
{user_input}
----------------------------------
Given the user prompt above and included file snippets, respond with the contents of a single file that has
the changes the user prompt requested. Do not provide an introduction, summary, or conclusion. Only respond 
with the file's contents. Do not respond with surrounding markdown. Add the filename of the file as the
first line of the response. It is okay to create a new file. Always respond with the entire contents of the 
new version of the file. Ensure white space and new lines are consistent with the original.
Example response:
/home/user/hello_project/hello_world.py
if __name__ == "__main__":
    print("Hello, World!")
"""
            else:
                return user_input

    def run_git_commit(self, user_input, stream_output):
        if (
            not self.commit_to_git or not self.should_diff
        ) and not self.git_apply_error:
            return
        
        if self.chat_mode:
            sys.stdout.write(
                f"{self.get_color_prefix(Style.BRIGHT, Fore.BLUE)}Apply these changes? (Y/N): {self.get_color_suffix()}"
            )
            apply_changes = prompt("", multiline=False).strip().lower()
        else:
            apply_changes = "n"
        if self.chat_mode:
            sys.stdout.write("\n")
        if "y" in apply_changes:
            # Commit any user-generated changes
            os.system("git add .")
            os.system(
                f'git commit -m "Automatic commit of user changes (dir-assistant)"'
            )
            output_lines = stream_output.split("\n")
            changed_filepath = output_lines[0].strip()
            file_content_lines = []
            if len(output_lines) > 1:
                file_content_lines = output_lines[1:]
            # Remove leading blank lines
            while file_content_lines and not file_content_lines[0].strip():
                file_content_lines.pop(0)
            # Remove leading ``` or ```language
            if file_content_lines and file_content_lines[0].strip().startswith(
                "```"
            ):
                file_content_lines.pop(0)
            # Remove trailing blank lines
            while file_content_lines and not file_content_lines[-1].strip():
                file_content_lines.pop()
            # Remove trailing ```
            if file_content_lines and file_content_lines[-1].strip().endswith(
                "```"
            ):
                file_content_lines.pop()
            cleaned_output = "\n".join(file_content_lines)
            try:
                os.makedirs(os.path.dirname(changed_filepath), exist_ok=True)
                with open(changed_filepath, "w") as changed_file:
                    changed_file.write(cleaned_output)
            except Exception as e:
                if self.chat_mode:
                    sys.stdout.write(
                        f"\n{self.get_color_prefix(Style.BRIGHT)}Error while committing changes, skipping commit: {e}{self.get_color_suffix()}\n\n"
                    )
                    sys.stdout.flush()
                return
            os.system("git add .")
            os.system(f'git commit -m "{user_input.strip()}"')
            if self.chat_mode:
                sys.stdout.write(
                    f"\n{self.get_color_prefix(Style.BRIGHT)}Changes committed.{self.get_color_suffix()}\n\n"
                )
                sys.stdout.flush()

    def stream_chat(self, user_input):
        self.git_apply_error = None
        super().stream_chat(user_input)