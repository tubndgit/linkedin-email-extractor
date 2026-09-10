import unittest
from src.linkedin_extractor import LinkedInExtractor

class TestLinkedInExtractor(unittest.TestCase):

    def setUp(self):
        self.extractor = LinkedInExtractor()

    def test_extract_names_and_domains(self):
        # Mock data for testing
        mock_data = [
            {"name": "John Doe", "domain": "example.com"},
            {"name": "Jane Smith", "domain": "sample.com"}
        ]
        
        # Assuming the method returns a list of dictionaries
        extracted_data = self.extractor.extract_names_and_domains(mock_data)
        
        self.assertEqual(len(extracted_data), 2)
        self.assertEqual(extracted_data[0]["name"], "John Doe")
        self.assertEqual(extracted_data[0]["domain"], "example.com")
        self.assertEqual(extracted_data[1]["name"], "Jane Smith")
        self.assertEqual(extracted_data[1]["domain"], "sample.com")

if __name__ == '__main__':
    unittest.main()