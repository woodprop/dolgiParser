import sqlite3
import datetime
from textwrap import shorten


class LinkDB:
    def __init__(self):
        self.conn = sqlite3.connect('Database.db')
        self.cursor = self.conn.cursor()
        self.cursor.execute("""CREATE TABLE IF NOT EXISTS debtors (id VARCHAR(16) NOT NULL, name VARCHAR(255), type VARCHAR(16), link VARCHAR(255), PRIMARY KEY (id))""")
        self.cursor.execute("""CREATE TABLE IF NOT EXISTS lots (id INTEGER PRIMARY KEY AUTOINCREMENT, inn VARCHAR(16), date_pub VARCHAR(16), lot_number VARCHAR(16) UNIQUE, type VARCHAR(16), description TEXT, address TINYTEXT, start_price INT, auction_type VARCHAR(32), date_start VARCHAR(16), place VARCHAR(32), link VARCHAR(255))""")


    def add_debtor(self, debtor):
        try:
            self.cursor.execute("INSERT INTO debtors (name, link, id, type) VALUES (?, ?, ?, ?)", (debtor['name'], debtor['link'], debtor['inn'], debtor['type']))
            self.conn.commit()
            print('\033[92m' + 'Должник внесён в базу' + '\033[0m')
        except:
            print('\033[91m' + 'Запись не добавлена, скорее всего, она уже существует...' + '\033[0m')

    def add_lot(self, lot):
        try:
            self.cursor.execute("INSERT INTO lots (inn, date_pub, lot_number, type, description, address, start_price, auction_type, date_start, place, link) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                                (lot['inn'], lot['date_pub'], lot['lot_number'], lot['type'], lot['description'], lot['address'], lot['start_price'], lot['auction_type'], lot['date_start'], lot['place'], lot['link']))
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
        self.cursor.execute("SELECT DISTINCT lots.link, description, debtors.name, debtors.link FROM lots JOIN debtors ON lots.inn = debtors.id")
        res = self.cursor.fetchall()
        # print(res[0][3])
        # return
        file = open('links.html', 'w', encoding='utf8')
        for lot in res:
            file.write('<div>' + '\n')
            lot_link = """<a href="{}">{}</a>""".format(lot[0], lot[0])
            sepatator = '<span> - </span>'
            lot_debtor = """<a href="{}">{}</a>""".format(lot[3], lot[2])
            lot_desc = """<p>{}</p>""".format(shorten(lot[1], width=1000, placeholder='...'))

            file.write(lot_link + '\n')
            file.write(sepatator + '\n')
            file.write(lot_debtor + '\n')
            file.write(lot_desc + '\n')
            file.write('</div>' + '\n')
            file.write('<hr>' + '\n')
        file.close()
