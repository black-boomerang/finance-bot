# Этот файл определяет точку входа в приложение. В нём происходит запуск бота

import settings
from bot.finance_bot import FinanceBot

if __name__ == '__main__':
    bot = FinanceBot(settings.TELEGRAM_API_TOKEN)


    @bot.message_handler(commands=['start'])
    def start_message(message):
        is_added = bot.database_manager.insert_subscriber(
            message.chat.id,
            message.chat.first_name,
            message.chat.id, True)
        if not is_added:
            bot.database_manager.subscribe_to_recommendations(
                message.chat.id)
        bot.send_message(message.chat.id,
                         'Привет, ты подписался на мои инвестиционные рекомендации. '
                         'Чтобы посмотреть, что я умею, набери /help',
                         ('get_share_info', 'unsubscribe_recommends', 'help'))


    @bot.message_handler(commands=['help'])
    def help_command(message):
        bot.send_message(
            message.chat.id,
            '<b>Список доступных команд:</b>\n\n'
            '/share_info - запросить информацию об определённой акции;\n'
            '/subscribe - подписаться на рекомендации;\n'
            '/unsubscribe - отписаться от рекомендаций;\n'
            '/help - посмотреть доступные команды.\n',
            ('get_share_info', 'unsubscribe_recommends', 'help'),
            parse_mode='HTML')


    @bot.message_handler(commands=['subscribe'])
    def subscribe_command(message):
        bot.database_manager.subscribe_to_recommendations(
            message.chat.id)
        bot.send_message(
            message.chat.id,
            'Ты подписался на инвестиционные рекомендации',
            ('get_share_info', 'unsubscribe_recommends', 'help')
        )


    @bot.message_handler(commands=['unsubscribe'])
    def unsubscribe_command(message):
        bot.database_manager.unsubscribe_from_recommendations(
            message.chat.id)
        bot.send_message(
            message.chat.id,
            'Ты отписался от инвестиционных рекомендаций',
            ('get_share_info', 'subscribe_recommends', 'help')
        )


    @bot.message_handler(commands=['share_info'])
    def share_info_command(message):
        message = bot.send_message(
            message.chat.id,
            'Напиши тикер акции',
            ()
        )
        bot.register_next_step_handler(message, get_share_info)


    def get_share_info(message):
        ticker = message.text.strip().upper()
        share_info = bot.database_manager.get_share_info(ticker)

        if share_info is None:
            answer_text = 'Тикер не найден. Я поддерживаю только акции, ' \
                          'торгующиеся на Санкт-Петербуржской бирже'
        else:
            ordered_info = (
                share_info['ticker'], share_info['price'], share_info['ep'],
                share_info['roe'], share_info['low_target'],
                share_info['avg_target'], share_info['high_target'],
                share_info['yahoo_rating'])
            answer_text = '`Тикер:` {}\n`Цена:` {}\n' \
                          '`P/E:` {:.2f}%\n`ROE:` {:.2f}%\n' \
                          '`Средний прогноз:` {}\n`Минимальный прогноз:` {}\n' \
                          '`Максимальный прогноз:` {}\n `Рейтинг YAHOO`: {}' \
                          ''.format(*ordered_info)

        # subscribe_recommends/unsubscribe_recommends в зависимости от пользователя
        user = bot.database_manager.get_subscriber_by_id(message.chat.id)
        if user['recommendations']:
            recommendations_key = 'unsubscribe_recommends'
        else:
            recommendations_key = 'subscribe_recommends'
        bot.send_message(
            message.chat.id,
            answer_text,
            ('get_share_info', recommendations_key, 'help'),
            parse_mode='Markdown'
        )


    @bot.callback_query_handler(func=lambda call: True)
    def query_handler(query):
        callback_data = query.data
        if callback_data == 'help':
            help_command(query.message)
        elif callback_data == 'subscribe_recommends':
            subscribe_command(query.message)
        elif callback_data == 'unsubscribe_recommends':
            unsubscribe_command(query.message)
        elif callback_data == 'get_share_info':
            share_info_command(query.message)
        bot.answer_callback_query(query.id)


    bot.polling(none_stop=True)
