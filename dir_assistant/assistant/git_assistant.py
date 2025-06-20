import os
import subprocess
from dir_assistant.assistant.cgrag_assistant import CGRAGAssistant


class GitAssistant(CGRAGAssistant):
    def __init__(
        self,
        system_instructions,
        embed,
        index,
        chunks,
        artifact_metadata,
        context_file_ratio,
        artifact_excludable_factor,
        api_context_cache_ttl,
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
            artifact_metadata,
            context_file_ratio,
            artifact_excludable_factor,
            api_context_cache_ttl,
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

    def run_git_commit(self, prompt, content):
        print("\nCommitting changes to git...")
        try:
            subprocess.run(["git", "add", "."], check=True, capture_output=True, text=True)
            commit_message = f"feat: respond to '{prompt[:50]}...'"
            result = subprocess.run(
                ["git", "commit", "-m", commit_message],
                check=True,
                capture_output=True,
                text=True,
            )
            print(f"Changes committed: {result.stdout.strip()}")
        except subprocess.CalledProcessError as e:
            # If there are no changes to commit, `git commit` can fail.
            # We can check the error message to see if that's the case.
            if "nothing to commit" in e.stderr:
                print("No changes to commit.")
            else:
                print(f"An error occurred during git commit: {e.stderr}")

