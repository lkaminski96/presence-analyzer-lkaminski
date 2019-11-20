# -*- coding: utf-8 -*-
"""
Presence analyzer unit tests.
"""

import datetime
import json
import os.path
import unittest

from mock import patch

from presence_analyzer import main, utils, views

TEST_DATA_CSV = os.path.join(
    os.path.dirname(__file__), '..', '..', 'runtime', 'data', 'test_data.csv'
)
TEST_BROKEN_DATA_CSV = os.path.join(
    os.path.dirname(__file__),
    '..',
    '..',
    'runtime',
    'data',
    'test_broken_data.csv'
)


# pylint: disable=maybe-no-member, too-many-public-methods
class PresenceAnalyzerViewsTestCase(unittest.TestCase):
    """
    Views tests.
    """

    def setUp(self):
        """
        Before each test, set up a environment.
        """
        main.app.config.update({'DATA_CSV': TEST_DATA_CSV})
        self.client = main.app.test_client()

    def tearDown(self):
        """
        Get rid of unused objects after each test.
        """
        pass

    def test_mainpage(self):
        """
        Test main page redirect.
        """
        resp = self.client.get('/')
        self.assertEqual(resp.status_code, 302)
        assert resp.headers['Location'].endswith('/presence_weekday.html')

    def test_api_users(self):
        """
        Test users listing.
        """
        resp = self.client.get('/api/v1/users')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.content_type, 'application/json')
        data = json.loads(resp.data)
        self.assertEqual(len(data), 2)
        self.assertDictEqual(data[0], {u'user_id': 10, u'name': u'User 10'})

    @patch.dict(
        'presence_analyzer.main.app.config',
        {'DATA_CSV': TEST_BROKEN_DATA_CSV}
    )
    @patch('presence_analyzer.views.log')
    def test_mean_time_weekday_view(self, mock_log):
        """
        Test mean time weekday view.
        """
        resp = self.client.get('/api/v1/mean_time_weekday/13')
        self.assertEqual(resp.status_code, 404)
        self.assertTrue(mock_log.debug.called)

        resp = self.client.get('/api/v1/mean_time_weekday/10')
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.data)
        self.assertEqual(len(data), 7)
        self.assertListEqual(
            data,
            [
                [u'Mon', 0],
                [u'Tue', 30047.0],
                [u'Wed', 24465.0],
                [u'Thu', 23705.0],
                [u'Fri', 0],
                [u'Sat', 0],
                [u'Sun', 0]
            ]
        )

    @patch.dict(
        'presence_analyzer.main.app.config',
        {'DATA_CSV': TEST_BROKEN_DATA_CSV}
    )
    @patch('presence_analyzer.views.log')
    def test_presence_weekday_view(self, mock_log):
        """
        Test presence weekday view.
        """
        resp = self.client.get('/api/v1/presence_weekday/13')
        self.assertEqual(resp.status_code, 404)
        self.assertTrue(mock_log.debug.called)

        resp = self.client.get('/api/v1/presence_weekday/10')
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.data)
        self.assertEqual(len(data), 8)
        self.assertListEqual(
            data,
            [
                [u'Weekday', u'Presence (s)'],
                [u'Mon', 0],
                [u'Tue', 30047.0],
                [u'Wed', 24465.0],
                [u'Thu', 23705.0],
                [u'Fri', 0],
                [u'Sat', 0],
                [u'Sun', 0]
            ]
        )


class PresenceAnalyzerUtilsTestCase(unittest.TestCase):
    """
    Utility functions tests.
    """

    def setUp(self):
        """
        Before each test, set up a environment.
        """
        main.app.config.update({'DATA_CSV': TEST_DATA_CSV})

    def tearDown(self):
        """
        Get rid of unused objects after each test.
        """
        pass

    @patch.dict(
        'presence_analyzer.main.app.config',
        {'DATA_CSV': TEST_BROKEN_DATA_CSV}
    )
    @patch('presence_analyzer.utils.log')
    def test_get_data(self, mock_log):
        """
        Test parsing of CSV file.
        """
        data = utils.get_data()
        self.assertIsInstance(data, dict)
        self.assertItemsEqual(data.keys(), [10, 11])
        self.assertNotIn([12], data.keys())
        sample_date = datetime.date(2013, 9, 10)
        self.assertIn(sample_date, data[10])
        self.assertItemsEqual(data[10][sample_date].keys(), ['start', 'end'])
        self.assertEqual(
            data[10][sample_date]['start'],
            datetime.time(9, 39, 5),
        )
        self.assertTrue(mock_log.debug.called)

    def test_group_by_weekday(self):
        """
        Test presence of the user/s grouped by weekday.
        """
        data = utils.get_data()
        self.assertListEqual(
            utils.group_by_weekday(data[10]),
            [[], [30047], [24465], [23705], [], [], []]
        )

    def test_seconds_since_midnight(self):
        """
        Test calculating seconds of provided time.
        """
        self.assertEqual(
            utils.seconds_since_midnight(
                datetime.time(hour=0, minute=0, second=0)
            ),
            0
        )
        self.assertEqual(
            utils.seconds_since_midnight(
                datetime.time(hour=23, minute=59, second=59)
            ),
            86399
        )
        self.assertEqual(
            utils.seconds_since_midnight(
                datetime.time(hour=1, minute=30, second=30)
            ),
            5430
        )

    def test_interval(self):
        """
        Test interval between two provided times.
        """
        sample_start_time = datetime.time(hour=8, minute=30, second=0)
        self.assertEqual(
            utils.interval(
                sample_start_time,
                datetime.time(hour=8, minute=30, second=0)
            ),
            0
        )
        self.assertEqual(
            utils.interval(
                sample_start_time,
                datetime.time(hour=16, minute=25, second=15)
            ),
            28515
        )

    def test_mean(self):
        """
        Test function for calculating  arithmetic mean.
        """
        self.assertEqual(utils.mean([]), 0)
        self.assertEqual(utils.mean([4.28, -3.20, -1.08]), 0.0)
        self.assertEqual(utils.mean([-0.3, 1, 0, 2.1]), 0.7)
        self.assertEqual(utils.mean([-1, -2, -3]), -2.0)


def suite():
    """
    Default test suite.
    """
    base_suite = unittest.TestSuite()
    base_suite.addTest(unittest.makeSuite(PresenceAnalyzerViewsTestCase))
    base_suite.addTest(unittest.makeSuite(PresenceAnalyzerUtilsTestCase))

    return base_suite


if __name__ == '__main__':
    unittest.main()
