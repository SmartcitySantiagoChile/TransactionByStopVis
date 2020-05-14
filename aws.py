import boto3
from botocore.exceptions import ClientError
from decouple import config


class AWSSession:
    """
    Class to interact wit Amazon Web Service (AWS) API through boto3 library
    """
    EARLY_TRANSACTION_BUCKET_NAME = config('EARLY_TRANSACTION_BUCKET_NAME')

    def __init__(self):

        self.session = boto3.Session(
            aws_access_key_id=config('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=config('AWS_SECRET_ACCESS_KEY'))

    def get_available_days(self, bucket_name):
        s3 = self.session.resource('s3')
        bucket = s3.Bucket(bucket_name)

        days = []
        for obj in bucket.objects.all():
            date = obj.key.split('.')[0]
            days.append(date)

        return days

    def check_bucket_exists(self, bucket_name):
        s3 = self.session.resource('s3')
        try:
            s3.meta.client.head_bucket(Bucket=bucket_name)
            return True
        except ClientError as e:
            # If a client error is thrown, then check that it was a 404 error.
            # If it was a 404 error, then the bucket does not exist.
            error_code = int(e.response['Error']['Code'])
            if error_code == 403:
                raise ValueError("Private Bucket. Forbidden Access!")
            elif error_code == 404:
                return False

    def check_file_exists(self, bucket_name, key):
        s3 = self.session.resource('s3')
        try:
            s3.Object(bucket_name, key).load()
        except ClientError as e:
            if e.response['Error']['Code'] == "404":
                # The object does not exist.
                return False
            else:
                # Something else has gone wrong.
                raise ValueError(e.response['Error'])
        else:
            # The object exists.
            return True

    def download_object_from_bucket(self, obj_key, bucket_name, file_path):
        s3 = self.session.resource('s3')
        bucket = s3.Bucket(bucket_name)
        bucket.download_file(obj_key, file_path)
