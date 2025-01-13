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

Real response:
"""
            else:
                return user_input

    def run_post_stream_processes(self, user_input, stream_output, write_to_stdout):
        if (
            not self.commit_to_git or not self.should_diff
        ) and not self.git_apply_error:
            return super().run_post_stream_processes(
                user_input, stream_output, write_to_stdout
            )
        else:
            sys.stdout.write(
                f"{Style.BRIGHT}{Fore.BLUE}Apply these changes? (Y/N): {Style.RESET_ALL}"
            )
            apply_changes = prompt("", multiline=False).strip().lower()
            if write_to_stdout:
                sys.stdout.write("\n")
            if apply_changes == "y":
                output_lines = stream_output.split("\n")
                changed_filepath = output_lines[0].strip()
                file_slice = output_lines[1:]
                if file_slice[0].startswith("```"):
                    file_slice = file_slice[1:]
                if file_slice[-1].endswith("```"):
                    file_slice = file_slice[:-1]
                cleaned_output = "\n".join(file_slice)
                try:
                    os.makedirs(os.path.dirname(changed_filepath), exist_ok=True)
                    with open(changed_filepath, "w") as changed_file:
                        changed_file.write(cleaned_output)
                except Exception as e:
                    return False
                os.system("git add .")
                os.system(f'git commit -m "{user_input.strip()}"')
                if write_to_stdout:
                    sys.stdout.write(
                        f"\n{Style.BRIGHT}Changes committed.{Style.RESET_ALL}\n\n"
                    )
                    sys.stdout.flush()
            return True

    def stream_chat(self, user_input):
        self.git_apply_error = None
        super().stream_chat(user_input)
