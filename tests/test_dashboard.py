import unittest
from app.dashboard.views import find_host_for_osd
from app.dashboard.views import get_unhealthy_osd_details


CEPH_OSD_TREE = {
    'nodes': [
        {
            'type': 'host',
            'name': 'testhost01',
            'children': [
                1,
                2,
                3
            ]
        },
        {
            'type': 'osd',
            'name': 'osd.1',
            'id': 1,
            'exists': 1,
            'status': 'down',
            'reweight': 1.0
        },
        {
            'type': 'osd',
            'name': 'osd.2',
            'id': 2,
            'exists': 1,
            'status': 'up',
            'reweight': 0.0
        },
        {
            'type': 'osd',
            'name': 'osd.3',
            'id': 3,
            'exists': 1,
            'status': 'up',
            'reweight': 1.0
        },
        {
            'type': 'osd',
            'name': 'osd.4',
            'id': 4,
            'exists': 0,
            'status': 'up',
            'reweight': 1.0
        }
    ]
}


class TestScraper(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_find_host(self):
        result = find_host_for_osd(0, CEPH_OSD_TREE)
        self.assertEqual(result, 'unknown')
        result = find_host_for_osd(1, CEPH_OSD_TREE)
        self.assertEqual(result, 'testhost01')

    def test_unhealthy_osd(self):
        result = get_unhealthy_osd_details(CEPH_OSD_TREE)
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 2)

    def test_unhealthy_osd_detail(self):
        result = get_unhealthy_osd_details(CEPH_OSD_TREE)
        for item in result:
            if item['name'] == 'osd.1':
                self.assertEqual(item['status'], 'down')
            if item['name'] == 'osd.2':
                self.assertEqual(item['status'], 'out')

if __name__ == '__main__':
    unittest.main()
