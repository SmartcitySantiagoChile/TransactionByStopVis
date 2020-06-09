from unittest import TestCase
import aws
import mock
import datetime
from botocore.exceptions import ClientError


class AwsTest(TestCase):

    @mock.patch('aws.boto3.Session')
    def setUp(self, boto3_session):
        boto3_session.return_value = mock.MagicMock(resource=mock.MagicMock())
        self.aws_session = aws.AWSSession()

    def test_get_available_days(self):
        date = mock.Mock(key='2020-05-08.transaction.gz')
        dates = mock.Mock(return_value=[date])
        bucket = mock.MagicMock(objects=mock.MagicMock(all=dates))
        bucket.Bucket.return_value = bucket
        self.aws_session.session.resource = mock.MagicMock(return_value=bucket)
        expected_date = [datetime.datetime(2020, 5, 8, 0, 0)]
        self.assertEqual(expected_date, self.aws_session.get_available_dates())

    def test_check_bucket_exists_true(self):
        bucket = mock.MagicMock(
            meta=mock.MagicMock(client=mock.MagicMock(head_bucket=mock.MagicMock(return_value=True))))
        self.aws_session.session.resource = mock.MagicMock(return_value=bucket)
        self.assertTrue(self.aws_session.check_bucket_exists())

    def test_check_bucket_exists_404_error(self):
        error = mock.MagicMock()
        error_response = {'Error': {'Code': '404'}}
        error.side_effect = ClientError(error_response=error_response, operation_name='mock error')
        bucket = mock.MagicMock(
            meta=mock.MagicMock(client=mock.MagicMock(head_bucket=error)))
        self.aws_session.session.resource = mock.MagicMock(return_value=bucket)
        self.assertFalse(self.aws_session.check_bucket_exists())

    def test_check_bucket_exists_403_error(self):
        error = mock.MagicMock()
        error_response = {'Error': {'Code': '403'}}
        error.side_effect = ClientError(error_response=error_response, operation_name='mock error')
        bucket = mock.MagicMock(
            meta=mock.MagicMock(client=mock.MagicMock(head_bucket=error)))
        self.aws_session.session.resource = mock.MagicMock(return_value=bucket)

        with self.assertRaises(ValueError):
            self.aws_session.check_bucket_exists()

    def test_check_file_exists(self):
        load = mock.MagicMock()
        load.load.return_value = '2020-05-08.transaction.gz'
        bucket = mock.MagicMock()
        bucket.Object.return_value = load
        self.aws_session.session.resource = mock.MagicMock(return_value=bucket)
        self.assertTrue(self.aws_session.check_file_exists('2020-05-08.transaction.gz'))


    def test_check_file_exists_404_error(self):
        error = mock.MagicMock()
        error_response = {'Error': {'Code': '404'}}
        error.load.side_effect = ClientError(error_response=error_response, operation_name='mock error')
        bucket = mock.MagicMock()
        bucket.Object.return_value = error
        self.aws_session.session.resource = mock.MagicMock(return_value=bucket)
        self.assertFalse(self.aws_session.check_file_exists('2020-05-08.transaction.gz'))

    def test_check_file_exists_403_error(self):
        error = mock.MagicMock()
        error_response = {'Error': {'Code': '403'}}
        error.load.side_effect = ClientError(error_response=error_response, operation_name='mock error')
        bucket = mock.MagicMock()
        bucket.Object.return_value = error
        self.aws_session.session.resource = mock.MagicMock(return_value=bucket)
        with self.assertRaises(ValueError):
            self.aws_session.check_file_exists('2020-05-08.transaction.gz')

    def test_download_object_from_bucket(self):
        bucket = mock.MagicMock(download_file=mock.MagicMock())
        bucket.Bucket.return_value = bucket
        self.aws_session.session.resource = mock.MagicMock(return_value=bucket)
        self.aws_session.download_object_from_bucket('2020-05-08.transaction.gz', '')
