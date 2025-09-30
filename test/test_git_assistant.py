import os
import unittest
from unittest.mock import MagicMock, patch

from dir_assistant.assistant.git_assistant import GitAssistant


class TestGitAssistant(unittest.TestCase):
    def setUp(self):
        self.assistant = GitAssistant(
            system_instructions="Test instructions",
            embed=None,
            index=None,
            chunks=[],
            context_file_ratio=0.5,
            artifact_excludable_factor=0.5,
            artifact_cosine_cutoff=1.5,
            artifact_cosine_cgrag_cutoff=1.5,
            api_context_cache_ttl=3600,
            rag_optimizer_weights={},
            output_acceptance_retries=1,
            use_cgrag=False,
            print_cgrag=False,
            commit_to_git=True,
            verbose=False,
            no_color=True,
            chat_mode=True,
            hide_thinking=True,
            thinking_start_pattern="",
            thinking_end_pattern="",
        )
        self.assistant.should_diff = True
        self.assistant.git_apply_error = None

    @patch("dir_assistant.assistant.git_assistant.prompt", return_value="y")
    @patch("os.system")
    @patch("os.makedirs")
    @patch("builtins.open")
    def test_file_traversal_attack_blocked(
        self, mock_open, mock_makedirs, mock_system, mock_prompt
    ):
        # Simulate a malicious stream_output
        malicious_output = "../../../etc/passwd\nmalicious content"
        user_input = "test"
        # Mock the write_error_message method to capture its output
        self.assistant.write_error_message = MagicMock()
        # Run the method
        result = self.assistant.run_post_stream_processes(user_input, malicious_output)
        # Assert that the file was not opened for writing
        mock_open.assert_not_called()
        # Assert that the error message was called with the expected message
        self.assistant.write_error_message.assert_called_once()
        self.assertIn(
            "Invalid file path", self.assistant.write_error_message.call_args[0][0]
        )
        # Assert that the method returned True to abort the operation
        self.assertTrue(result)

    @patch("dir_assistant.assistant.git_assistant.prompt", return_value="y")
    @patch("os.system")
    @patch("os.makedirs")
    @patch("builtins.open")
    def test_absolute_path_attack_blocked(
        self, mock_open, mock_makedirs, mock_system, mock_prompt
    ):
        # Simulate a malicious stream_output
        malicious_output = "/root/.ssh/authorized_keys\nmalicious content"
        user_input = "test"
        # Mock the write_error_message method to capture its output
        self.assistant.write_error_message = MagicMock()
        # Run the method
        result = self.assistant.run_post_stream_processes(user_input, malicious_output)
        # Assert that the file was not opened for writing
        mock_open.assert_not_called()
        # Assert that the error message was called with the expected message
        self.assistant.write_error_message.assert_called_once()
        self.assertIn(
            "Invalid file path", self.assistant.write_error_message.call_args[0][0]
        )
        # Assert that the method returned True to abort the operation
        self.assertTrue(result)


if __name__ == "__main__":
    unittest.main()
