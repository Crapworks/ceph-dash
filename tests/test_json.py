import unittest
from app import app


class TestScraper(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True

    def tearDown(self):
        pass

    def test_config(self):
        config = app.config['USER_CONFIG']
        self.assertIsInstance(config, dict)
        self.assertTrue('ceph_config' in config)

if __name__ == '__main__':
    unittest.main()
