from sqlalchemy import Column, Integer, String, Boolean, Time
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

    def __init__(self, user_id, user_name, chat_id, recommendations):
        self.user_id = user_id
        self.user_name = user_name
        self.chat_id = chat_id
        self.recommendations = recommendations
