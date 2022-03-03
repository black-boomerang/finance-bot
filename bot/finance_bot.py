# Основной класс бота, запускаемого в bot_worker.py
import calendar
import copy
import os
from datetime import date

import pandas as pd
import telebot
from telebot.types import InlineKeyboardButton

from analyzer import Analyzer
from drawler import Drawler
from schedule_thread import ScheduleThread
from settings import MONTH_NAMES
from storage import DatabaseManager


class FinanceBot(telebot.TeleBot):
    def __init__(self, token):
        super().__init__(token)
        self.database_manager = DatabaseManager()
        self.analyzer = Analyzer()
        self.portfolio = self.analyzer.portfolio

        # кнопки умной клавиатуры
        self._buttons_info = {
            'subscribe_recommends': 'Подписаться на инвестиционные рекомендации',
            'unsubscribe_recommends': 'Отписаться от инвестиционных рекомендаций',
            'help': 'Помощь',
            'get_share_info': 'Информация об акции',
            'get_previous_version': 'Посмотреть предыдущий рейтинг'
        }
        self.callbacks = self._buttons_info.keys()
        self.keyboard_buttons = dict()
        for callback, text in self._buttons_info.items():
            self.keyboard_buttons[callback] = InlineKeyboardButton(text,
                                                                   callback_data=callback)

        # отдельный поток, отвечающий за отправку изменения рекомендаций и
        # ежемесячной прибыльности портфеля
        self.reg_thread = ScheduleThread()
        self.reg_thread.add_job(self.update_recommendations, 'cron',
                                day_of_week='mon-fri', hour=21, minute=0)
        self.reg_thread.add_job(self.send_profitability, 'cron',
                                day='1', hour=18, minute=0)
        self.reg_thread.start()

    @staticmethod
    def _get_recommendations_table(companies, prev_companies):
        """
        Формирование картинки с рекомендованными акциями
        """
        companies_df = companies.reset_index()[
            ['index', 'Rating', 'Current Price', 'Average Target']]
        prev_companies_df = prev_companies.reset_index()[
            ['index', 'Rating', 'Current Price', 'Average Target']]

        # вычисляем добавленные и удалённые из рейтинга акции
        concat_df = pd.concat(
            [companies_df['index'], prev_companies_df['index']])
        indices = (concat_df.drop_duplicates(keep=False).index + 1).tolist()
        added = indices[:len(indices) // 2]
        deleted = indices[len(indices) // 2:]

        companies_df.columns = ['Тикер', 'Рейтинг', 'Цена', 'Цель']
        colors_dict = {'#00083e': (0,),
                       '#d9d9d9': (1, 3, 5),
                       '#ffffff': (2, 4),
                       '#d4f870': tuple(added),
                       '#ff9273': ()
                       }

        image = Drawler.draw_table(table=companies_df, colors_dict=colors_dict,
                                   width=1000, height=400)
        image.save('companies_table.png')

    def update_recommendations(self):
        """
        Запуск анализатора и отправка рекомендаций подписчикам,
        если рекомендации изменились
        """
        prev_best = copy.copy(self.analyzer.best_companies)
        cur_best = self.analyzer.get_best_companies()
        if set(prev_best.index) != set(cur_best.index):
            self.send_recommendations(cur_best, prev_best)

    def send_profitability(self):
        """
        Отправка подписчикам прибыльности портфеля за прошедший месяц
        """
        today = date.today()
        prev_prev_month = (today.month + 9) % 12 + 1  # индексация с единицы
        prev_prev_year = today.year - (today.month <= 2)
        last_day = calendar.monthrange(prev_prev_year, prev_prev_month)[1]
        prev_date = date(prev_prev_year, prev_prev_month, last_day)

        profit = self.portfolio.get_total_profitability()
        month_profit = self.portfolio.get_range_profitability(first=prev_date)

        month_name = MONTH_NAMES[(today.month + 10) % 12]  # индексация с нуля
        text = '`Прибыльность за всё время:` {:.2f}%\n' \
               '`Прибыльность за {}:` {:.2f}%'.format(profit * 100, month_name,
                                                      month_profit * 100)
        subscribers = self.database_manager.get_subscribers()
        for subscriber in subscribers:
            if subscriber['recommendations']:
                self.send_message(subscriber['chat_id'], text, (),
                                  parse_mode='Markdown')

    def send_recommendations(self, best_companies, prev_best_companies):
        """
        Добавление умной клавиатуры к сообщению и вызов метода базового класса.
        Используется для отправки рекомендаций
        """
        self._get_recommendations_table(best_companies, prev_best_companies)
        text = 'Список самых недооценённых акций на ' \
               'Санкт-Петербуржской бирже на сегодняшний ' \
               'день'
        text = 'Произошли изменения в рейтинге акций'
        subscribers = self.database_manager.get_subscribers()
        for subscriber in subscribers:
            if subscriber['recommendations']:
                try:
                    with open('companies_table.png', 'rb') as sent_img:
                        self.send_photo(subscriber['chat_id'], sent_img, text)
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

    def send_photo(self, chat_id, sent_img, text, buttons=(), **kwargs):
        """
        Добавление умной клавиатуры к сообщению с картинкой и вызов метода
        базового класса
        """
        keyboard = telebot.types.InlineKeyboardMarkup()
        for button_name in buttons:
            keyboard.row(self.keyboard_buttons[button_name])
        return super().send_photo(chat_id, sent_img, text,
                                  reply_markup=keyboard, **kwargs)
