from bs4 import BeautifulSoup
import re
import asyncio
from pyppeteer import launch
from db import LinkDB

base_url = 'http://bankrot.fedresurs.ru/'
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
    links = get_info(html)
    if not links:
        print('No links in response...')
        return

    for link in links:
        print(link)
        if check_link(link, keywords):
            db.insert(link)

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
    # await page.screenshot({'path': 'example.png'})
    html = await page.content()
    await browser.close()
    return html
# ////////////////////////////////////////////////////////


def get_info(page):
    data = []
    soup = BeautifulSoup(page, 'html.parser')
    links = soup.find_all('a', text=re.compile("Объявление о проведении торгов"))    # Ключевая фраза

    if links:
        for l in links:
            rawlink = l['onclick']
            link = base_url.replace('/', '') + rawlink.split('\'')[1]   # ппц, но пока пусть так
            data.append(link)
    return data


# ---------- Проверка ссылки на наличие ключевых слов ----------
def check_link(link, keywords):
    html = asyncio.get_event_loop().run_until_complete(get_html(link, 2000))
    soup = BeautifulSoup(html, 'html.parser')
    lot_text = soup.find('div', class_='msg')

    for kw in keywords:
        if kw in soup.text:
            print('Найдено: {}'.format(kw))
            snils = soup.select_one('#ctl00_BodyPlaceHolder_lblBody > div > table:nth-child(6) > tbody > tr:nth-child(6) > td:nth-child(2)')
            if snils:
                print('СНИЛС: {}'.format(snils.text))
            return True

    return False
# ///////////////////////////////////////////////////////////////////////////////////////////////////////

if __name__ == '__main__':
    main()
