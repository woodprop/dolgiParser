from bs4 import BeautifulSoup
import re
import asyncio
from pyppeteer import launch
from db import LinkDB

base_url = 'http://bankrot.fedresurs.ru'
base_url_mes = 'https://bankrot.fedresurs.ru/Messages.aspx'

def main():
    keywords = ['здание', 'помещение', 'квартира']
    html = asyncio.get_event_loop().run_until_complete(get_search_result_page(base_url_mes, 3000))
    # return
    db = LinkDB()
    # db.insert('hlkgsdkgjksd')
    # db.get_all()
    # db.create_web()
    # return
    # html = asyncio.get_event_loop().run_until_complete(get_html(base_url_mes, 2000))
    data = get_info(html)
    links = data['links']
    debtors = data['debtors']

    if not links:
        print('No links in response...')
        return

    print('\033[92m' + 'Начало проверки лотов...' + '\033[0m')
    for link in links:
        # print(link)
        lot = get_lot_info(link, keywords)
        if lot:
            db.add_lot(lot)

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

    return  # Страницу пока не делаем TODO

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
    await page.type('input[id="ctl00_cphBody_cldrBeginDate_tbSelectedDate"]', '01.03.2020')

    await page.click('input[id="ctl00_cphBody_cldrEndDate_tbSelectedDate"]')
    await page.keyboard.down('Control')
    await page.keyboard.press('KeyA')
    await page.keyboard.up('Control')
    await page.type('input[id="ctl00_cphBody_cldrEndDate_tbSelectedDate"]', '01.03.2020')

    await page.keyboard.press('Enter')
    print('Поиск...')
    await page.waitFor(5000)
    # await page.screenshot({'path': 'example.png'})
    html = await page.content()
    await browser.close()

    return html


# >>>>>>>>>> Не используется, но пока храним <<<<<<<<<<
async def get_html(url, delay):
    browser = await launch()
    page = await browser.newPage()
    await page.goto(url)
    print('Loading page...')
    await page.waitFor(delay)
    await page.screenshot({'path': 'example.png'})
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


def get_lot_info(link, keywords):
    html = asyncio.get_event_loop().run_until_complete(get_html(link, 2000))
    soup = BeautifulSoup(html, 'html.parser')
    lot_data = {}
    if '(изменено)' in soup.select_one('h1').text:
        print('Лот неактуальный')
        return False
    for kw in keywords:
        if kw in soup.text:
            print('\033[92m' + 'Найдено: {}'.format(kw) + '\033[0m')

            if 'ФИО' in soup.text:
                lot_data['inn'] = soup.select_one('#ctl00_BodyPlaceHolder_lblBody > div > table:nth-child(6) > tbody > tr:nth-child(5) > td:nth-child(2)').text.strip()
                lot_data['date_pub'] = soup.select_one('#ctl00_BodyPlaceHolder_lblBody > div > table:nth-child(2) > tbody > tr.odd > td:nth-child(2)').text.strip()
                lot_data['lot_number'] = soup.select_one('#ctl00_BodyPlaceHolder_lblBody > div > table:nth-child(2) > tbody > tr.even > td:nth-child(2)').text.strip()
                # lot_data['type'] = soup.select_one('').text.strip()
                # lot_data['address'] = soup.select_one('').text.strip()
            else:
                lot_data['inn'] = soup.select_one('#ctl00_BodyPlaceHolder_lblBody > div > table:nth-child(6) > tbody > tr:nth-child(4) > td:nth-child(2)').text.strip()
                lot_data['date_pub'] = soup.select_one('#ctl00_BodyPlaceHolder_lblBody > div > table:nth-child(2) > tbody > tr.odd > td:nth-child(2)').text.strip()
                lot_data['lot_number'] = soup.select_one('#ctl00_BodyPlaceHolder_lblBody > div > table:nth-child(2) > tbody > tr.even > td:nth-child(2)').text.strip()
                # lot_data['type'] = soup.select_one('').text.strip()
                # lot_data['address'] = soup.select_one('').text.strip()
            lot_data['type'] = ''
            lot_data['address'] = ''
            lot_data['description'] = soup.select('div.msg')[-2].text.strip()
            lot_data['start_price'] = soup.select_one('table.lotInfo > tbody > tr.odd > td:nth-child(3)').text.strip()
            lot_data['auction_type'] = soup.select_one('#ctl00_BodyPlaceHolder_lblBody > div > table:nth-child(14) > tbody > tr:nth-child(1) > td:nth-child(2)').text.strip()
            lot_data['date_start'] = soup.select_one('#ctl00_BodyPlaceHolder_lblBody > div > table:nth-child(14) > tbody > tr:nth-child(2) > td:nth-child(2)').text.strip()
            try:
                lot_data['place'] = soup.select_one('#ctl00_BodyPlaceHolder_lblBody > div > table:nth-child(14) > tbody > tr:nth-child(7) > td:nth-child(2)').text.strip()
            except:
                lot_data['place'] = ''
            lot_data['link'] = link

            return lot_data

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
