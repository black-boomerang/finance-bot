import os
from datetime import datetime, timedelta

import pandas as pd

from analyzer.cloud_manager import download_from_cloud


def get_best_companies(companies_number=30):
    recent_date = datetime.today()
    filename = 'ordered_rangs_' + recent_date.strftime(
        '%Y_%m_%d') + '.xlsx'
    while recent_date > datetime(2020, 7, 1) and not download_from_cloud(
            filename):
        recent_date -= timedelta(days=1)
        filename = 'ordered_rangs_' + recent_date.strftime(
            '%Y_%m_%d') + '.xlsx'

    companies = pd.read_excel(filename, index_col=0)
    best_companies = companies.head(companies_number).index.to_list()
    os.remove(filename)
    return best_companies
