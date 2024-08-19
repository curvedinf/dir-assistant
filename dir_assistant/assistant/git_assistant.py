import os
import tempfile

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
Create a .diff file with changes that could be applied to the attached files that address the user's prompt.
Do not provide an introduction, summary, or conclusion. Only respond with the .diff file's contents.
"""
            else:
                return user_input

    def run_post_stream_processes(self, user_input, stream_output, write_to_stdout):
        if not self.commit_to_git or not self.should_diff:
            return super().run_post_stream_processes(user_input, stream_output, write_to_stdout)
        else:
            apply_changes = prompt("Apply these changes? (Y/N): ", multiline=False).strip().lower()
            if apply_changes == 'y':
                with tempfile.NamedTemporaryFile(delete=False) as temp_file:
                    temp_file.write(stream_output)
                exit_code = os.system(f"git apply {temp_file.name}")
                if exit_code != 0:
                    return False
                commit_message = user_input.strip()
                os.system('git add .')
                os.system(f'git commit -m "{commit_message}"')
            return True