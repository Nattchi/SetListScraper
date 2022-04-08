from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import time
import re
import random
from bs4 import BeautifulSoup

from database import *
from liveinfo import *
from artistinfo import *


def get_driver():
    driver_path = '/app/.chromedriver/bin/chromedriver'
    chrome_options = Options()
    # ここにuser_agentからランダムで読み込み
    # chrome_options.add_argument('--user-agent=' + self.user_agent)
    chrome_options.add_argument('--headless')  # driver のウィンドウを表示しない

    driver = webdriver.Chrome(
        options=chrome_options, executable_path=driver_path)
    driver.implicitly_wait(5)

    return driver


class Scraper:
    def __init__(self, artist):
        self.save_dir_path = "./results/"
        self.domain = 'https://www.livefans.jp'
        self.user_agent = get_user_agent()
        self.driver = get_driver()
        self.db = Postgresql()
        self.bs = self.get_bs4_object(self.domain)
        self.live_info = new_liveinfo_dict()
        self.artist_info = ArtistInfo(artist)
        self.result = dict()

    def renew_liveinfo(self):
        return {
            "live_title": self.live_info["live_title"],
            "title": self.live_info["title"],
            "date": self.live_info["date"],
            "place": self.live_info["place"],
            "url": self.live_info["url"],
            "setlist": self.live_info["setlist"],
        }

    def pager_crawl(self):
        spnext = self.bs.find("span", class_="next")

        while spnext is not None:
            anext = spnext.find(
                "a", attrs={"href": re.compile(r'search/index/page:\d(.)+$')})
            if anext is None:
                break
            self.append_liveinfo()
            nexturl = anext.get('href')
            self.bs = self.get_bs4_object(self.domain + nexturl)
            spnext = self.bs.find("span", class_="next")

        self.append_liveinfo()
        print(self.artist_info.event_url)
        print(self.artist_info.event_title)

    def append_liveinfo(self):
        # ライブ情報へのリンクを取得
        for info in self.bs.findAll("h3", class_="artistName"):
            for link in info.findAll("a", {"href": re.compile(r"events/\d+$")}):
                self.artist_info.event_url.append(link.get('href'))
                self.artist_info.event_title.append(link.get_text())
                # print(link.get_text())

    def get_taiban(self, url):
        self.bs = self.get_bs4_object(self.domain + url)
        taiban = self.bs.find("th", class_="taibanDate")
        return taiban

    def is_taiban(self, url):
        taiban = self.get_taiban(url)
        return taiban is not None

    def taiban(self, url):
        # 対バンページ用
        # taiban = bs.select_one('th.taibanDate')
        # TODO: Fesページ対応 https://www.livefans.jp/events/51403
        taiban = self.get_taiban(url)
        if taiban:
            for taiban_link in self.bs.section.findAll("a", {"href": re.compile(r"events/\d+$")}):
                # print(taiban_link.get('href'))

                self.live_info["place"] = self.bs.find(
                    "a", class_="icoPlace").get_text()
                self.live_info["date"] = self.bs.find(
                    "h2", class_="date").get_text()
                self.live_info["date"] = self.live_info["date"].replace(
                    self.live_info["place"], '')

                if taiban_link.get_text().casefold() == self.artist_info.artist.casefold():
                    print("対バンページ: ", taiban_link.get('href'))
                    link = taiban_link.get('href')
                    self.bs = self.get_bs4_object(self.domain + link)
                    break

    def get_bs4_object(self, link=None):
        if link is not None:
            self.driver.get(link)
        page_source = self.driver.page_source
        return BeautifulSoup(page_source, 'html.parser')

    def set_liveinfo(self):
        self.bs = self.get_bs4_object('https://www.livefans.jp/search?option=1&keyword=' + self.artist_info.artist
                                      + '&genre=all&setlist=on&setlist=1&sort=e2')
        self.artist_info.artist_url = self.domain + \
            "/artists/" + self.artist_info.artist
        self.get_artist_url()
        self.pager_crawl()
        dict.fromkeys(self.artist_info.event_url)
        self.get_liveinfo()

    def get_artist_url(self):
        # artist名, url取得
        match = False
        for artist_box in self.bs.findAll("div", class_="artistBox"):
            for url in artist_box.h3.findAll("a", {"href": re.compile(r"artists/\d+$")}):
                match = self.artist_info.artist == url.get_text()
                if match:
                    self.artist_info.artist = url.get_text()
                    self.artist_info.artist_url = url.get('href')
                    break
            if match:
                break

    def get_liveinfo(self):
        # ライブ情報を取得
        for idx, link in enumerate(self.artist_info.event_url):
            self.live_info = self.renew_liveinfo()
            self.live_info["title"] = self.artist_info.event_title[idx]
            self.live_info["url"] = link

            self.bs = self.get_bs4_object(self.domain + link)
            time.sleep(3)
            self.driver.set_page_load_timeout(3000)

            isTaiban = self.is_taiban(link)
            if isTaiban:
                self.get_taiban(link)
            else:
                try:
                    self.live_info["place"] = self.bs.find(
                        "address").find("a").get_text()
                    self.live_info["date"] = self.bs.find(
                        "p", class_="date").get_text()
                except Exception as e:
                    print(e)
                    continue

            isLoadInfo = self.load_info()
            if not isLoadInfo:
                continue
            time.sleep(3)
            self.bs = BeautifulSoup(self.driver.page_source, 'html.parser')
            # time.sleep(3)
            # self.get_bs4_object()
            self.set_setlist()
            self.artist_info.add_live_info(self.live_info)
            # self.artist_info[self.live_info["live_title"]] = self.live_info

        store_db(self)

    def load_info(self):
        isLoadInfo = False
        # セトリ編集ボタンをクリック
        for tticon in self.bs.findAll("p", class_="tticons"):
            content = tticon.get_text().rstrip()
            if not (not content or len(content) == 0):
                for edit in tticon.findAll("a", {"onclick": re.compile(r"^document.EditSetlist.submit().+$")}):
                    if edit:
                        self.driver.execute_script(
                            "document.EditSetlist.submit();")
                        # print("Clicked")
                        isLoadInfo = True
                        break
            if isLoadInfo:
                break

        return isLoadInfo

    def set_setlist(self):
        count = 0
        # print(self.live_info["title"], self.live_info["place"], self.live_info["date"])
        live_title = self.live_info["title"] + \
            self.live_info["place"] + self.live_info["date"]
        self.live_info["live_title"] = live_title

        setlist = dict()
        for song in self.bs.findAll("input", {"id": re.compile(r"^sl_song_name_.+$")}):
            count += 1
            setlist[count] = dict()
            if song['value'] != "":
                setlist[count]["tune_name"] = song['value']

        count = 0
        for artist in self.bs.findAll("input", {"id": re.compile(r"^sl_song_artist_name_.+$")}):
            count += 1
            if artist['value'] != "":
                setlist[count]["artist"] = artist['value']
            else:
                setlist[count]["artist"] = self.artist_info.artist

        self.live_info["setlist"] = setlist.copy()
        print(self.live_info["setlist"])


def get_user_agent():
    user_agent = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.169 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3626.121 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.157 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.113 Safari/537.36'
    ]
    return user_agent[random.randrange(0, len(user_agent), 1)]
