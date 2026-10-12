import os
import sys
import unittest
from unittest.mock import patch, MagicMock

# Make sure Python can find our source code
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(current_dir, '..', 'src')
sys.path.append(src_dir)

from llm_module.client import GeminiClient

class TestGeminiClient(unittest.TestCase):
    
    @patch('llm_module.client.genai.configure')
    @patch('llm_module.client.genai.GenerativeModel')
    # We also mock os.getenv so this test runs even if the user hasn't set up the .env file yet.
    @patch.dict(os.environ, {"GEMINI_API_KEY": "fake_test_key", "GEMINI_MODEL": "test-model"})
    def test_ask_question_success(self, mock_generative_model, mock_configure):
        # 1. Setup the Mock (Fake) API Response
        # We tell our fake model to return a specific answer when called, skipping the real internet.
        mock_model_instance = MagicMock()
        mock_response = MagicMock()
        mock_response.text = "This is a fake response about photosynthesis."
        mock_model_instance.generate_content.return_value = mock_response
        
        # When our client initializes the model, it should get our fake instance
        mock_generative_model.return_value = mock_model_instance
        
        # 2. Run the actual code
        client = GeminiClient()
        result = client.ask_question("What is photosynthesis?")
        
        # 3. Assert (Verify) the results
        # We check if the result matches our fake text
        self.assertEqual(result, "This is a fake response about photosynthesis.")
        
        # We also check that generate_content was actually called with the exact prompt
        mock_model_instance.generate_content.assert_called_once_with("What is photosynthesis?")
        
        # And check if configure was called with the correct fake key
        mock_configure.assert_called_once_with(api_key="fake_test_key")

    @patch('llm_module.client.genai.configure')
    @patch('llm_module.client.genai.GenerativeModel')
    @patch.dict(os.environ, {"GEMINI_API_KEY": "fake_test_key", "GEMINI_MODEL": "test-model"})
    def test_generate_json_success(self, mock_generative_model, mock_configure):
        mock_model_instance = MagicMock()
        mock_response = MagicMock()
        mock_response.text = '{"question_text": "Sample", "options": ["A", "B", "C", "D"]}'
        mock_model_instance.generate_content.return_value = mock_response
        mock_generative_model.return_value = mock_model_instance

        client = GeminiClient()
        result = client.generate_json("Generate question JSON")

        self.assertEqual(result, '{"question_text": "Sample", "options": ["A", "B", "C", "D"]}')
        mock_model_instance.generate_content.assert_called_once()

    @patch.dict(os.environ, {"GEMINI_API_KEY": ""}, clear=True)
    def test_offline_mode_without_api_key(self):
        client = GeminiClient(api_key="")
        self.assertTrue(client.is_offline)
        response = client.ask_question("Explain Photosynthesis")
        self.assertIn("Photosynthesis", response)
        self.assertIn("glucose", response.lower())

        json_response = client.generate_json("Generate MCQ for History")
        self.assertIn("question_text", json_response)
        self.assertIn("options", json_response)

if __name__ == '__main__':
    unittest.main()
