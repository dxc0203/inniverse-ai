
import sys
import os
import unittest
from unittest.mock import patch, MagicMock
from PIL import Image
import io

# Add the src directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from src.app.main import generate_image_from_text, generate_image_from_image_and_text

class TestMain(unittest.TestCase):

    @patch('google.genai.GenerativeModel')
    def test_generate_image_from_text_mock(self, mock_generative_model):
        # Arrange
        mock_model_instance = MagicMock()
        mock_generative_model.return_value = mock_model_instance

        # Create a mock response object that mimics the actual structure
        mock_response = MagicMock()
        mock_part = MagicMock()
        mock_inline_data = MagicMock()
        mock_inline_data.data = b'test_image_data'
        mock_part.inline_data = mock_inline_data
        mock_response.parts = [mock_part]
        mock_model_instance.generate_content.return_value = mock_response
        
        prompt = "a cat"
        is_test = False

        # Act
        image_data_list = generate_image_from_text(prompt, is_test)

        # Assert
        self.assertIsNotNone(image_data_list)
        self.assertEqual(len(image_data_list), 1)
        self.assertEqual(image_data_list[0], b'test_image_data')
        mock_model_instance.generate_content.assert_called_once_with(prompt)

    @patch('google.genai.GenerativeModel')
    def test_generate_image_from_image_and_text_mock(self, mock_generative_model):
        # Arrange
        mock_model_instance = MagicMock()
        mock_generative_model.return_value = mock_model_instance
        
        mock_response = MagicMock()
        mock_part = MagicMock()
        mock_inline_data = MagicMock()
        mock_inline_data.data = b'test_image_data_2'
        mock_part.inline_data = mock_inline_data
        mock_response.parts = [mock_part]
        mock_model_instance.generate_content.return_value = mock_response

        prompt = "a dog"
        # Create a dummy image
        image = Image.new('RGB', (100, 100), color = 'red')
        
        is_test = False

        # Act
        image_data_list = generate_image_from_image_and_text(image, prompt, is_test)

        # Assert
        self.assertIsNotNone(image_data_list)
        self.assertEqual(len(image_data_list), 1)
        self.assertEqual(image_data_list[0], b'test_image_data_2')
        mock_model_instance.generate_content.assert_called_once_with([prompt, image])


    def test_generate_image_from_text_test_mode(self):
        # Arrange
        prompt = "a cat"
        is_test = True

        # Act
        image_paths = generate_image_from_text(prompt, is_test)

        # Assert
        self.assertIsNotNone(image_paths)
        self.assertEqual(len(image_paths), 1)
        self.assertTrue(os.path.exists(image_paths[0]))

    def test_generate_image_from_image_and_text_test_mode(self):
        # Arrange
        prompt = "a dog"
        image = Image.new('RGB', (100, 100), color = 'red')
        is_test = True

        # Act
        image_paths = generate_image_from_image_and_text(image, prompt, is_test)

        # Assert
        self.assertIsNotNone(image_paths)
        self.assertEqual(len(image_paths), 1)
        self.assertTrue(os.path.exists(image_paths[0]))


if __name__ == '__main__':
    unittest.main()
