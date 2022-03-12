from main import *
import telebot
from telebot import types
from auth_data import token
import sqlite3
import time


def telegram_bot(token):
    bot = telebot.TeleBot(token)
    log = ''
    passw = ''

    # Подключаем базу данных и создаем функцию для заполнения
    conn = sqlite3.connect('DataBase.db', check_same_thread=False)
    cursor = conn.cursor()

    def db_commit_table(user_id: int, login: str, password: str, marks: str):
        cursor.execute('INSERT INTO records (user_id, login, password, marks) VALUES(?,?,?,?)', (user_id, login, password, marks))
        conn.commit()

    # Основные действия бота
    @bot.message_handler(commands=['start'])
    def start_message(message):
        bot.send_message(message.chat.id, 'Привет! Напиши /help для ознакомления с ботом')

    @bot.message_handler(commands=['help'])
    def help_list(message):
        bot.send_message(message.chat.id, 'Привет! Это бот, который поможет вам упростить просмотр оценок, а также,' +
                                          ' с его помощью вы сможете получать уведомления о ваших новых оценках.'+'\n'
                                          'Перечень команд:'+'\n'
                                          '/reg - Регистрация'+'\n'
                                          '/mydiary - Получить табель'+'\n'
                                          '/subscribe - Подписка на рассылку о новых оценках'+'\n'
                                          '/unsubscribe - Отключение подписки'+'\n' 
                                          '/delete - Удалить логин и пароль из базы данных'
                         )

    @bot.message_handler(commands=['mydiary'])
    def tables_mark(message):
        user_id = message.chat.id
        if cursor.execute('SELECT * FROM records WHERE user_id = ?', (user_id, )).fetchone() is None:
            bot.send_message(user_id, 'Вы не зарегестрированы! Напишите /reg для регистрации')
        else:
            log = cursor.execute(f'SELECT login FROM records WHERE user_id={user_id}').fetchone()
            passw = cursor.execute(f'SELECT password FROM records WHERE user_id={user_id}').fetchone()
            table = get_marks_table(log, passw)
            table_str = []
            for key, value in table.items():
                if len(value) != 0:
                    table_str.append('{}: {} ({})'.format(key, ' '.join(map(str, value)), round(sum(value)/len(value), 2)))
                else:
                    table_str.append('{}: {}'.format(key, ' '.join(map(str, value))))
            diary = '\n'.join(table_str)
            bot.send_message(user_id, diary)

    @bot.message_handler(commands=['subscribe'])
    def monitoring(message):
        user_id = message.chat.id
        if cursor.execute('SELECT * FROM records WHERE user_id = ?', (user_id, )).fetchone() is None:
            bot.send_message(user_id, 'Вы не зарегестрированы! Напишите /reg для регистрации')
        else:
            bot.send_message(user_id, 'Вы успешно включили уведомления о новых оценках')
            delay_time = 5
            # delay_time_night = 5 * 3600
            usr_log = cursor.execute(f'SELECT login FROM records WHERE user_id={user_id}').fetchone()
            usr_passw = cursor.execute(f'SELECT password FROM records WHERE user_id={user_id}').fetchone()

            # Меняем значение подписки с False на True
            cursor.execute('UPDATE records SET subscription=? WHERE user_id=?', (1, user_id))
            conn.commit()

            while True:
                subs_condition = cursor.execute(f'SELECT subscription FROM records WHERE user_id={user_id}').fetchone()[0]
                if subs_condition == 1:
                    old_html = cursor.execute(f'SELECT marks FROM records WHERE user_id={user_id}').fetchone()[0]
                    new_marks = get_marks_table(usr_log, usr_passw)
                    data = get_data(old=old_html, new=new_marks)
                    if data is not False:
                        new_marks_html = elschool_html(usr_log, usr_passw)
                        cursor.execute('UPDATE records SET marks=? WHERE user_id=?', (new_marks_html, user_id))
                        conn.commit()
                        bot.send_message(user_id, str(data))
                    else:
                        bot.send_message(user_id, 'NO')
                else:
                    break
                time.sleep(delay_time)

    @bot.message_handler(commands=['unsubscribe'])
    def unsubscribe(message):
        user_id = message.chat.id
        cursor.execute('UPDATE records SET subscription=? WHERE user_id=?', (0, user_id))
        conn.commit()
        bot.send_message(user_id, 'Вы отключили подписку')

    @bot.message_handler(commands=['delete'])
    def delete(message):
        user_id = message.chat.id
        if cursor.execute('SELECT * FROM records WHERE user_id = ?', (user_id,)).fetchone() is None:
            bot.send_message(user_id, 'Вас нет в базе данных')

        else:
            markup = types.InlineKeyboardMarkup(row_width=2)
            item1 = types.InlineKeyboardButton('Да, я точно уверен', callback_data='delete_yes')
            item2 = types.InlineKeyboardButton('Нет', callback_data='delete_no')
            markup.add(item1, item2)
            bot.send_message(user_id, 'Вы уверены, что хотите удалить ваши данные?', reply_markup=markup)

    @bot.message_handler(commands=['reg'])
    def registration(message):
        user_id = message.chat.id
        if cursor.execute('SELECT * FROM records WHERE user_id = ?', (user_id, )).fetchone() is not None:
            bot.send_message(user_id,
                             'Вы уже зарегестрированы! Удалите данные командой /delete, и пройдите регистрацию заново')
        else:
            bot.send_message(message.chat.id, 'Напиши свой логин')
            bot.register_next_step_handler(message, get_login)

    def get_login(message):
        global log
        log = message.text
        bot.send_message(message.chat.id, 'Напиши свой пароль')
        bot.register_next_step_handler(message, get_password)

    def get_password(message):
        global log
        global passw
        passw = message.text
        markup = types.InlineKeyboardMarkup(row_width=1)
        item1 = types.InlineKeyboardButton('Да', callback_data='yes')
        item2 = types.InlineKeyboardButton('Нет', callback_data='no')
        markup.add(item1, item2)
        bot.send_message(message.chat.id, 'Ваш логин: ' + log + '\n' +
                                          'Ваш пароль: ' + passw + '\n' +
                                          'Верно?',
                         reply_markup=markup)

    # Ответ на созданные кнопки
    @bot.callback_query_handler(func=lambda call: True)
    def answer(call):
        global log
        global passw
        if call.message:
            if call.data == 'yes':
                markup = types.InlineKeyboardMarkup(row_width=2)
                item3 = types.InlineKeyboardButton('Запомнить', callback_data='DB')
                item4 = types.InlineKeyboardButton('Ввывести оценки', callback_data='DB_no')
                markup.add(item3, item4)
                bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.id,
                                      text='Нажав на «Запомнить», бот запомнит ваши логин и пароль и вам будут достпуны'+
                                           ' команды из списка /help. Или вы просто можете ввывести оценки.',
                                      reply_markup=markup)
            elif call.data == 'no':
                bot.send_message(call.message.chat.id, 'Напишите заново /reg')

            if call.data == 'DB':
                table_html = elschool_html(log, passw)
                if table_html != 'Неправильно введены данные!':
                    user_id = call.message.chat.id
                    cursor.execute(f'SELECT user_id FROM records WHERE user_id={user_id}')
                    if cursor.fetchone() is None:
                        db_commit_table(user_id=user_id, login=log, password=passw, marks=table_html)
                    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.id,
                                          text='Ваши данные успешно записаны! Напишите /help для ознакомления с коман'+
                                               'дами или откройте меню рядом со строкой ввода текста.'
                                          )
                else:
                    bot.send_message(call.message.chat.id, 'Логин и пароль неверны')
            elif call.data == 'DB_no':
                table = get_marks_table(log, passw)
                table_str = []
                for key, value in table.items():
                    if len(value) != 0:
                        table_str.append(
                            '{}: {} ({})'.format(key, ' '.join(map(str, value)), round(sum(value) / len(value), 2)))
                    else:
                        table_str.append('{}: {}'.format(key, ' '.join(map(str, value))))
                diary = '\n'.join(table_str)
                bot.send_message(call.message.chat.id, diary)

            if call.data == 'delete_yes':
                cursor.execute(f'DELETE FROM records WHERE user_id={call.message.chat.id}')
                conn.commit()
                bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.id,
                                      text='Ваши данные успешно удаленны')
            elif call.data == 'delete_no':
                bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.id,
                                      text='Красавчик')

    bot.infinity_polling()


if __name__ == '__main__':
    telegram_bot(token)


