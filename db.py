import sqlite3
import datetime
from textwrap import shorten


class LinkDB:
    def __init__(self):
        self.conn = sqlite3.connect('Database.db')
        self.cursor = self.conn.cursor()
        self.cursor.execute("""CREATE TABLE IF NOT EXISTS debtors (id VARCHAR(16) NOT NULL, name VARCHAR(255), type VARCHAR(16), link VARCHAR(255), PRIMARY KEY (id))""")
        self.cursor.execute("""CREATE TABLE IF NOT EXISTS messages (id INTEGER PRIMARY KEY AUTOINCREMENT, inn VARCHAR(16), date_pub VARCHAR(16), message_number VARCHAR(16) UNIQUE, description TEXT, auction_type VARCHAR(32), date_start VARCHAR(16), place VARCHAR(32), link VARCHAR(255))""")
        self.cursor.execute("""CREATE TABLE IF NOT EXISTS lots (id INTEGER PRIMARY KEY AUTOINCREMENT, message_number VARCHAR(16) UNIQUE, description TEXT, address TINYTEXT, type VARCHAR(16), start_price INT)""")


    def add_debtor(self, debtor):
        try:
            self.cursor.execute("INSERT INTO debtors (name, link, id, type) VALUES (?, ?, ?, ?)", (debtor['name'], debtor['link'], debtor['inn'], debtor['type']))
            self.conn.commit()
            print('\033[92m' + 'Должник внесён в базу' + '\033[0m')
        except:
            print('\033[91m' + 'Запись не добавлена, скорее всего, она уже существует...' + '\033[0m')

    def add_message(self, message):
        try:
            self.cursor.execute("INSERT INTO messages (inn, date_pub, message_number, description, auction_type, date_start, place, link) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                                (message['inn'], message['date_pub'], message['message_number'], message['description'], message['auction_type'], message['date_start'], message['place'], message['link']))
            self.conn.commit()
            print('\033[92m' + 'Сообщение внесено в базу' + '\033[0m')
        except:
            print('\033[91m' + 'Запись не добавлена, скорее всего, она уже существует...' + '\033[0m')

    def add_lot(self, lot):
        try:
            self.cursor.execute("INSERT INTO lot (message_number, description, type, start_price) VALUES (?, ?, ?, ?)",
                                (lot['message_number'], lot['description'], lot['type'], lot['start_price']))
            self.conn.commit()
            print('\033[92m' + 'Лот внесён в базу' + '\033[0m')
        except:
            print('\033[91m' + 'Запись не добавлена, скорее всего, она уже существует...' + '\033[0m')


    def insert(self, link):
        self.cursor.execute("INSERT INTO links VALUES (?, ?)", (link, datetime.datetime.now()))
        self.conn.commit()

    def get_all(self):
        self.cursor.execute("SELECT * FROM links")
        print(self.cursor.fetchall())

    def create_web(self):
        self.cursor.execute("SELECT DISTINCT messages.link, description, debtors.name, debtors.link FROM messages JOIN debtors ON messages.inn = debtors.id")
        res = self.cursor.fetchall()
        # print(res[0][3])
        # return
        file = open('links.html', 'w', encoding='utf8')
        for message in res:
            file.write('<div>' + '\n')
            message_link = """<a href="{}">{}</a>""".format(message[0], message[0])
            sepatator = '<span> - </span>'
            message_debtor = """<a href="{}">{}</a>""".format(message[3], message[2])
            message_desc = """<p>{}</p>""".format(shorten(message[1], width=1000, placeholder='...'))

            file.write(message_link + '\n')
            file.write(sepatator + '\n')
            file.write(message_debtor + '\n')
            file.write(message_desc + '\n')
            file.write('</div>' + '\n')
            file.write('<hr>' + '\n')
        file.close()
