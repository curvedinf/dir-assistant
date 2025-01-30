import os
import pty
import subprocess
import time
from test.utils import ALT_ENTER, read_until, send_input


def test_smoketest_noninteractive():
    """
    Smoke test for the dir-assistant CLI application in a virtual terminal environment.
    This test verifies that dir-assistant can handle multi-line prompts submitted via Alt-Enter,
    allowing newlines in user input. It uses a pseudo-terminal to simulate user interaction.

    - Requires -s pytest flag to run
    - Requires OPENAI_API_KEY configured
    """

    new_env = os.environ.copy()

    # Modify the environment for the subprocess
    new_env["DIR_ASSISTANT__LITELLM_MODEL"] = "gpt-4o-mini"
    new_env["DIR_ASSISTANT__LITELLM_CONTEXT_SIZE"] = "10000"
    # Use the current embed model so we don't have to reindex

    result = subprocess.run(
        ["python", "-m", "dir_assistant", "-s", "What does this codebase do?"],
        capture_output=True,
        text=True,
        check=False,
        env=new_env,
    )

    print(result.stdout)
    assert result.returncode == 0
    assert len(result.stdout) > 50
