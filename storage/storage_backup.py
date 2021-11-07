import os
from datetime import date

import pandas as pd

from storage import CloudManager

if __name__ == "__main__":
    cloud_manager = CloudManager()
    start_date = date(2021, 8, 1)
    end_date = date.today()
    date_range = pd.date_range(start_date, end_date).strftime(
        '%Y_%m_%d').tolist()

    for i in date_range:
        filename = 'ordered_ranks_' + i + '.csv'
        if cloud_manager.download_from_cloud(filename):
            os.replace(filename, 'backup\\' + filename)
            print(filename + ' downloaded')
            cloud_manager.delete_from_cloud(filename)
