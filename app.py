from bs4 import BeautifulSoup
import re
import asyncio
from pyppeteer import launch


base_url = 'http://bankrot.fedresurs.ru/'


def main():
    html = asyncio.get_event_loop().run_until_complete(get_html(base_url, 5000))
    links = get_info(html)
    if not links:
        print('No links in response...')
        return

    for link in links:
        print(link)
        if check_link(link, 'Васенко'):
            print('YES')




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

    links = soup.find_all('a', text=re.compile("Уведомление"))    # Ключевая фраза

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

    return keyword in lot_text.text




if __name__ == '__main__':
    main()
