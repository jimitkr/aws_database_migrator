import os

import boto3

from PropertyLoader import PropertyLoader


class AWSClients:

    def __init__(self):
        self.aws_access_key_id = None
        self.aws_secret_access_key = None
        # get config properties
        self.config_properties = PropertyLoader()
        self.verify_aws_access_keys()

    def verify_aws_access_keys(self):

        # reminder - why os.getenv and not os.environ? os.environ throws exception if variable is undefined,
        # but not if variable is just empty. This is a problem
        self.aws_access_key_id = os.getenv('AWS_ACCESS_KEY_ID')
        if self.aws_access_key_id is None:
            self.config_properties.logger.exception(
                'Environment variable AWS_ACCESS_KEY_ID is undefined. Please define your AWS user\'s '
                'AWS_ACCESS_KEY_ID in the environment variables for the operating system user running this program. Note - operating system user is a separate entity from your AWS user')
            exit(1)

        self.aws_secret_access_key = os.getenv('AWS_SECRET_ACCESS_KEY')
        if self.aws_secret_access_key is None:
            self.config_properties.logger.exception(
                'Environment variable AWS_SECRET_ACCESS_KEY is undefined. Please define your AWS user\'s AWS_SECRET_ACCESS_KEY in the environment variables for the operating system user running this program. Note - operating system user is a separate entity from your AWS user')
            exit(1)

    def get_dms_handle(self):
        return boto3.client('dms', aws_access_key_id=self.aws_access_key_id, aws_secret_access_key=self.aws_secret_access_key, region_name=self.config_properties.aws_region)

    def get_ec2_handle(self):
        return boto3.client('ec2', aws_access_key_id=self.aws_access_key_id, aws_secret_access_key=self.aws_secret_access_key, region_name=self.config_properties.aws_region)

    def get_rds_handle(self):
        return boto3.client('rds', aws_access_key_id=self.aws_access_key_id, aws_secret_access_key=self.aws_secret_access_key, region_name=self.config_properties.aws_region)


'''
    def get_iam_handle(self):
        """ Returns handle to Identitiy And Access Management (IAM) """
        return boto.connect_iam(self.aws_access_key_id, self.aws_secret_access_key)
'''
