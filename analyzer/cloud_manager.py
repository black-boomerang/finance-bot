import boto3
import botocore

import settings


def upload_to_cloud(filename):
    s3_client = boto3.client('s3',
                             aws_access_key_id=settings.CLOUDCUBE_ACCESS_KEY_ID,
                             aws_secret_access_key=settings.CLOUDCUBE_SECRET_ACCESS_KEY)

    s3_client.upload_file(filename, 'cloud-cube',
                          settings.CLOUDCUBE_URL[
                          -12:] + '/public/' + filename)


def download_from_cloud(filename):
    s3_client = boto3.client('s3',
                             aws_access_key_id=settings.CLOUDCUBE_ACCESS_KEY_ID,
                             aws_secret_access_key=settings.CLOUDCUBE_SECRET_ACCESS_KEY)

    try:
        s3_client.download_file('cloud-cube',
                                settings.CLOUDCUBE_URL[
                                -12:] + '/public/' + filename, filename)
    except botocore.exceptions.ClientError:
        return False
    return True
