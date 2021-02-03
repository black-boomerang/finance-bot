import os

import plotly.figure_factory as ff
import telebot

from analyzer import Analyzer
from schedule_thread import ScheduleThread
from storage import DatabaseManager


class FinanceBot(telebot.TeleBot):
    def __init__(self, token):
        super().__init__(token)
        self.database_manager = DatabaseManager()
        self.analyzer = Analyzer()

        self.keyboard_buttons = dict()
        self.keyboard_buttons[
            'subscribe_recommends'] = telebot.types.InlineKeyboardButton(
            'Подписаться на инвестиционные рекомендации',
            callback_data='subscribe_recommends')
        self.keyboard_buttons[
            'unsubscribe_recommends'] = telebot.types.InlineKeyboardButton(
            'Отписаться от инвестиционных рекомендаций',
            callback_data='unsubscribe_recommends')
        self.keyboard_buttons['help'] = telebot.types.InlineKeyboardButton(
            'Помощь',
            callback_data='help')

        self.thread = ScheduleThread(self.send_recommendations, 'cron',
                                     day_of_week='mon-fri', hour=20,
                                     minute=12)
        self.thread.start()

    @staticmethod
    def _get_recommendations_table(companies):
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

    def send_recommendations(self):
        companies_number = 5
        best_companies = self.analyzer.get_best_companies(companies_number)
        self._get_recommendations_table(best_companies)
        recommendations_text = '`Список самых недооценённых акций на ' \
                               'Санкт-Петербуржской бирже на сегодняшний ' \
                               'день:\n`'
        with open('companies_table.png', 'rb') as sent_img:
            subscribers = self.database_manager.get_subscribers()
            for subscriber in subscribers:
                if subscriber['recommendations']:
                    try:
                        self.send_photo(subscriber['chat_id'], sent_img,
                                        recommendations_text,
                                        parse_mode='Markdown')
                    except telebot.apihelper.ApiException:
                        pass
        #os.remove('companies_table.png')

    def send_message(self, chat_id, text, buttons=(), **kwargs):
        keyboard = telebot.types.InlineKeyboardMarkup()
        for button_name in buttons:
            keyboard.row(self.keyboard_buttons[button_name])
        super().send_message(chat_id, text, reply_markup=keyboard, **kwargs)
