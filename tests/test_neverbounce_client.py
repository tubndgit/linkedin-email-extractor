import unittest
from src.neverbounce_client import NeverBounceClient

class TestNeverBounceClient(unittest.TestCase):

    def setUp(self):
        self.client = NeverBounceClient(api_key='test_api_key')

    def test_verify_email_valid(self):
        email = 'test@example.com'
        response = self.client.verify_email(email)
        self.assertIn('result', response)
        self.assertEqual(response['result'], 'valid')

    def test_verify_email_invalid(self):
        email = 'invalid@example.com'
        response = self.client.verify_email(email)
        self.assertIn('result', response)
        self.assertEqual(response['result'], 'invalid')

    def test_verify_email_format(self):
        email = 'not-an-email'
        response = self.client.verify_email(email)
        self.assertIn('result', response)
        self.assertEqual(response['result'], 'invalid')

if __name__ == '__main__':
    unittest.main()