# Менеджер управления базой данных. В базе хранятся данные о подписчиках

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import settings
from storage.models import Base, User, ShareInfo


class DatabaseManager:
    def __init__(self, engine=None):
        if engine is None:
            engine = create_engine(settings.DATABASE_URL)
        self.engine = engine
        self.session = sessionmaker(bind=self.engine)()
        self.metadata = Base.metadata

    def create_all(self):
        self.metadata.create_all(self.engine)

    def drop_all(self):
        self.metadata.drop_all(self.engine)

    def insert_subscriber(self, subscriber_id, subscriber_name, chat_id,
                          is_subscribe_recommends=True):
        try:
            new_user = User(subscriber_id, subscriber_name, chat_id,
                            is_subscribe_recommends)
            self.session.add(new_user)
            self.session.commit()
        except:
            print(f'Подписчик {subscriber_id} уже есть в таблице')
            self.session.rollback()
            return False
        return True

    def delete_subscriber(self, subscriber_id):
        try:
            user = self.session.query(User).filter(
                User.user_id == subscriber_id).first()
            self.session.delete(user)
            self.session.commit()
        except:
            print(f'Подписчика {subscriber_id} нет в таблице')
            self.session.rollback()

    def subscribe_to_recommendations(self, subscriber_id):
        try:
            user = self.session.query(User).filter(
                User.user_id == subscriber_id).first()
            user.recommendations = True
            self.session.commit()
        except:
            print(f'Подписчика {subscriber_id} нет в таблице')
            self.session.rollback()

    def unsubscribe_from_recommendations(self, subscriber_id):
        try:
            user = self.session.query(User).filter(
                User.user_id == subscriber_id).first()
            user.recommendations = False
            self.session.commit()
        except:
            print(f'Подписчика {subscriber_id} нет в таблице')
            self.session.rollback()

    def get_subscribers(self):
        users = [user.__dict__ for user in self.session.query(User).all()]
        for user in users:
            user.pop('_sa_instance_state')
        return users

    def get_subscriber_by_id(self, subscriber_id):
        try:
            user = self.session.query(User).filter(
                User.user_id == subscriber_id).first().__dict__
            user.pop('_sa_instance_state')
            return user
        except:
            print(f'Подписчика {subscriber_id} нет в таблице')
            return None

    def get_share_info(self, ticker):
        try:
            share_info = self.session.query(ShareInfo).filter(
                ShareInfo.ticker == ticker).first().__dict__
            share_info.pop('_sa_instance_state')
            return share_info
        except:
            print(f'Тикера {ticker} нет в таблице')
            return None

    def insert_update_share_info(self, ticker, pe, roe, price, yahoo_rating,
                                 low_target, avg_target, high_target):
        try:
            share_info = self.session.query(ShareInfo).filter(
                ShareInfo.ticker == ticker).first()
            share_info.pe = pe
            share_info.roe = roe
            share_info.price = price
            share_info.yahoo_rating = yahoo_rating
            share_info.low_target = low_target
            share_info.low_target = avg_target
            share_info.low_target = high_target
        # тикера ещё нет в таблице
        except:
            self.session.rollback()
            share_info = ShareInfo(ticker, pe, roe, yahoo_rating, price,
                                   low_target, avg_target, high_target)
            self.session.add(share_info)
        self.session.commit()
