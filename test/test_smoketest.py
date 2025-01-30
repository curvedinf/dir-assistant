import os
import pty
import subprocess
import sys
import pytest

@pytest.fixture
def repo_root():
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

@pytest.fixture
def python_executable():
    return sys.executable

def run_dir_assistant_with_pty(cmd_args, cwd, input_commands):
    master_fd, slave_fd = pty.openpty()
    process = subprocess.Popen(
        [sys.executable, "-m", "dir_assistant"] + cmd_args,
        cwd=cwd,
        stdin=slave_fd,
        stdout=slave_fd,
        stderr=subprocess.PIPE,
        text=True
    )
    os.close(slave_fd)  # Close the slave fd in the parent process
    stdout = ""
    for cmd in input_commands:
        os.write(master_fd, (cmd + "\x1b\r").encode())
        while True:
            try:
                data = os.read(master_fd, 1024).decode()
                stdout += data
                sys.stdout.write(data)
                sys.stdout.flush()
                if "You (Press ALT-Enter, OPT-Enter, or CTRL-O to submit):" in data:
                    break
            except OSError:
                break
    process.wait()
    os.close(master_fd)
    return stdout, process.returncode

def test_start_mode_default_models(repo_root, python_executable):
    simulated_commands = ["exit"]
    stdout, returncode = run_dir_assistant_with_pty(["start"], cwd=repo_root, input_commands=simulated_commands)
    assert returncode == 0, f"STDERR: {stdout}"
    assert "Assistant:" in stdout, "Expected Assistant prompt not found in STDOUT."