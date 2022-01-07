# Менеджер управления облаком. В облаке хранятся таблицы с прогнозами цен на акции

import boto3
import botocore

import settings
from storage.singleton import SingletonMeta


class CloudManager(metaclass=SingletonMeta):
    def __init__(self):
        self.s3_client = boto3.client('s3',
                                      aws_access_key_id=settings.CLOUDCUBE_ACCESS_KEY_ID,
                                      aws_secret_access_key=settings.CLOUDCUBE_SECRET_ACCESS_KEY)

    def upload_to_cloud(self, filename):
        self.s3_client.upload_file(filename, 'cloud-cube',
                                   settings.CLOUDCUBE_URL[
                                   -12:] + '/public/' + filename)

    def download_from_cloud(self, filename):
        try:
            self.s3_client.download_file('cloud-cube',
                                         settings.CLOUDCUBE_URL[
                                         -12:] + '/public/' + filename,
                                         filename)
        except botocore.exceptions.ClientError:
            return False
        return True

    def delete_from_cloud(self, filename):
        self.s3_client.delete_object(Bucket='cloud-cube',
                                     Key=settings.CLOUDCUBE_URL[
                                         -12:] + '/public/' + filename)
