import subprocess
import sys
import os
import pytest

@pytest.fixture
def repo_root():
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

@pytest.fixture
def python_executable():
    return sys.executable

def run_dir_assistant(cmd_args, cwd, input=None):
    return subprocess.run(
        [sys.executable, "-m", "dir_assistant"] + cmd_args,
        cwd=cwd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        input=input  # Pass the simulated input here
    )

def test_start_mode_default_models(repo_root, python_executable):
    # Simulate typing 'exit' followed by a newline to terminate the interactive session
    simulated_input = "exit\n"
    
    result = run_dir_assistant(["start"], cwd=repo_root, input=simulated_input)
    
    assert result.returncode == 0, f"STDERR: {result.stderr}"
    assert "Assistant:" in result.stdout, "Expected Assistant prompt not found in STDOUT."

def test_single_prompt_mode(repo_root, python_executable):
    prompt = "What is the purpose of the dir-assistant project?"
    result = run_dir_assistant(["-s", prompt], cwd=repo_root)
    
    assert result.returncode == 0, f"STDERR: {result.stderr}"
    assert "Assistant:" in result.stdout

def test_api_model_gpt4o_mini(repo_root, python_executable, monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "your_openai_api_key_here")
    prompt = "Explain the functionality of the main.py script."
    result = run_dir_assistant(["-s", prompt], cwd=repo_root)
    
    assert result.returncode == 0, f"STDERR: {result.stderr}"
    assert "Assistant:" in result.stdout

def test_api_embed_model_text_embedding_3_small(repo_root, python_executable, monkeypatch):
    monkeypatch.setenv("DIR_ASSISTANT__LITELLM_EMBED_MODEL", "text-embedding-3-small")
    prompt = "Provide a summary of the project's README."
    result = run_dir_assistant(["-s", prompt], cwd=repo_root)
    
    assert result.returncode == 0, f"STDERR: {result.stderr}"
    assert "Assistant:" in result.stdout

def test_verbose_no_color_modes(repo_root, python_executable):
    prompt = "List all available commands in dir-assistant."
    result = run_dir_assistant(["start", "-v", "-n"], cwd=repo_root)
    
    assert result.returncode == 0, f"STDERR: {result.stderr}"
    assert "Assistant:" in result.stdout

def test_invalid_argument(repo_root, python_executable):
    prompt = "This should fail."
    result = run_dir_assistant(["-invalid_arg", prompt], cwd=repo_root)
    
    assert result.returncode != 0
    assert "error" in result.stderr.lower()