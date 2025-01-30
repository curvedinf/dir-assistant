import pytest
import pty
import os
import subprocess
import time
import sys

def test_virtual_terminal_smoketest():
    """
    Smoke test for the dir-assistant CLI application in a virtual terminal environment.
    This test verifies that dir-assistant can handle multi-line prompts submitted via Alt-Enter,
    allowing newlines in user input. It uses a pseudo-terminal to simulate user interaction.
    """
    def read_until(master_fd, prompt, timeout=5):
        """
        Reads from the master file descriptor until the specified prompt is found
        or the timeout is reached.
        Args:
            master_fd (int): File descriptor for the master end of the pty.
            prompt (str): The string to wait for in the output.
            timeout (int): Maximum time to wait in seconds.
        Returns:
            str: The accumulated output as a decoded string.
        """
        output = ""
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                # Read up to 1024 bytes from the master fd
                data = os.read(master_fd, 1024).decode(errors="ignore")
                output += data
                # Print output to test stdout immediately
                sys.stdout.write(data)
                sys.stdout.flush()
                if prompt in output:
                    return output
            except OSError:
                # If the read fails, return what has been read so far
                break
            time.sleep(0.1)
        return output

    def send_input(master_fd, input_str):
        """
        Sends an input string to the master file descriptor.
        Args:
            master_fd (int): File descriptor for the master end of the pty.
            input_str (str): The string to send as input.
        """
        os.write(master_fd, input_str.encode())

    # Create a new pseudo-terminal pair
    master_fd, slave_fd = pty.openpty()
    
    try:
        # Start the dir-assistant subprocess connected to the slave end of the pty
        process = subprocess.Popen(
            ["python", "-m", "dir_assistant"],
            stdin=slave_fd,
            stdout=slave_fd,
            stderr=slave_fd,
            universal_newlines=True,
            bufsize=0
        )

        # Allow some time for the application to start
        time.sleep(1)

        # Read the startup messages until the main prompt is reached
        output = read_until(master_fd, "Type 'exit' to quit the conversation.", timeout=10)
        assert "Type 'exit' to quit the conversation." in output, "Startup prompt not found."

        # Prepare a multi-line prompt
        multi_line_prompt = "This is a multi-line prompt\nwith several lines.\nPlease process it accordingly."

        # Simulate pressing Alt-Enter by sending the appropriate escape sequence
        # Alt-Enter is often represented by sending an escape character followed by Enter
        alt_enter = "\x1b\r"  # ESC + carriage return

        # Send the multi-line prompt followed by Alt-Enter to submit
        send_input(master_fd, multi_line_prompt + alt_enter)

        # Read the response from the assistant until "Goodbye!" is found
        response = read_until(master_fd, "Goodbye!", timeout=10)

        # Optionally, perform assertions on the response
        assert "Goodbye!" in response, "Exit confirmation not received."
    
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