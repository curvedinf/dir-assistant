```python
import os
import sys
import tempfile
from colorama import Style, Fore
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
            should_diff_output = self.run_one_off_completion(f"""Does the prompt below request changes to files? 
Respond only with "YES" or "NO". Do not respond with additional characters.
User prompt:
{user_input}
""")
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
first line of the response.
Example response:
/home/user/hello_project/hello_world.py
if __name__ == "__main__":
    print("Hello, World!")
Real response:
"""
            else:
                return user_input

    def run_post_stream_processes(self, user_input, stream_output, write_to_stdout):
        if (not self.commit_to_git or not self.should_diff) and not self.git_apply_error:
            return super().run_post_stream_processes(user_input, stream_output, write_to_stdout)
        else:
            sys.stdout.write(f'{Style.BRIGHT}{Fore.BLUE}Apply these changes? (Y/N): {Style.RESET_ALL}')
            apply_changes = prompt('', multiline=False).strip().lower()
            if write_to_stdout:
                sys.stdout.write('\n')
            if apply_changes == 'y':
                output_lines = stream_output.split('\n')
                changed_filepath = output_lines[0].strip()
                cleaned_output = '\n'.join(line for line in output_lines[1:] if not (line.startswith('```') or line.endswith('```')))
                with open(changed_filepath, 'w') as changed_file:
                    changed_file.write(cleaned_output)
                os.system('git add .')
                os.system(f'git commit -m "{user_input.strip()}"')
                if write_to_stdout:
                    sys.stdout.write(f'\n{Style.BRIGHT}Changes committed.{Style.RESET_ALL}\n\n')
                    sys.stdout.flush()
            return True

    def stream_chat(self, user_input):
        self.git_apply_error = None
        super().stream_chat(user_input)
```