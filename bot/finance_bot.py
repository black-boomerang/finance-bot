import telebot
from prettytable import PrettyTable

from analyzer import Analyzer
from bot.database_manager import DatabaseManager
from schedule_thread import ScheduleThread


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
                                     day_of_week='mon-fri', hour=16,
                                     minute=32)
        self.thread.start()

    @staticmethod
    def _get_recommendations_text(companies):
        recommendations_text = 'Список самых недооценённых акций на ' \
                               'Санкт-Петербуржской бирже на сегодняшний ' \
                               'день:\n'
        table = PrettyTable(['Тикер', 'Рейтинг', 'Цена', 'Цель'])
        for index in companies.index.to_list():
            values = companies.loc[index]
            table.add_row(
                [index, values.loc['Rating'], values.loc['Current Price'],
                 values.loc['Average Target']])
        return '`' + recommendations_text + table.get_string() + '`'

    def send_recommendations(self):
        companies_number = 30
        best_companies = self.analyzer.get_best_companies(companies_number)
        recommendations_text = self._get_recommendations_text(best_companies)
        subscribers = self.database_manager.get_subscribers()
        for subscriber in subscribers:
            if subscriber['recommendations']:
                try:
                    self.send_message(subscriber['chat_id'],
                                      recommendations_text,
                                      parse_mode='Markdown')
                except telebot.apihelper.ApiException:
                    pass

    def send_message(self, chat_id, text, buttons=(), **kwargs):
        keyboard = telebot.types.InlineKeyboardMarkup()
        for button_name in buttons:
            keyboard.row(self.keyboard_buttons[button_name])
        super().send_message(chat_id, text, reply_markup=keyboard, **kwargs)
