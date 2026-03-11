import os
import sys
import unittest
from unittest.mock import patch, MagicMock
from PIL import Image

# Add the src directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../app')))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.main import process_images

class TestProcessImages(unittest.TestCase):

    def test_process_images_test_mode(self):
        # Arrange
        images = []
        prompt = "Test prompt"
        is_test = True

        # Act
        result = process_images(images, prompt, is_test)

        # Assert
        self.assertEqual(result, "This is a test response from the AI.")

    @patch('app.main.st')
    @patch('app.main.genai.GenerativeModel')
    @patch('app.main.genai.configure')
    def test_process_images_live_mode(self, mock_configure, mock_generative_model, mock_st):
        # Arrange
        mock_model = MagicMock()
        mock_response = MagicMock()
        mock_response.text = "Live response"
        mock_model.generate_content.return_value = mock_response
        mock_generative_model.return_value = mock_model
        mock_st.session_state.get.return_value = "test_api_key"

        images = [Image.new('RGB', (100, 100))]
        prompt = "Live prompt"
        is_test = False

        # Act
        result = process_images(images, prompt, is_test)

        # Assert
        self.assertEqual(result, "Live response")
        mock_configure.assert_called_with(api_key="test_api_key")
        mock_generative_model.assert_called_with('gemini-1.5-flash')
        mock_model.generate_content.assert_called_with([prompt] + images)

if __name__ == '__main__':
    unittest.main()
