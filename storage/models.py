# Модели для базы данных

from sqlalchemy import Column, Integer, String, Boolean, Time, Float
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class User(Base):
    __tablename__ = 'users'

    user_id = Column(Integer, primary_key=True)
    user_name = Column(String, default='Уважаемый', nullable=False)
    chat_id = Column(Integer, nullable=False, unique=True)
    recommendations = Column(Boolean, default=True)
    recommendations_time = Column(Time(timezone=True),
                                  server_default='17:30:00')
    is_admin = Column(Boolean, default=False)

    def __init__(self, user_id, user_name, chat_id, recommendations):
        self.user_id = user_id
        self.user_name = user_name
        self.chat_id = chat_id
        self.recommendations = recommendations


class ShareInfo(Base):
    __tablename__ = 'shares_info'

    ticker = Column(String, primary_key=True)
    ep = Column(Float, default=0.0, nullable=False)
    roe = Column(Float, default=0.0, nullable=False)
    yahoo_rating = Column(Float, default=5.0, nullable=False)
    price = Column(Float, default=0.0, nullable=False)
    low_target = Column(Float, default=0.0, nullable=False)
    avg_target = Column(Float, default=0.0, nullable=False)
    high_target = Column(Float, default=0.0, nullable=False)
    company_name = Column(String, default='', nullable=False)

    def __init__(self, ticker, ep=0.0, roe=0.0, yahoo_rating=5.0, price=0.0,
                 low_target=0.0, avg_target=0.0, high_target=0.0,
                 company_name=''):
        self.ticker = ticker
        self.ep = ep
        self.roe = roe
        self.yahoo_rating = yahoo_rating
        self.price = price
        self.low_target = low_target
        self.avg_target = avg_target
        self.high_target = high_target
        self.company_name = company_name
