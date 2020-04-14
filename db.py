import pymysql
from textwrap import shorten
from jinja2 import Template


class LinkDB:
    def __init__(self):
        self.connect()
        self.cursor.execute("""CREATE TABLE IF NOT EXISTS debtors (id VARCHAR(16) NOT NULL, name VARCHAR(255), type VARCHAR(16), link VARCHAR(255), PRIMARY KEY (id))""")
        self.cursor.execute("""CREATE TABLE IF NOT EXISTS messages (id INT PRIMARY KEY AUTO_INCREMENT, inn VARCHAR(16), date_pub DATETIME, message_number VARCHAR(16) UNIQUE, description TEXT, auction_type VARCHAR(32), date_start DATETIME, place VARCHAR(255), link VARCHAR(255))""")
        self.cursor.execute("""CREATE TABLE IF NOT EXISTS lots (id INT PRIMARY KEY AUTO_INCREMENT, message_number VARCHAR(16), description TEXT, address TINYTEXT, type VARCHAR(16), start_price INT)""")

    def connect(self):
        self.conn = pymysql.connect(host='kkokarev.beget.tech',
                                    user='kkokarev_lottest',
                                    password='EUf9&gwu',
                                    db='kkokarev_lottest',
                                    charset='utf8mb4',
                                    )
        self.cursor = self.conn.cursor()

    # ---------- Добавление должника в базу ----------
    def add_debtor(self, debtor):
        try:
            self.connect()
            self.cursor.execute("INSERT INTO debtors (name, link, id, type) VALUES (%s, %s, %s, %s)", (debtor['name'], debtor['link'], debtor['inn'], debtor['type']))
            self.conn.commit()
            print('\033[92m' + 'Должник внесён в базу' + '\033[0m')
        except Exception as e:
            print(e)
            print('\033[91m' + 'Запись не добавлена, скорее всего, она уже существует...' + '\033[0m')

    # ---------- Добавление сообщения о торгах в базу ----------
    def add_message(self, message):
        try:
            self.connect()
            self.cursor.execute("INSERT INTO messages (inn, date_pub, message_number, description, auction_type, date_start, place, link) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
                           (message['inn'], message['date_pub'], message['message_number'], message['description'], message['auction_type'], message['date_start'], message['place'], message['link']))
            self.conn.commit()
            print('\033[92m' + 'Сообщение внесено в базу' + '\033[0m')
            for lot in message['lots']:
                # print(lot)
                if lot['description'] and lot['start_price']:
                    self.add_lot(lot)
        except Exception as e:
            print(e)
            print('\033[91m' + 'Запись не добавлена, скорее всего, она уже существует...' + '\033[0m')

    # ---------- Добавление лота в базу ----------
    def add_lot(self, lot):
        try:
            self.connect()
            self.cursor.execute("INSERT INTO lots (message_number, description, type, start_price) VALUES (%s, %s, %s, %s)",
                            (lot['message_number'], lot['description'], lot['type'], lot['start_price']))
            self.conn.commit()
            print('\033[92m' + 'Лот внесён в базу' + '\033[0m')
        except Exception as e:
            print(e)
            print('\033[91m' + 'Запись не добавлена, скорее всего, она уже существует...' + '\033[0m')

    def get_lots(self, message_number):
        self.connect()
        self.cursor.execute(
            "SELECT type, description, address, start_price FROM lots WHERE lots.message_number = " + str(
                message_number))
        return self.cursor.fetchall()

    def create_web(self):
        data = []
        self.connect()
        self.cursor.execute("SELECT DISTINCT messages.link, messages.description, debtors.name, debtors.link, messages.message_number, messages.date_start, messages.date_pub FROM messages JOIN debtors ON messages.inn = debtors.id")
        res = self.cursor.fetchall()

        for row in res:
            msg_data = {
                'message_link': row[0],
                'message_description': row[1],
                'message_number': row[4],
                'message_date_start': row[5],
                'message_date_pub': row[6],
                'debtor_name': row[2],
                'debtor_link': row[3],
                'message_lots': [],
            }

            lots = self.get_lots(msg_data['message_number'])
            msg_data['message_lots'] = lots
            data.append(msg_data)

        file = open('links.html', 'w', encoding='utf8')
        template = Template(u'''\
<!doctype html>
<html lang="en">
  <head>
    <!-- Required meta tags -->
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1, shrink-to-fit=no">

    <!-- Bootstrap CSS -->
    <link rel="stylesheet" href="https://stackpath.bootstrapcdn.com/bootstrap/4.4.1/css/bootstrap.min.css" integrity="sha384-Vkoo8x4CGsO3+Hhxv8T/Q5PaXtkKtu6ug5TOeNV6gBiFeWPGFN9MuhOf23Q9Ifjh" crossorigin="anonymous">

    <title>Результаты поиска</title>
  </head>
  <body>
    <div class="container">
    {% for message in res %}
        <div class="card mt-5">
          <div class="card-header bg-dark text-white d-flex justify-content-between">
            <b>№ сообщения: {{ message['message_number'] }}</b>
            <span class="">Дата публикации: {{ message['message_date_pub'] }}</span> 
          </div>
          <div class="card-body">
          <div class="accordion" id="accordionExample">
          <div class="card">
            <div class="card-header" id="headingTwo">
              <h2 class="mb-0">
                <button class="btn btn-outline-secondary collapsed" type="button" data-toggle="collapse" data-target="#collapse{{ message['message_number'] }}" aria-expanded="false" aria-controls="collapseTwo">
                  Текст объявления
                </button>
              </h2>
            </div>
            <div id="collapse{{ message['message_number'] }}" class="collapse" aria-labelledby="headingTwo" data-parent="#accordionExample">
              <div class="card-body">
                {{ message['message_description'] }}
              </div>
            </div>
            </div>
            </div>
            
            <h3 class="text-center">Лоты:</h3>
            <table class="table table-bordered">
                <thead class="thead-light">
                    <tr>
                      <th scope="col">Описание</th>
                      <th scope="col">Цена</th>
                    </tr>
                </thead>
                <tbody>
                    {% for lot in message['message_lots'] %}
                    <tr>
                      <td><div style="max-height: 150px; overflow-y: scroll">{{ lot[1] }}</div></td>
                      <td>{{ '{:0,}&nbsp;&#8381;'.format(lot[3]).replace(',', '&nbsp;') }}</td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
            <a href="{{ message['message_link'] }}" target="_blank" class="btn btn-info">Объявление о проведении торгов</a>
            <a href="{{ message['debtor_link'] }}" target="_blank" class="btn btn-danger">Карточка должника</a>
            <a href="#" target="_blank" class="btn btn-secondary disabled">Площадка торгов</a>
            <h5 class="d-inline-block float-right text-right">Начало подачи заявок: {{ message['message_date_start'] }}</h5>
          </div>
        </div>
    {% endfor %}
    </div>
    

    <!-- Optional JavaScript -->
    <!-- jQuery first, then Popper.js, then Bootstrap JS -->
    <script src="https://code.jquery.com/jquery-3.4.1.slim.min.js" integrity="sha384-J6qa4849blE2+poT4WnyKhv5vZF5SrPo0iEjwBvKU7imGFAV0wwj1yYfoRSJoZ+n" crossorigin="anonymous"></script>
    <script src="https://cdn.jsdelivr.net/npm/popper.js@1.16.0/dist/umd/popper.min.js" integrity="sha384-Q6E9RHvbIyZFJoft+2mJbHaEWldlvI9IOYy5n3zV9zzTtmI3UksdQRVvoxMfooAo" crossorigin="anonymous"></script>
    <script src="https://stackpath.bootstrapcdn.com/bootstrap/4.4.1/js/bootstrap.min.js" integrity="sha384-wfSDF2E50Y2D1uUdj0O3uMBJnjuUD4Ih7YwaYd1iqfktj0Uod8GCExl3Og8ifwB6" crossorigin="anonymous"></script>
  </body>
</html>''')

        file.write(template.render({'res': data, 'shorten': shorten}))
        file.close()
