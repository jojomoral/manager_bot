from aiogram import Bot, types
from aiogram.dispatcher import Dispatcher, FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.utils import executor
from aiogram.types import ReplyKeyboardRemove, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, \
    InlineKeyboardButton

import asyncio
import datetime
import sqlite3
import pandas as pd
import traceback

###########################
####    ТОКЕН БОТА ########
###########################
TOKEN = '1888300214:AAHANDYsJaZfVXKIH-Bnmx5382XqO88YYoE'

sql_conn = sqlite3.connect('main.db', check_same_thread=False)
sql_curs = sql_conn.cursor()

bot = Bot(token=TOKEN)

dp = Dispatcher(bot, storage=MemoryStorage())

work_days = ['1', '2', '3', '4', '5', '6', '7']
work_hours = ['00:00', '23:50']

async def edit_message_desk(interval=1):
    while True:
        await asyncio.sleep(interval)
        data = DB.get_wait()
        for line in data:
            manager_get, desk_id, message_id, num, timer, manager_id, client_fio = line
            manager_status = DB.get_col_db('managers', manager_id, 'status')
            manager_fio = DB.get_col_db('managers', manager_id, 'fio')

            timer = TIME.count_timer(timer)
            timer = DB.set_time_wait(num)

            get = ''
            if manager_get == 1:
                get = ', подтвердил получение уведомления'

            text = f"""❗️❗️❗️❗️❗️❗️❗️❗️❗️❗️❗️❗️
Менеджер: {manager_fio}
Статус: {manager_status} {get}
Клиент: {client_fio}
Время: {timer}
❗️❗️❗️❗️❗️❗️❗️❗️❗️❗️❗️❗️	
"""
            markup = InlineKeyboardMarkup()
            markup.add(InlineKeyboardButton('Менеджер подошел', callback_data=f'desk_get_{num}'))
            try:
                await bot.edit_message_text(text, desk_id, message_id, reply_markup=markup)
            except Exception as ex:
                print('К клиенту уже подошли')


async def delete_time_dinner(interval=30):
    while True:
        await asyncio.sleep(interval)
        sql = "UPDATE managers SET status = 'готов' WHERE TIME(SUBSTR(managers.status, 9, 5)) < TIME('now','localtime')"
        sql_curs.execute(sql)
        sql_conn.commit()


class DB():

    def get_manager_message_id(id):
        sql = f'SELECT id_message FROM managers WHERE id = {id}'
        sql_curs.execute(sql)
        select = sql_curs.fetchall()[0][0]
        sql_conn.commit()
        return select

    def set_manager_message_id(id, id_message):
        sql = f'UPDATE managers SET id_message = {id_message} WHERE id = {id}'
        sql_curs.execute(sql)
        sql_conn.commit()

    def set_time_agree(num):
        time = TIME.get_time_now()
        sql = f"UPDATE history SET time_agree = '{time}' WHERE number = {num}"
        sql_curs.execute(sql)
        sql_conn.commit()

    def get_messages_for_delete_id(id):
        sql = f"SELECT id_desk,id_message,id_message_manager FROM message_id_desk WHERE id_manager = {id}"
        sql_curs.execute(sql)
        select = sql_curs.fetchall()
        sql_conn.commit()
        return select

    def get_wait_manager(num):
        sql = f"SELECT id_manager FROM message_id_desk WHERE num_client = {num}"
        sql_curs.execute(sql)
        select = sql_curs.fetchall()[0][0]
        sql_conn.commit()
        return select

    def delete_wait(id):
        sql = f"DELETE FROM message_id_desk WHERE id_manager = {id}"
        sql_curs.execute(sql)
        sql_conn.commit()

    def get_wait():
        sql = "SELECT manager_get, id_desk, id_message, num_client, timer, id_manager, fio_client FROM message_id_desk"
        sql_curs.execute(sql)
        select = sql_curs.fetchall()
        sql_conn.commit()
        return select

    def get_wait_timer(num_client):
        sql = f"SELECT timer FROM message_id_desk WHERE num_client = {num_client}"
        sql_curs.execute(sql)
        select = sql_curs.fetchall()[0][0]
        sql_conn.commit()
        return select

    def set_wait_timer(num_client, timer):
        sql = f"UPDATE message_id_desk SET timer = '{timer}' WHERE num_client = {num_client}"
        sql_curs.execute(sql)
        sql_conn.commit()

    def set_wait_manager_get(num_client, id_message_manager):
        sql = f"UPDATE message_id_desk SET manager_get = 1, id_message_manager = {id_message_manager} WHERE num_client = {num_client}"
        sql_curs.execute(sql)
        sql_conn.commit()

    def set_new_wait(id_desk, id_message, num_client, id_manager, fio_client, id_message_manager):
        sql = f"""INSERT INTO message_id_desk (id_desk, id_message, num_client, id_manager,fio_client, id_message_manager ) 
									VALUES ({id_desk},{id_message},{num_client}, '{id_manager}', '{fio_client}', {id_message_manager})"""

        sql_curs.execute(sql)
        sql_conn.commit()

    def get_hisory():
        filename = 'history.xlsx'
        sql = "SELECT date, id_manager, fio_client, time_start, time_agree, time_wait FROM history"
        df = pd.read_sql(sql, sql_conn)
        writer = pd.ExcelWriter(filename)
        df.to_excel(writer)

        writer.save()
        writer.close()

    def get_managers():
        sql = 'SELECT * FROM managers'
        sql_curs.execute(sql)
        select = sql_curs.fetchall()
        sql_conn.commit()
        return select

    def check_manager(id):
        sql = f'SELECT id FROM managers WHERE id = {id}'
        sql_curs.execute(sql)
        select = sql_curs.fetchall()
        sql_conn.commit()
        if len(select) != 0:
            return True
        return False

    def check_admin(id):
        sql = f'SELECT id FROM id_admins WHERE id = {id}'
        sql_curs.execute(sql)
        select = sql_curs.fetchall()
        sql_conn.commit()
        if len(select) != 0:
            return True
        return False

    def check_desk(id):
        sql = f'SELECT id FROM id_front_desk_stuff WHERE id = {id}'
        sql_curs.execute(sql)
        select = sql_curs.fetchall()
        sql_conn.commit()
        if len(select) != 0:
            return True
        return False

    def get_last_number():
        sql = 'SELECT number FROM history ORDER BY number DESC LIMIT 1;'
        sql_curs.execute(sql)
        select = sql_curs.fetchall()[0][0]
        sql_conn.commit()
        return select

    def set_time_wait(num):
        sql = f"SELECT time_start FROM history WHERE number = {num};"
        sql_curs.execute(sql)
        time_start = sql_curs.fetchall()[0][0]
        sql_conn.commit()
        time = TIME.get_delta_time(time_start)
        sql = f"UPDATE history SET time_wait = '{time}' WHERE number = {num};"
        sql_curs.execute(sql)
        sql_conn.commit()
        return time

    def set_time_start(num):
        time = TIME.get_time_now()
        sql = f"UPDATE history SET time_start = '{time}' WHERE number = {num}"
        sql_curs.execute(sql)
        sql_conn.commit()

    def set_new_history(id_manager, fio_client):
        date = TIME.get_date_now()
        sql = f"INSERT INTO history ('date','id_manager', 'fio_client') VALUES ('{date}','{id_manager}', '{fio_client}');"
        sql_curs.execute(sql)
        sql_conn.commit()
        sql = "SELECT number FROM history ORDER BY number DESC LIMIT 1;"
        sql_curs.execute(sql)
        select = sql_curs.fetchall()[0][0]
        return select

    def get_client_fio(num):
        sql = f'SELECT fio_client FROM history WHERE number = {num}'
        sql_curs.execute(sql)
        select = sql_curs.fetchall()[0][0]
        sql_conn.commit()
        return select

    def get_col_db(table, id, col):
        sql = f'SELECT {col} FROM {table} WHERE id = {id}'
        sql_curs.execute(sql)
        select = sql_curs.fetchall()[0][0]
        sql_conn.commit()
        return select

    def set_status(id, status):
        sql = f"UPDATE managers SET status = '{status}' WHERE id = {id}"
        sql_curs.execute(sql)
        sql_conn.commit()


class desk_stuff_step(StatesGroup):
    CLIENT_FIO = State()


class manager_set_dinner(StatesGroup):
    DINNER_TIME = State()


class TIME():

    def count_timer(timer):
        now = datetime.datetime.strptime(timer, "%M:%S") + datetime.timedelta(seconds=1)
        return now.strftime('%M:%S')

    def get_time_now():
        now = datetime.datetime.now()
        return now.strftime('%H:%M:%S')

    def get_date_now():
        now = datetime.datetime.now()
        return now.date()

    def get_delta_time(time_first):
        now = datetime.datetime.strptime(TIME.get_time_now(), "%H:%M:%S")
        time_first = datetime.datetime.strptime(time_first, "%H:%M:%S")
        delta = datetime.datetime.strptime(str(now - time_first), "%H:%M:%S")
        return delta.strftime('%M:%S')

    def is_work_time():
        day_now = str(datetime.datetime.now().isoweekday())
        time_now = datetime.datetime.strptime(TIME.get_time_now(), "%H:%M:%S")
        time_start = datetime.datetime.strptime(work_hours[0], "%H:%M")
        time_finish = datetime.datetime.strptime(work_hours[1], "%H:%M")

        if (time_start < time_now < time_finish) and (day_now in work_days):
            return True

        return False


# Обработка команды get_history
@dp.message_handler(commands=['get_history'])
async def process_menu_m_command(message: types.Message):
    if DB.check_admin(message.chat.id):
        DB.get_hisory()
        with open('history.xlsx', 'rb') as file:
            await bot.send_document(message.chat.id, file)
    else:
        await bot.send_message(message.chat.id, 'Доступ к данной команде есть только у администраторов')


# Обработка команды menu_m
@dp.message_handler(commands=['menu_m'])
async def process_menu_m_command(message: types.Message):
    if TIME.is_work_time():
        if DB.check_desk(message.chat.id):
            await bot.delete_message(message.chat.id, message_id=message.message_id)
            markup = InlineKeyboardMarkup()
            managers = DB.get_managers()

            for manager in managers:
                status_now = ''
                if manager[2] != 'готов':
                    status_now = f'({manager[2]})'

                markup.add(
                    InlineKeyboardButton(f'{manager[1]} {status_now}', callback_data=f'menu_m_call_{manager[0]}'))
            markup.add(InlineKeyboardButton(f'Отмена', callback_data=f'delete_message'))

            await bot.send_message(message.chat.id, text="Выбери менеджера", reply_markup=markup)

        else:
            await bot.send_message(message.chat.id, text="Доступ к данной команде есть только у сотрудников рецепшена")
    else:
        await bot.send_message(message.chat.id, text='Рабочее время закончилось')


# Обработка команды menu_m
@dp.message_handler(commands=['set_status'])
async def process_status_command(message: types.Message):
    if TIME.is_work_time():
        if DB.check_manager(message.chat.id):
            await bot.delete_message(message.chat.id, message_id=message.message_id)
            markup = ReplyKeyboardMarkup(resize_keyboard=True)
            markup.add(KeyboardButton('На месте'))
            markup.row(KeyboardButton('Отсутствие'))
            markup.row(KeyboardButton('Обед'))

            msg = await bot.send_message(message.chat.id, 'Выбери статус', reply_markup=markup)

            DB.set_manager_message_id(message.chat.id, msg.message_id)

        else:
            await bot.send_message(message.chat.id, text="Доступ к данной команде есть только у менеджеров")
    else:
        await bot.send_message(message.chat.id, text='Рабочее время закончилось')


# Обработка кнопок статуса менеджеров
@dp.callback_query_handler(lambda c: c.data.startswith('status_'))
async def process_callback_button1(callback: types.CallbackQuery):
    await bot.answer_callback_query(callback.id)

    await bot.delete_message(callback.message.chat.id, message_id=callback.message.message_id)
    if callback.data == 'status_ready':
        DB.set_status(callback.message.chat.id, 'готов')
        await bot.send_message(callback.message.chat.id, 'Установлен статус "На месте"')

    elif callback.data == 'status_miss':
        DB.set_status(callback.message.chat.id, 'отсутствие')
        await bot.send_message(callback.message.chat.id, 'Установлен статус "Отсутствие"')

    else:
        DB.set_status(callback.message.chat.id, 'обед')
        await bot.send_message(callback.message.chat.id, 'Напиши время, до скольки у тебя будет обед в формате ЧЧ:ММ')


# Обработка кнопок меню менеджеров
@dp.callback_query_handler(lambda c: c.data.startswith('delete_message'))
async def process_callback_button(callback: types.CallbackQuery):
    await bot.answer_callback_query(callback.id)
    await bot.delete_message(callback.message.chat.id, message_id=callback.message.message_id)


# Обработка кнопок меню менеджеров
@dp.callback_query_handler(lambda c: c.data.startswith('menu_m_call_'))
async def process_callback_button(callback: types.CallbackQuery):
    await bot.answer_callback_query(callback.id)
    await desk_stuff_step.CLIENT_FIO.set()
    manager_id = callback.data[12:]

    manager_status = DB.get_col_db('managers', manager_id, 'status')

    if manager_status != 'отсутствие':
        state = dp.current_state(user=callback.message.chat.id)

        await bot.delete_message(callback.message.chat.id, message_id=callback.message.message_id)
        await state.update_data(manager_id=manager_id)
        await bot.send_message(callback.message.chat.id, 'Введите ФИО клиента')


# Подтверждение получения уведомления от менеджера
@dp.callback_query_handler(lambda c: c.data.startswith('manager_get_'))
async def process_callback_button(callback: types.CallbackQuery):
    await bot.answer_callback_query(callback.id)

    data = callback.data[12:]
    num, desk_id = data.split('_')

    manager_fio = DB.get_col_db('managers', callback.message.chat.id, 'fio')
    client_fio = DB.get_client_fio(num)
    manager_status = DB.get_col_db('managers', callback.message.chat.id, 'status')

    DB.set_wait_manager_get(num, callback.message.message_id)
    DB.set_time_agree(num)

    await bot.edit_message_text(f'Вас ожидает клиент {client_fio}', callback.message.chat.id,
                                message_id=callback.message.message_id)


# Подтверждение прихода менеджера
@dp.callback_query_handler(lambda c: c.data.startswith('desk_get_'))
async def process_callback_button(callback: types.CallbackQuery):
    await bot.answer_callback_query(callback.id)

    num = callback.data[9:]
    time = DB.set_time_wait(num)
    manager_id = DB.get_wait_manager(num)

    messages_for_delete_id = DB.get_messages_for_delete_id(manager_id)

    DB.delete_wait(manager_id)
    for line in messages_for_delete_id:
        await bot.delete_message(callback.message.chat.id, message_id=line[1])
        await bot.delete_message(manager_id, message_id=line[2])


# Ожидание ввода времени обеда
@dp.message_handler(state=manager_set_dinner.DINNER_TIME)
async def dinner_time(message: types.Message, state: FSMContext):
    DB.set_status(message.chat.id, f'обед до {message.text}')
    msg_id = DB.get_manager_message_id(message.chat.id)

    await bot.delete_message(message.chat.id, message_id=message.message_id)
    await bot.delete_message(message.chat.id, message_id=msg_id)
    await bot.send_message(message.chat.id, f'Установлен статус "обед до {message.text}"')
    await state.finish()


# Ожидание ввода ФИО клиента от рецепшена
@dp.message_handler(state=desk_stuff_step.CLIENT_FIO)
async def fio_state_stuff(message: types.Message, state: FSMContext):
    data = await state.get_data()

    manager_id = data['manager_id']
    client_fio = message.text
    if client_fio.replace(' ', '').isalpha():
        manager_fio = DB.get_col_db('managers', manager_id, 'fio')
        manager_status = DB.get_col_db('managers', manager_id, 'status')
        await state.finish()

        num = DB.set_new_history(manager_id, client_fio)

        DB.set_time_start(num)

        text_desk = f"""❗️❗️❗️❗️❗️❗️❗️❗️❗️❗️❗️❗️
    Менеджер: {manager_fio}
    Статус: {manager_status}
    Клиент: {client_fio}
    Время: 00:00
    ❗️❗️❗️❗️❗️❗️❗️❗️❗️❗️❗️❗️	
    """
        markup_desk = InlineKeyboardMarkup()
        markup_desk.add(InlineKeyboardButton('Менеджер подошел', callback_data=f'desk_get_{num}'))

        # Отправка информации менеджеру
        text = f'Вас ожидает клиент {client_fio}'
        markup = InlineKeyboardMarkup()
        markup.add(
            InlineKeyboardButton('Подтвердить получение уведомления', callback_data=f'manager_get_{num}_{message.chat.id}'))


        msg_desk = await bot.send_message(message.chat.id, text_desk, reply_markup=markup_desk)
        msg = await bot.send_message(manager_id, text, reply_markup=markup)

        DB.set_new_wait(message.chat.id, msg_desk.message_id, num, manager_id, client_fio, msg.message_id)
    else:
        await bot.send_message(message.chat.id, 'ФИО должно состоять только из букв. Повторите ввод.')
    await bot.delete_message(message.chat.id, message_id=message.message_id)
    await bot.delete_message(message.chat.id, message_id=message.message_id - 1)


@dp.message_handler()
async def handler_text(message: types.Message):
    if DB.check_manager(message.chat.id):
        msg_id = DB.get_manager_message_id(message.chat.id)
        if message.text == 'На месте':
            DB.set_status(message.chat.id, 'готов')

            await bot.delete_message(message.chat.id, message_id=msg_id)
            await bot.send_message(message.chat.id, 'Установлен статус "На месте"')
        elif message.text == 'Отсутствие':
            DB.set_status(message.chat.id, 'отсутствие')

            await bot.delete_message(message.chat.id, message_id=msg_id)
            await bot.send_message(message.chat.id, 'Установлен статус "Отсутствие"')
        elif message.text == 'Обед':
            msg = await bot.send_message(message.chat.id, 'Напиши время, до скольки у тебя будет обед в формате ЧЧ:ММ')

            DB.set_manager_message_id(message.chat.id, msg.message_id)

            await bot.delete_message(message.chat.id, message_id=msg_id)
            await manager_set_dinner.DINNER_TIME.set()

    await bot.delete_message(message.chat.id, message_id=message.message_id)


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.create_task(edit_message_desk())
    loop.create_task(delete_time_dinner())
    executor.start_polling(dp)
