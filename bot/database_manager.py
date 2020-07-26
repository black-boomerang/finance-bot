import os

import psycopg2

import settings


def _get_keys(filename):
    with open(filename) as sql_script:
        lines = sql_script.readlines()
    index = 0
    for line in lines:
        index += 1
        if line.strip() == '(':
            break

    keys = []
    for line in lines[index:]:
        if line.strip() == ')':
            break
        keys.append(line.split(maxsplit=1)[0])
    return keys


class DatabaseManager:
    def __init__(self):
        self.connection = psycopg2.connect(settings.DATABASE_URL,
                                           sslmode='require')
        self.cursor = self.connection.cursor()
        self.keys = _get_keys(
            os.path.join('SQL_scripts', 'create_subscribers_table.sql'))

    def execute_sql(self, filename, params=(), is_fetch=False):
        with open(filename) as sql_script:
            self.cursor.execute(sql_script.read().format(*params))
        rows = self.cursor.fetchall() if is_fetch else None
        self.connection.commit()
        return rows

    def create_subscribers_table(self):
        self.execute_sql(
            os.path.join('SQL_scripts', 'create_subscribers_table.sql'))

    def insert_subscriber(self, subscriber_id, subscriber_name, chat_id,
                          is_subscribe_recommends=True):
        try:
            self.execute_sql(
                os.path.join('SQL_scripts', 'insert_subscriber.sql'),
                params=(subscriber_id, subscriber_name, chat_id,
                        str(is_subscribe_recommends)))
        except psycopg2.errors.UniqueViolation:
            print('Подписчик уже есть в таблице')
            self.connection.rollback()
            return False
        return True

    def delete_subscriber(self, subscriber_id):
        self.execute_sql(os.path.join('SQL_scripts', 'delete_subscriber.sql'),
                         params=(subscriber_id,))

    def subscribe_to_recommendations(self, subscriber_id):
        self.execute_sql(
            os.path.join('SQL_scripts', 'update_recommendations.sql'),
            params=(True, subscriber_id))

    def unsubscribe_from_recommendations(self, subscriber_id):
        self.execute_sql(
            os.path.join('SQL_scripts', 'update_recommendations.sql'),
            params=(False, subscriber_id))

    def get_subscribers(self):
        return [dict(zip(self.keys, values)) for values in self.execute_sql(
            os.path.join('SQL_scripts', 'select_all_subscribers.sql'),
            is_fetch=True)]
