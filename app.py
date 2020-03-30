from bs4 import BeautifulSoup
import re
import asyncio
from pyppeteer import launch
from db import LinkDB

base_url = 'http://bankrot.fedresurs.ru'
base_url_mes = 'https://bankrot.fedresurs.ru/Messages.aspx'

# ---------- Сброс ограничения времени открытого браузера в 20 секунд ----------
def disable_timeout_pyppeteer():
    import pyppeteer.connection
    original_method = pyppeteer.connection.websockets.client.connect
    def new_method(*args, **kwargs):
        kwargs['ping_interval'] = None
        kwargs['ping_timeout'] = None
        return original_method(*args, **kwargs)

    pyppeteer.connection.websockets.client.connect = new_method
# -------------------------------------------------------------------------------

def main():
    keywords = ['здание', 'помещение', 'квартира']
    disable_timeout_pyppeteer()
    html = asyncio.get_event_loop().run_until_complete(get_search_result_page(base_url_mes, 3000))
    # return
    db = LinkDB()
    # db.insert('hlkgsdkgjksd')
    # db.get_lots(4846856)
    # db.create_web()
    # return
    # html = asyncio.get_event_loop().run_until_complete(get_html(base_url_mes, 2000))
    data = get_info(html)
    links = data['links']
    debtors = data['debtors']

    if not links:
        print('No links in response...')
        return

    print('\033[92m' + 'Начало проверки сообщений...' + '\033[0m')
    for link in links:
        # print(link)
        message = get_message_info(link, keywords)
        if message:
            db.add_message(message)

    if not debtors:
        print('Должники не найдены...')
        return

    print('\033[92m' + 'Внесение должников в базу...' + '\033[0m')
    for d in debtors:
        # print(d['name'], d['link'])
        d.update(get_debtor_info(d))
        if 'Organization' in d['link']:
            d['type'] = 'company'
        else:
            d['type'] = 'person'

        db.add_debtor(d)

    # return  # Страницу пока не делаем TODO

    # ---------- Сборка веб-страницы ----------
    print('Создание страницы со ссылками...')
    db.create_web()

# -------------------------------------------------------------------------------------------------------------------

async def get_search_result_page(url, delay):
    browser = await launch()
    page = await browser.newPage()


    await page.setViewport(viewport=dict(width=1920, height=4080))

    await page.goto(url)
    print('Загрузка страницы поиска...')
    await page.waitFor(delay)

    # ---------- Клик на поле ТИП СООБЩЕНИЯ ----------
    print('Выбор категирии и дат...')
    await page.click('input[name="ctl00$cphBody$mdsMessageType$tbSelectedText"]')
    await page.waitFor(2000)

    # Раскрытие списка "Огранизация и проведение реализации имущества"
    await page.mouse.click(200, 270)
    await page.waitFor(1000)
    # Клик на "Объявление о проведении торгов"
    await page.mouse.click(200, 300)
    await page.waitFor(1000)
    # await page.screenshot({'path': 'example.png'})

    # ---------- Ввод даты поиска ----------
    await page.click('input[id="ctl00_cphBody_cldrBeginDate_tbSelectedDate"]')
    await page.keyboard.down('Control')
    await page.keyboard.press('KeyA')
    await page.keyboard.up('Control')
    await page.type('input[id="ctl00_cphBody_cldrBeginDate_tbSelectedDate"]', '27.03.2020')

    await page.click('input[id="ctl00_cphBody_cldrEndDate_tbSelectedDate"]')
    await page.keyboard.down('Control')
    await page.keyboard.press('KeyA')
    await page.keyboard.up('Control')
    await page.type('input[id="ctl00_cphBody_cldrEndDate_tbSelectedDate"]', '27.03.2020')

    await page.keyboard.press('Enter')
    print('Поиск...')
    # await page.waitForSelector('table.bank')
    # print('OK')
    await page.waitFor(5000)
    # await page.screenshot({'path': 'example.png'})
    html = await page.content()
    # --------------------- test code ---------------------------

    # print(len(html))

    for p in range(2, 10):
        print('\033[92m' + 'Поиск по странице {}...'.format(p) + '\033[0m')
        await page.evaluate('''__doPostBack('ctl00$cphBody$gvMessages','Page${}')'''.format(p))
        await page.waitFor(1000)
        if await page.querySelector('th[scope="col"]'):
            # await page.screenshot({'path': 'example{}.png'.format(p)})
            html += await page.content()
            print('\033[92m' + 'Успешно!' + '\033[0m')
            # print(len(html))
        else:
            break
    # print(pagination_links)
    # for p_link in pagination_links:
    #     print(p_link)




    # -----------------------------------------------------------
    await browser.close()

    return html


# -------------------------------------------------------------
async def get_html(url, delay):
    browser = await launch()
    page = await browser.newPage()
    await page.goto(url)
    print('Loading page...')
    await page.waitForSelector('table')
    # await page.waitFor(delay)
    # await page.screenshot({'path': 'example.png'})
    html = await page.content()
    await browser.close()
    return html
# ////////////////////////////////////////////////////////


def get_debtor_info(debtor):
    data = {}
    html = asyncio.get_event_loop().run_until_complete(get_html(debtor['link'], 3000))
    soup = BeautifulSoup(html, 'html.parser')
    inn = soup.find('span', id='ctl00_cphBody_lblINN').text
    data['inn'] = inn
    return data


def get_message_info(link, keywords):
    print(link)
    html = asyncio.get_event_loop().run_until_complete(get_html(link, 2000))
    soup = BeautifulSoup(html, 'html.parser')
    try:
        lot_table = soup.select_one('table.lotInfo').text
    except:
        print('\033[91m' + 'Пустой лот!...' + '\033[0m')
        return False

    message_data = {'lots': []}
    if '(изменено)' in soup.select_one('h1').text:
        print('Лот неактуальный')
        return False

    for kw in keywords:
        if kw not in lot_table.lower():
            continue

        print('\033[92m' + 'Найдено: {}'.format(kw) + '\033[0m')
        # if 'ФИО' in soup.text:
        if 'ФИО' in soup.select_one('table.headInfo:nth-child(6)').text:
            print('Физ лицо')
            message_data['inn'] = soup.select_one('#ctl00_BodyPlaceHolder_lblBody > div > table:nth-child(6) > tbody > tr:nth-child(5) > td:nth-child(2)').text.strip()
            message_data['date_pub'] = soup.select_one('#ctl00_BodyPlaceHolder_lblBody > div > table:nth-child(2) > tbody > tr.odd > td:nth-child(2)').text.strip()
            message_data['message_number'] = soup.select_one('#ctl00_BodyPlaceHolder_lblBody > div > table:nth-child(2) > tbody > tr.even > td:nth-child(2)').text.strip()
        else:
            message_data['inn'] = soup.select_one('#ctl00_BodyPlaceHolder_lblBody > div > table:nth-child(6) > tbody > tr:nth-child(4) > td:nth-child(2)').text.strip()
            message_data['date_pub'] = soup.select_one('#ctl00_BodyPlaceHolder_lblBody > div > table:nth-child(2) > tbody > tr.odd > td:nth-child(2)').text.strip()
            message_data['message_number'] = soup.select_one('#ctl00_BodyPlaceHolder_lblBody > div > table:nth-child(2) > tbody > tr.even > td:nth-child(2)').text.strip()
        message_data['description'] = soup.select('div.msg')[-2].text.strip()
        message_data['auction_type'] = soup.select_one('#ctl00_BodyPlaceHolder_lblBody > div > table:nth-child(14) > tbody > tr:nth-child(1) > td:nth-child(2)').text.strip()
        message_data['date_start'] = soup.select_one('#ctl00_BodyPlaceHolder_lblBody > div > table:nth-child(14) > tbody > tr:nth-child(2) > td:nth-child(2)').text.strip()
        try:
            message_data['place'] = soup.select_one('#ctl00_BodyPlaceHolder_lblBody > div > table:nth-child(14) > tbody > tr:nth-child(7) > td:nth-child(2)').text.strip()
        except:
            message_data['place'] = ''
        message_data['link'] = link

        # ---------- Получение данных по лотам из таблицы ----------
        rows = soup.select('.lotInfo > tbody:nth-child(1) > tr')
        for r in rows:
            lot_data = {}
            lot_data['message_number'] = message_data['message_number']
            lot_data['description'] = ''
            lot_data['type'] = ''
            lot_data['start_price'] = ''
            try:
                lot_data['description'] = r.select_one('td:nth-child(2)').text
            except:
                pass

            # ---------- Поиск кадастровых номеров и оборачивание в ссылки ----------
            # ToDo добить шаблоны
            try:
                lot_text = r.select_one('td:nth-child(2)').text
                matches = set(re.findall(r'\d{1,4}:\d{1,4}:\d+:\d{1,6}', lot_text))

                # print(matches)
                for m in matches:
                    # print(m)
                    lot_text = lot_text.replace(m, ' <a href="' + 'https://roskarta.com/map/' + m + '" target="_blank"> ' + m + '</a>')

                    # print(lot_text)
                    lot_data['description'] = lot_text
            except:
                pass
            try:
                lot_data['start_price'] = int(r.select_one('td:nth-child(3)').text.strip().split(',')[0].replace(' ', ''))
            except:
                pass

            message_data['lots'].append(lot_data)
        # ------------------------------------------------------------
        return message_data
    return False



def get_info(page):
    data = {'links': [], 'debtors': []}

    soup = BeautifulSoup(page, 'html.parser')

    links = soup.find_all('a', text=re.compile("Объявление о проведении торгов"))    # Ключевая фраза
    if links:
        for l in links:
            debtor_link = l.parent.nextSibling.find('a')
            debtor = {'name': debtor_link.text.strip(), 'link': base_url + debtor_link['href']}
            # print('Должник: {} | Ссылка: {}'.format(debtor['name'], debtor['link']))

            rawlink = l['onclick']
            link = base_url.replace('/', '') + rawlink.split('\'')[1]   # ппц, но пока пусть так
            data['links'].append(link)
            data['debtors'].append(debtor)
    return data


# ---------- НЕ ИСПОЛЬЗУЕТСЯ!!!!!!! Проверка ссылки на наличие ключевых слов ToDO удалить в конце проекта ----------
def check_link(link, keywords):
    html = asyncio.get_event_loop().run_until_complete(get_html(link, 2000))
    soup = BeautifulSoup(html, 'html.parser')
    lot_text = soup.find('div', class_='msg')

    for kw in keywords:
        if kw in soup.text:
            print('\033[92m' + 'Найдено: {}'.format(kw) + '\033[0m')
            # snils = soup.select_one('#ctl00_BodyPlaceHolder_lblBody > div > table:nth-child(6) > tbody > tr:nth-child(6) > td:nth-child(2)')
            # if snils:
            #     print('СНИЛС: {}'.format(snils.text))
            return html

    return False
# ///////////////////////////////////////////////////////////////////////////////////////////////////////


if __name__ == '__main__':
    main()
