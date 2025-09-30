import unittest
from unittest.mock import patch, MagicMock
from dir_assistant.cli.start import initialize_llm
from dir_assistant.cli.config import CONFIG_DEFAULTS
class TestConcurrencyOverride(unittest.TestCase):
    def setUp(self):
        self.mock_args = MagicMock()
        self.mock_args.verbose = False
        self.mock_args.no_color = True
        self.mock_args.ignore = []
        self.mock_args.dirs = []
        self.config = CONFIG_DEFAULTS.copy()
        # Set non-default concurrency values to test against
        self.config["INDEX_CONCURRENT_FILES"] = 50
        self.config["INDEX_CHUNK_WORKERS"] = 50
        # Add dummy model paths to satisfy checks in initialize_llm
        self.config["LLM_MODEL"] = "dummy.gguf"
        self.config["EMBED_MODEL"] = "dummy-embed.gguf"
        self.config["LITELLM_COMPLETION_OPTIONS"]['model'] = 'dummy-api'
        self.config["LITELLM_EMBED_COMPLETION_OPTIONS"]['model'] = 'dummy-api-embed'
    @patch("dir_assistant.cli.start.create_file_index")
    @patch("dir_assistant.cli.start.LlamaCppEmbed")
    @patch("dir_assistant.cli.start.LiteLLMAssistant") # Mock the assistant to prevent initialization
    def test_local_embed_overrides_concurrency(self, mock_llm_assistant, mock_embed, mock_create_file_index):
        """Verify concurrency is set to 1 when ACTIVE_EMBED_IS_LOCAL is True."""
        mock_embed.return_value.get_chunk_size.return_value = 4096
        mock_create_file_index.return_value = (None, [])
        config_local = self.config.copy()
        config_local["ACTIVE_EMBED_IS_LOCAL"] = True
        config_local["ACTIVE_MODEL_IS_LOCAL"] = True
        initialize_llm(self.mock_args, config_local, chat_mode=False)
        self.assertTrue(mock_create_file_index.called)
        call_args = mock_create_file_index.call_args[0]
        
        # args are (embed, ignore_paths, embed_chunk_size, extra_dirs, verbose, 
        # index_concurrent_files, index_max_files_per_minute, 
        # index_chunk_workers, index_max_chunk_requests_per_minute)
        self.assertEqual(call_args[5], 1)  # index_concurrent_files
        self.assertEqual(call_args[7], 1)  # index_chunk_workers
    @patch("dir_assistant.cli.start.create_file_index")
    @patch("dir_assistant.cli.start.LiteLlmEmbed")
    @patch("dir_assistant.cli.start.LiteLLMAssistant")
    def test_api_embed_uses_config_concurrency(self, mock_llm_assistant, mock_embed, mock_create_file_index):
        """Verify concurrency uses config values when ACTIVE_EMBED_IS_LOCAL is False."""
        mock_create_file_index.return_value = (None, [])
        config_api = self.config.copy()
        config_api["ACTIVE_EMBED_IS_LOCAL"] = False
        config_api["ACTIVE_MODEL_IS_LOCAL"] = False
        initialize_llm(self.mock_args, config_api, chat_mode=False)
        self.assertTrue(mock_create_file_index.called)
        call_args = mock_create_file_index.call_args[0]
        self.assertEqual(call_args[5], self.config["INDEX_CONCURRENT_FILES"])  # index_concurrent_files
        self.assertEqual(call_args[7], self.config["INDEX_CHUNK_WORKERS"])  # index_chunk_workers
if __name__ == '__main__':
    unittest.main()
