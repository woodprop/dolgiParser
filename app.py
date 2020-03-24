from bs4 import BeautifulSoup
import re
import asyncio
from pyppeteer import launch
from db import LinkDB

base_url = 'http://bankrot.fedresurs.ru/'
base_url_mes = 'https://bankrot.fedresurs.ru/Messages.aspx'

def main():
    html = asyncio.get_event_loop().run_until_complete(set_date_period(base_url_mes, 3000))

    db = LinkDB()
    # db.insert('hlkgsdkgjksd')
    # db.get_all()
    # db.create_web()
    # return
    html = asyncio.get_event_loop().run_until_complete(get_html(base_url_mes, 2000))
    links = get_info(html)
    if not links:
        print('No links in response...')
        return

    for link in links:
        print(link)
        if check_link(link, 'квартира'):
            print('YES')
            db.insert(link)

    db.create_web()


async def set_date_period(url, delay):
    browser = await launch()
    page = await browser.newPage()

    await page.setViewport(viewport=dict(width=1920, height=4080))

    await page.goto(url)
    print('Loading page...')
    await page.waitFor(delay)

    await page.click('input[id="ctl00_cphBody_cldrBeginDate_tbSelectedDate"]')
    await page.keyboard.down('Control')
    await page.keyboard.press('KeyA')
    await page.keyboard.up('Control')
    await page.type('input[id="ctl00_cphBody_cldrBeginDate_tbSelectedDate"]', '04.02.2020')
    await page.click('input[id="ctl00_cphBody_cldrEndDate_tbSelectedDate"]')
    await page.keyboard.down('Control')
    await page.keyboard.press('KeyA')
    await page.keyboard.up('Control')
    await page.type('input[id="ctl00_cphBody_cldrEndDate_tbSelectedDate"]', '05.02.2020')
    await page.keyboard.press('Enter')

    await page.waitFor(5000)
    await page.screenshot({'path': 'example.png'})
    html = await page.content()
    soup = BeautifulSoup(html, 'html.parser')
    inp = soup.find('input', id='ctl00_cphBody_cldrBeginDate_tbSelectedDate')

    await browser.close()
    return html


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


def get_info(page):
    data = []
    soup = BeautifulSoup(page, 'html.parser')

    links = soup.find_all('a', text=re.compile("Объявление о проведении торгов"))    # Ключевая фраза

    if links:
        for l in links:
            # print(l)
            rawlink = l['onclick']
            link = base_url.replace('/', '') + rawlink.split('\'')[1]   # ппц, но пока пусть так
            data.append(link)
    return data


def check_link(link, keyword):
    html = asyncio.get_event_loop().run_until_complete(get_html(link, 2000))
    soup = BeautifulSoup(html, 'html.parser')
    lot_text = soup.find('div', class_='msg')

 #   return keyword in lot_text.text
    if 'здание' in lot_text.text:
        print('здание')
        return 1

  #  if 'жилое' in lot_text.text:
  #     print('жилое')
  #      return 2

    if 'помещение' in lot_text.text:
        print('помещение')
        return 3

    if 'квартира' in lot_text.text:
        print('квартира')
        return 4
    #
    # if 'hjjlh' in lot_text.text:
    #     return 32



if __name__ == '__main__':
    main()
