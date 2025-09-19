import unittest
from unittest.mock import patch, MagicMock
from dir_assistant.assistant.base_assistant import BaseAssistant
from dir_assistant.assistant.cgrag_assistant import CGRAGAssistant
class TestArtifactRelevancyCutoff(unittest.TestCase):
    def setUp(self):
        # Mock dependencies for BaseAssistant and CGRAGAssistant
        self.mock_embed = MagicMock()
        self.mock_embed.count_tokens.return_value = 10
        self.mock_index = None
        # The full chunks list that the assistant "knows" about
        self.all_chunks = [
            {'text': 'chunk1_text\n\n', 'filepath': 'file1.txt'},
            {'text': 'chunk2_text\n\n', 'filepath': 'file2.txt'},
            {'text': 'chunk3_text\n\n', 'filepath': 'file3.txt'},
            {'text': 'chunk4_text\n\n', 'filepath': 'file4.txt'},
        ]
        # Sample search results with varying distances, as returned by search_index
        self.mock_search_results = [
            (self.all_chunks[0], 0.5),  # Relevant for both cutoffs
            (self.all_chunks[1], 1.0),  # Relevant for 1.5, not for 1.2
            (self.all_chunks[2], 1.6),  # Not relevant for 1.5
            (self.all_chunks[3], 2.0),  # Not relevant for 1.5
        ]
    @patch('dir_assistant.assistant.base_assistant.search_index')
    def test_base_assistant_relevancy_cutoff(self, mock_search_index):
        # Configure mock
        mock_search_index.return_value = self.mock_search_results
        # Instantiate assistant
        assistant = BaseAssistant(
            system_instructions="test",
            embed=self.mock_embed,
            index=self.mock_index,
            chunks=self.all_chunks,
            context_file_ratio=0.8,
            artifact_excludable_factor=0.1,
            artifact_relevancy_cutoff=1.5,
            artifact_relevancy_cgrag_cutoff=1.5, # not used by base assistant directly
            api_context_cache_ttl=3600,
            rag_optimizer_weights={},
            output_acceptance_retries=1,
            verbose=False,
            no_color=True,
            chat_mode=False,
            hide_thinking=True,
            thinking_start_pattern="",
            thinking_end_pattern="",
        )
        assistant.context_size = 1000 # to avoid issues with token limits
        assistant.count_tokens = MagicMock(return_value=10)
        # Run the method under test, using the instance's cutoff
        relevant_text = assistant.build_relevant_full_text("test query", assistant.artifact_relevancy_cutoff)
        # Assertions
        self.assertIn("chunk1_text", relevant_text)
        self.assertIn("chunk2_text", relevant_text)
        self.assertNotIn("chunk3_text", relevant_text)
        self.assertNotIn("chunk4_text", relevant_text)
        # Verify search_index was called
        mock_search_index.assert_called_once()
    @patch('dir_assistant.assistant.base_assistant.search_index')
    def test_cgrag_assistant_relevancy_cutoffs(self, mock_search_index):
        # Configure mock
        mock_search_index.return_value = self.mock_search_results
        # Instantiate assistant with different cutoffs for regular and CGRAG
        assistant = CGRAGAssistant(
            system_instructions="test",
            embed=self.mock_embed,
            index=self.mock_index,
            chunks=self.all_chunks,
            context_file_ratio=0.8,
            artifact_excludable_factor=0.1,
            artifact_relevancy_cutoff=1.5,
            artifact_relevancy_cgrag_cutoff=1.2, # Stricter cutoff for CGRAG
            api_context_cache_ttl=3600,
            rag_optimizer_weights={},
            output_acceptance_retries=1,
            use_cgrag=True,
            print_cgrag=False,
            verbose=False,
            no_color=True,
            chat_mode=False,
            hide_thinking=True,
            thinking_start_pattern="",
            thinking_end_pattern="",
        )
        assistant.context_size = 1000
        assistant.count_tokens = MagicMock(return_value=10)
        # Test CGRAG cutoff (1.2)
        cgrag_text = assistant.build_relevant_full_text("test query for cgrag", cutoff=assistant.artifact_relevancy_cgrag_cutoff)
        self.assertIn("chunk1_text", cgrag_text)
        self.assertNotIn("chunk2_text", cgrag_text)
        self.assertNotIn("chunk3_text", cgrag_text)
        self.assertNotIn("chunk4_text", cgrag_text)
        
        # Test regular cutoff (1.5)
        regular_text = assistant.build_relevant_full_text("test query for regular", cutoff=assistant.artifact_relevancy_cutoff)
        self.assertIn("chunk1_text", regular_text)
        self.assertIn("chunk2_text", regular_text)
        self.assertNotIn("chunk3_text", regular_text)
        self.assertNotIn("chunk4_text", regular_text)
if __name__ == '__main__':
    unittest.main()
