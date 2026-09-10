import unittest
from unittest.mock import patch
from src.hunterio_client import HunterIOClient

class TestHunterIOClient(unittest.TestCase):

    @patch('src.hunterio_client.requests.get')
    def test_generate_email_success(self, mock_get):
        # Arrange
        client = HunterIOClient(api_key='test_api_key')
        mock_response = {
            'data': {
                'email': 'test@example.com',
                'status': 'success'
            }
        }
        mock_get.return_value.json.return_value = mock_response
        mock_get.return_value.status_code = 200

        # Act
        email = client.generate_email('John Doe', 'example.com')

        # Assert
        self.assertEqual(email, 'test@example.com')
        mock_get.assert_called_once_with(
            'https://api.hunter.io/v2/email-finder',
            params={'full_name': 'John Doe', 'domain': 'example.com', 'api_key': 'test_api_key'}
        )

    @patch('src.hunterio_client.requests.get')
    def test_generate_email_failure(self, mock_get):
        # Arrange
        client = HunterIOClient(api_key='test_api_key')
        mock_get.return_value.status_code = 404

        # Act
        email = client.generate_email('John Doe', 'example.com')

        # Assert
        self.assertIsNone(email)
        mock_get.assert_called_once_with(
            'https://api.hunter.io/v2/email-finder',
            params={'full_name': 'John Doe', 'domain': 'example.com', 'api_key': 'test_api_key'}
        )

if __name__ == '__main__':
    unittest.main()