import unittest
import subprocess
import sys
import os

class TestDirAssistantSmoke(unittest.TestCase):
    def setUp(self):
        # Ensure the tests are run from the repository root
        self.repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.python_executable = sys.executable
        self.dir_assistant_cmd = [
            self.python_executable,
            "-m",
            "dir_assistant"
        ]

    def test_start_mode_default_models(self):
        """Test running dir-assistant in start mode with default local LLM and embed models."""
        result = subprocess.run(
            self.dir_assistant_cmd + ["start"],
            cwd=self.repo_root,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        self.assertEqual(result.returncode, 0, msg=f"STDERR: {result.stderr}")

    def test_single_prompt_mode(self):
        """Test running dir-assistant with the single prompt mode."""
        prompt = "What is the purpose of the dir-assistant project?"
        result = subprocess.run(
            self.dir_assistant_cmd + ["-s", prompt],
            cwd=self.repo_root,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        self.assertEqual(result.returncode, 0, msg=f"STDERR: {result.stderr}")
        self.assertIn("Assistant:", result.stdout)

    def test_api_model_gpt4o_mini(self):
        """Test running dir-assistant using the 'gpt-4o-mini' API model."""
        # Ensure the OpenAI API key is set
        os.environ["OPENAI_API_KEY"] = "your_openai_api_key_here"
        prompt = "Explain the functionality of the main.py script."
        result = subprocess.run(
            self.dir_assistant_cmd + ["-s", prompt],
            cwd=self.repo_root,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        self.assertEqual(result.returncode, 0, msg=f"STDERR: {result.stderr}")
        self.assertIn("Assistant:", result.stdout)

    def test_api_embed_model_text_embedding_3_small(self):
        """Test running dir-assistant using the 'text-embedding-3-small' API embed model."""
        # Set the embed model to 'text-embedding-3-small'
        os.environ["DIR_ASSISTANT__LITELLM_EMBED_MODEL"] = "text-embedding-3-small"
        prompt = "Provide a summary of the project's README."
        result = subprocess.run(
            self.dir_assistant_cmd + ["-s", prompt],
            cwd=self.repo_root,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        self.assertEqual(result.returncode, 0, msg=f"STDERR: {result.stderr}")
        self.assertIn("Assistant:", result.stdout)

    def test_verbose_no_color_modes(self):
        """Test running dir-assistant with verbose and no-color options."""
        prompt = "List all available commands in dir-assistant."
        result = subprocess.run(
            self.dir_assistant_cmd + ["start", "-v", "-n"],
            cwd=self.repo_root,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        self.assertEqual(result.returncode, 0, msg=f"STDERR: {result.stderr}")
        self.assertIn("Assistant:", result.stdout)

    def test_invalid_argument(self):
        """Test running dir-assistant with an invalid argument."""
        prompt = "This should fail."
        result = subprocess.run(
            self.dir_assistant_cmd + ["-invalid_arg", prompt],
            cwd=self.repo_root,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("error", result.stderr.lower())

if __name__ == "__main__":
    unittest.main()