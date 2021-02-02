import json
import os

from assets.portfolio import Portfolio
from storage.cloud_manager import CloudManager


def load_from_json(filename):
    cloud_manager = CloudManager()
    if not cloud_manager.download_from_cloud(filename):
        return None
    with open(filename, 'rb') as json_file:
        loaded_portfolio = json.load(json_file)
    os.remove(filename)
    return loaded_portfolio
