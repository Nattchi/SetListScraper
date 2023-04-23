import sqlite3

import boto3
import psycopg
import json
import os

import requests



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

class R2(DataBase):
    def __init__(self):
        # R2のアクセスキーとシークレットキー,アカウントIDを設定
        self.access_key = os.environ['AWS_ACCESS_KEY']
        self.secret_key = os.environ['AWS_SECRET_ACCESS_KEY']
        self.account_id = os.environ['AWS_ACCOUNT_ID']
        self.connection = DataBase.connection
        self.cursor = DataBase.cursor



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


def r2_upload(scraper, bucket_name=os.getenv('R2_BUCKET_NAME', ""), object_key=os.getenv('R2_OBJECT_KEY', "")):
    """
    :param scraper: Scraper object
    :param bucket_name: upload先のbucket
    :param object_key:  object_key
    :return: void
    """

    # R2のアクセスキーとシークレットキー,アカウントIDを設定
    access_key = os.environ['AWS_ACCESS_KEY']
    secret_key = os.environ['AWS_SECRET_ACCESS_KEY']
    account_id = os.environ['AWS_ACCOUNT_ID']

    # R2のエンドポイントURLを設定
    endpoint_url = f"https://{account_id}.r2.storageapi.net"

    # AWSの認証情報を設定
    # session = boto3.Session(
    #     aws_access_key_id=access_key,
    #     aws_secret_access_key=secret_key
    # )
    #
    # # Cloudflare R2のAPIエンドポイントを設定
    # cloudflare_r2 = session.client('r2',
    #                                region_name='ap-northeast-1',
    #                                endpoint_url=endpoint_url
    #                                )
    #

    # データをJSON形式に変換
    json_data = json.dumps(scraper.artist_info.__dict__)
    print("JSON\n" + json_data)


    if bucket_name == "":
        bucket_name = "setlist-bucket"
    if object_key == "":
        object_key = f"live_info/{scraper.artist_info.artist}"

    # # JSONデータをR2にアップロード
    # # s3.put_object(Bucket=bucket_name, Key=object_key, Body=json_data)
    # cloudflare_r2.get_waiter()

    response = boto3.client('s3').put_object(
        Body=json_data,
        Bucket=bucket_name,
        Key=f"{scraper.artist_info.artist}-setlist.json",
    )

    print("S3 Response\n" + response)
    # boto3.client('s3').put_object(Bucket=bucket_name, Key=object_key, Body=json_data)

