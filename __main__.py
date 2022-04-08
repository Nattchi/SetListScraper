#!/usr/bin/env python

from setlistscraper.database import Postgresql
from setlistscraper.scraper import Scraper

if __name__ == '__main__':
    db = Postgresql()
    artists = db.get_artist()

    for artist in artists:
        scraper = Scraper(artist)
        scraper.set_liveinfo()

        scraper.driver.close()
        scraper.driver.quit()
        scraper.db.connection.close()

    print("COMPLETED!!")
