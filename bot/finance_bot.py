# Основной класс бота, запускаемого в bot_worker.py

import os

import plotly.figure_factory as ff
import telebot
from telebot.types import InlineKeyboardButton

from analyzer import Analyzer
from schedule_thread import ScheduleThread
from storage import DatabaseManager


class FinanceBot(telebot.TeleBot):
    def __init__(self, token):
        super().__init__(token)
        self.database_manager = DatabaseManager()
        self.analyzer = Analyzer()

        # кнопки умной клавиатуры
        self._buttons_info = {
            'subscribe_recommends': 'Подписаться на инвестиционные рекомендации',
            'unsubscribe_recommends': 'Отписаться от инвестиционных рекомендаций',
            'help': 'Помощь',
            'get_share_info': 'Информация об акции'
        }
        self.callbacks = self._buttons_info.keys()
        self.keyboard_buttons = dict()
        for callback, text in self._buttons_info.items():
            self.keyboard_buttons[callback] = InlineKeyboardButton(text,
                                                                   callback_data=callback)

        # отдельный поток, отвечающий за ежедневную отправку рекомендаций
        self.thread = ScheduleThread(self.update_recommendations, 'cron',
                                     day_of_week='mon-fri', hour=21,
                                     minute=0)
        self.thread.start()

    @staticmethod
    def _get_recommendations_table(companies):
        """
        Формирование картинки с рекомендованными акциями
        """
        companies_df = companies.reset_index()[
            ['index', 'Rating', 'Current Price', 'Average Target']]
        companies_df.columns = ['Тикер', 'Рейтинг', 'Цена', 'Цель']
        fig = ff.create_table(companies_df)
        fig.update_layout(
            autosize=False,
            width=500,
            height=200,
        )
        fig.write_image('companies_table.png', scale=2)

    def update_recommendations(self):
        """
        Запуск анализатора и отправка рекомендаций подписчикам,
        если рекомендации изменились
        """
        best_companies, is_changed = self.analyzer.get_best_companies(5)
        if is_changed:
            self.send_recommendations(best_companies)

    def send_recommendations(self, best_companies):
        """
        Добавление умной клавиатуры к сообщению и вызов метода базового класса.
        Используется для отправки рекомендаций
        """
        self._get_recommendations_table(best_companies)
        recommendations_text = '`Список самых недооценённых акций на ' \
                               'Санкт-Петербуржской бирже на сегодняшний ' \
                               'день`'
        subscribers = self.database_manager.get_subscribers()
        for subscriber in subscribers:
            if subscriber['recommendations']:
                try:
                    with open('companies_table.png', 'rb') as sent_img:
                        self.send_photo(subscriber['chat_id'], sent_img,
                                        recommendations_text)
                except telebot.apihelper.ApiException:
                    pass
        os.remove('companies_table.png')

    def send_message(self, chat_id, text, buttons=(), **kwargs):
        """
        Добавление умной клавиатуры к сообщению и вызов метода базового класса.
        Используется для отправки сообщений в bot_worker.py
        """
        keyboard = telebot.types.InlineKeyboardMarkup()
        for button_name in buttons:
            keyboard.row(self.keyboard_buttons[button_name])
        return super().send_message(chat_id, text, reply_markup=keyboard,
                                    **kwargs)
