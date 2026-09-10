import unittest
from src.anymailfinder_client import AnyMailFinderClient

class TestAnyMailFinderClient(unittest.TestCase):

    def setUp(self):
        self.client = AnyMailFinderClient(api_key='test_api_key')

    def test_find_additional_emails_success(self):
        names = ['John Doe']
        domain = 'example.com'
        response = self.client.find_additional_emails(names, domain)
        self.assertIsInstance(response, list)
        self.assertGreater(len(response), 0)

    def test_find_additional_emails_no_names(self):
        names = []
        domain = 'example.com'
        response = self.client.find_additional_emails(names, domain)
        self.assertEqual(response, [])

    def test_find_additional_emails_invalid_domain(self):
        names = ['John Doe']
        domain = 'invalid_domain'
        response = self.client.find_additional_emails(names, domain)
        self.assertEqual(response, [])

if __name__ == '__main__':
    unittest.main()