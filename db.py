import sqlite3
import datetime


class LinkDB:
    def __init__(self):
        self.conn = sqlite3.connect('linkDatabase.db')
        self.cursor = self.conn.cursor()
        self.cursor.execute("""CREATE TABLE IF NOT EXISTS links (link, timestamp)""")

    def insert(self, link):
        self.cursor.execute("INSERT INTO links VALUES (?, ?)", (link, datetime.datetime.now()))
        self.conn.commit()

    def get_all(self):
        self.cursor.execute("SELECT * FROM links")
        print(self.cursor.fetchall())

    def create_web(self):
        self.cursor.execute("SELECT DISTINCT link, timestamp FROM links ORDER BY timestamp DESC")
        links = self.cursor.fetchall()

        file = open('links.html', 'w')
        for link in links:
            tag = """<a href="{}" style="display: block">{}</a>""".format(link[0], link[1])
            file.write(tag + '\n')
        file.close()
