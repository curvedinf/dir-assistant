import os
import pty
import subprocess
import time
from test.utils import ALT_ENTER, read_until, send_input


def test_smoketest_interactive():
    """
    Smoke test for the dir-assistant CLI application in a virtual terminal environment.
    This test verifies that dir-assistant can handle multi-line prompts submitted via Alt-Enter,
    allowing newlines in user input. It uses a pseudo-terminal to simulate user interaction.

    - Requires -s pytest flag to run
    - Requires OPENAI_API_KEY configured
    """

    # Create a new pseudo-terminal pair
    master_fd, slave_fd = pty.openpty()

    try:
        new_env = os.environ.copy()

        # Modify the environment for the subprocess
        new_env["DIR_ASSISTANT__VERBOSE"] = "true"
        new_env["DIR_ASSISTANT__LITELLM_MODEL"] = "gpt-4o-mini"
        new_env["DIR_ASSISTANT__LITELLM_CONTEXT_SIZE"] = "10000"
        # Use the current embed model so we don't have to reindex

        # Start the dir-assistant subprocess connected to the slave end of the pty
        process = subprocess.Popen(
            ["python", "-m", "dir_assistant"],
            stdin=slave_fd,
            stdout=slave_fd,
            stderr=slave_fd,
            universal_newlines=True,
            bufsize=0,
            env=new_env,
        )

        # Allow some time for the application to start
        time.sleep(1)

        # Read the startup messages until the main prompt is reached
        output = read_until(
            master_fd,
            "You (Press ALT-Enter, OPT-Enter, or CTRL-O to submit):",
            timeout=60,
        )
        assert (
            "Type 'exit' to quit the conversation." in output
        ), "Startup prompt not found."

        # Prepare a multi-line prompt
        multi_line_prompt = "Describe the purpose of this codebase.\n\nThen say roughly how many lines of code it has."

        # Send the multi-line prompt followed by Alt-Enter to submit
        send_input(master_fd, multi_line_prompt + ALT_ENTER)

        # Read the response from the assistant until "Goodbye!" is found
        response = read_until(
            master_fd,
            "You (Press ALT-Enter, OPT-Enter, or CTRL-O to submit):",
            timeout=60,
        )
        assert len(response) > 50
    finally:
        # Terminate the subprocess if it's still running
        process.terminate()
        try:
            process.wait(timeout=2)
        except subprocess.TimeoutExpired:
            process.kill()
        # Close both ends of the pty
        os.close(master_fd)
        os.close(slave_fd)
