from bs4 import BeautifulSoup
import re
import asyncio
from pyppeteer import launch


base_url = 'http://bankrot.fedresurs.ru/'


def main():
    html = asyncio.get_event_loop().run_until_complete(get_html(base_url))
    links = get_info(html)
    for link in links:
        print(link)


async def get_html(url):
    browser = await launch()
    page = await browser.newPage()
    await page.goto(url)
    print('Loading page...')
    await page.waitFor(5000)
    # await page.screenshot({'path': 'example.png'})
    html = await page.content()
    await browser.close()
    return html


def get_info(page):
    data = []
    soup = BeautifulSoup(page, 'html.parser')

    links = soup.find_all('a', text=re.compile("Сообщение о судебном"))    # Ключевая фраза

    for l in links:
        # print(l)
        rawlink = l['onclick']
        link = base_url.replace('/', '') + rawlink.split('\'')[1]   # ппц, но пока пусть так
        data.append(link)
    return data


if __name__ == '__main__':
    main()
