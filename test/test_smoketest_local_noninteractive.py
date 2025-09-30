import os
import subprocess

from dir_assistant.cli.models import MODELS_DEFAULT_EMBED, MODELS_DEFAULT_LLM


def test_smoketest_local_noninteractive():
    """
    Smoke test for the dir-assistant CLI application in non-interactive mode with local models.
    This test verifies that dir-assistant can run a single prompt using the default
    local LLM and embedding models.
    - Requires -s pytest flag to run.
    - Requires default local models to be downloaded via `dir-assistant models download-embed`
      and `dir-assistant models download-llm`.
    """
    new_env = os.environ.copy()
    # Modify the environment for the subprocess to use local models
    new_env["DIR_ASSISTANT__ACTIVE_MODEL_IS_LOCAL"] = "true"
    new_env["DIR_ASSISTANT__ACTIVE_EMBED_IS_LOCAL"] = "true"
    new_env["DIR_ASSISTANT__LLM_MODEL"] = MODELS_DEFAULT_LLM
    new_env["DIR_ASSISTANT__EMBED_MODEL"] = MODELS_DEFAULT_EMBED

    new_env["DIR_ASSISTANT__USE_CGRAG"] = "true"

    new_env["DIR_ASSISTANT__LLAMA_CPP_OPTIONS__n_ctx"] = "10000"
    new_env["DIR_ASSISTANT__LLAMA_CPP_EMBED_OPTIONS__n_ctx"] = "2000"

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
