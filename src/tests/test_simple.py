
import unittest
try:
    import google.genai as genai
except (ImportError, AttributeError):
    genai = None

class TestSimple(unittest.TestCase):
    def test_import(self):
        if genai:
            print(dir(genai))
        self.assertTrue(genai is not None and hasattr(genai, 'GenerativeModel'))

if __name__ == '__main__':
    unittest.main()
