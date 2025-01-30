import os
import sys
import time

# Simulate pressing Alt-Enter by sending the appropriate escape sequence
# Alt-Enter is often represented by sending an escape character followed by Enter
ALT_ENTER = "\x1b\r"  # ESC + carriage return


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
