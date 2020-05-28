import os
from datetime import datetime
from unittest import TestCase

import mock

import process_data


class ProcessDataTest(TestCase):

    def setUp(self):
        dir_path = os.path.dirname(os.path.realpath(__file__))
        self.data_path = os.path.join(dir_path, 'files')

    @mock.patch('process_data.AWSSession')
    def test_check_available_days(self, aws_session):
        aws_session.get_available_dates.return_value = [datetime.strptime('2019-02-05', "%Y-%m-%d"),
                                                        datetime.strptime('2020-02-05', "%Y-%m-%d"),
                                                        datetime.strptime('2021-02-05', "%Y-%m-%d")]
        start_date = datetime.strptime('2020-01-01', "%Y-%m-%d")
        end_date = datetime.strptime('2020-12-31', "%Y-%m-%d")
        available_days = process_data.check_available_days(aws_session, start_date, end_date)
        self.assertEqual(datetime.strptime('2020-02-05', "%Y-%m-%d"), available_days[0])
