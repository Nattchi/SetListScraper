#!/usr/bin/env python
import requests

from setlistscraper.database import *
from setlistscraper.scraper import Scraper

if __name__ == '__main__':
    db = SQLite3()
    # artists = db.get_artist()
    artists = ["プロジェクトセカイ"]

    for artist in artists:
        scraper = Scraper(artist)
        scraper.set_liveinfo()

        scraper.driver.close()
        scraper.driver.quit()
        scraper.db.connection.close()

    print("COMPLETED!!")
