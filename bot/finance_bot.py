import telebot

from analyzer import finance_analyzer
from bot.database_manager import DatabaseManager
from bot.schedule_thread import ScheduleThread


class FinanceBot(telebot.TeleBot):
    def __init__(self, token):
        super().__init__(token)
        self.database_manager = DatabaseManager()

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
                                     day_of_week='mon-fri', hour=13)
        self.thread.start()

    def send_recommendations(self):
        companies_number = 30
        best_companies = finance_analyzer.get_best_companies(companies_number)
        recommendations_text = 'Список самых недооценённых акций на ' \
                               'Санкт-Петербуржской бирже на сегодняшний ' \
                               'день:\n' + \
                               '\n'.join(
                                   ['. '.join([str(index), company]) + ';' for
                                    index, company in
                                    zip(list(range(1, companies_number + 1)),
                                        best_companies)])
        subscribers = self.database_manager.get_subscribers()
        for subscriber in subscribers:
            self.send_message(subscriber['chat_id'],
                              '<b>Ваши рекомендации:</b>\n\n' + recommendations_text,
                              parse_mode='HTML')

    def send_message(self, chat_id, text, buttons=(), **kwargs):
        keyboard = telebot.types.InlineKeyboardMarkup()
        for button_name in buttons:
            keyboard.row(self.keyboard_buttons[button_name])
        super().send_message(chat_id, text, reply_markup=keyboard, **kwargs)
