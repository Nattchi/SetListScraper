import sqlite3
import psycopg
import json
import os


class DataBase(object):
    connection = None
    cursor = None


class Postgresql(DataBase):
    def __init__(self):
        self.dbhost = os.environ['DBHOST']
        self.dbport = os.environ['DBPORT']
        self.dbname = os.environ['DBNAME']
        self.dbuser = os.environ['DBUSER']
        self.dbpw = os.environ['DBPW']

        if DataBase.connection is None:
            try:
                DataBase.connection = psycopg.connect(
                    f"host={self.dbhost} post={self.port} dbname={self.dbname} user={self.dbuser} password={self.dbpw}")
                DataBase.cursor = DataBase.connection.cursor()
            except Exception as error:
                print(f"Error: Connection is not established {error}")
            else:
                print("Connection established.")

        self.connection = DataBase.connection
        self.cursor = DataBase.cursor

    def get_artist(self):
        return self.cursor.execute(f'''SELECT schemaname, tablename, tableowner FROM pg_tables
        WHERE schemaname not like 'pg_%' and schemaname != 'information_schema';''')


class SQLite3(DataBase):
    def __init__(self, filepath_sqlite3="db.sqlite3"):
        if DataBase.connection is None:
            try:
                DataBase.connection = sqlite3.connect(filepath_sqlite3)
                DataBase.cursor = DataBase.connection.cursor()
            except Exception as error:
                print(f"Error: Connection is not established {error}")
            else:
                print("Connection established.")
        self.connection = DataBase.connection
        self.cursor = DataBase.cursor

    # def __del__(self):
    #     self.connection.close()


def store_db(scraper):
    print(scraper.artist_info.live_info_dict)
    scraper.db.cursor.execute(
        f'DROP TABLE IF EXISTS {scraper.artist_info.artist}')
    # Create table
    scraper.db.cursor.execute(f'''CREATE TABLE {scraper.artist_info.artist}
    (setlist_id integer not null PRIMARY KEY AUTOINCREMENT, live_title TEXT,artist_url TEXT, title TEXT, date TEXT,
    place TEXT, url TEXT, setlist TEXT)''')

    # Insert a row of data
    count = 1
    for result in scraper.artist_info.live_info_dict.values():
        # print(json.dumps(result['setlist']))
        scraper.db.cursor.execute(f'INSERT INTO {scraper.artist_info.artist} VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
                                  ([count, result['live_title'],
                                    scraper.artist_info.artist_url,
                                    result['title'],
                                    result['date'],
                                    result['place'],
                                    result['url'],
                                    json.dumps(
                                        result['setlist'])]))
        count += 1
    # Save (commit) the changes
    scraper.db.connection.commit()


def update_db(scraper):
    event_url = scraper.db.cursor.execute(
        f'''SELECT url FROM {scraper.artist_info.artist}''').fetchall()
    print(set(event_url))
