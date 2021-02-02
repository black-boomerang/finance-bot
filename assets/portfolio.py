import json
import os
from datetime import date

from assets.shares_pack import SharesPack
from storage import CloudManager, DatabaseManager


class Portfolio:
    def __init__(self, initial_budget):
        self.active_shares = {}
        self.closed_shares = {}
        self.free_funds = initial_budget
        self.cloud_manager = CloudManager()
        self.database_manager = DatabaseManager()

    def buy(self, share_ticker, number, price, purchase_date=None):
        cost = number * price
        if cost > self.free_funds:
            print('Недостаточно средств для покупки')
            return False

        if purchase_date is None:
            purchase_date = date.today()

        pack = SharesPack(number, open_price=price, open_date=purchase_date)
        if share_ticker in self.active_shares.keys():
            self.active_shares[share_ticker].append(pack)
        else:
            self.active_shares[share_ticker] = (pack)
        self.free_funds -= cost
        return True

    def sell(self, share_ticker, number, price, sale_date):
        if share_ticker not in self.active_shares.keys():
            print("В портфеле нет таких акций")
            return False

        sell_shares = self.active_shares[share_ticker].sort(
            key=lambda pack: pack.open_date)
        shares_number = 0
        for shares_pack in sell_shares:
            shares_number += shares_pack.number

        if shares_number < number:
            print("В портфеле недостаточно акций. В нём {} акций {}".format(
                number, share_ticker))
            return False

        self.free_funds += number * price
        while number > 0:
            shares_pack = sell_shares[0]
            if shares_pack.number < number:
                shares_pack.close_date = sale_date
                shares_pack.close_price = price
                sell_shares.pop(0)
                self.closed_shares[share_ticker].append(shares_pack)
            else:
                closed_pack = shares_pack.copy()
                closed_pack.number = number
                closed_pack.close_date = sale_date
                closed_pack.close_price = price
                self.closed_shares[share_ticker].append(closed_pack)
                shares_pack.number -= number
            number -= shares_pack.number

        self.active_shares[share_ticker] = sell_shares
        return True

    def save_to_json(self, filename):
        with open(filename, 'wb') as json_file:
            json.dump(self, json_file)
        self.cloud_manager.upload_to_cloud(filename)
        os.remove(filename)

    def get_profitability(self):
        pass
