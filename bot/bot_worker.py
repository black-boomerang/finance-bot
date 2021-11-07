# Этот файл определяет точку входа в приложение. В нём происходит запуск бота

import settings
from bot.finance_bot import FinanceBot

if __name__ == '__main__':
    bot = FinanceBot(settings.TELEGRAM_API_TOKEN)


    @bot.message_handler(commands=['start'])
    def start_message(message):
        is_added = bot.database_manager.insert_subscriber(
            message.from_user.id,
            message.from_user.first_name,
            message.chat.id, True)
        if not is_added:
            bot.database_manager.subscribe_to_recommendations(
                message.from_user.id)
        bot.send_message(message.chat.id,
                         'Привет, ты подписался на мои инвестиционные рекомендации. '
                         'Чтобы посмотреть, что я умею, набери /help',
                         ('unsubscribe_recommends', 'help'))


    @bot.message_handler(commands=['help'])
    def help_command(message):
        bot.send_message(
            message.chat.id,
            '<b>Список доступных команд:</b>\n\n'
            '/subscribe - подписаться на рекомендации;\n'
            '/unsubscribe - отписаться от рекомендаций;\n'
            '/help - посмотреть доступные команды.\n',
            ('unsubscribe_recommends', 'help'), parse_mode='HTML')


    @bot.message_handler(commands=['subscribe'])
    def subscribe_command(message):
        bot.database_manager.subscribe_to_recommendations(
            message.from_user.id)
        bot.send_message(
            message.chat.id,
            'Ты подписался на инвестиционные рекомендации',
            ('unsubscribe_recommends', 'help')
        )


    @bot.message_handler(commands=['unsubscribe'])
    def unsubscribe_command(message):
        bot.database_manager.unsubscribe_from_recommendations(
            message.from_user.id)
        bot.send_message(
            message.chat.id,
            'Ты отписался от инвестиционных рекомендаций',
            ('subscribe_recommends', 'help')
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
        bot.answer_callback_query(query.id)


    bot.polling(none_stop=True)
