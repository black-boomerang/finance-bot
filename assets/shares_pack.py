from datetime import date


class SharesPack:
    def __init__(self, number, open_price=0, close_price=0, open_date=None,
                 close_date=None):
        self.number = number
        self.open_price = open_price
        self.close_price = close_price
        self.open_date = date.today() if open_date is None else open_date
        self.close_date = date.max if close_date is None else close_date
