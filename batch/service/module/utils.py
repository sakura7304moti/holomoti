import os
import psycopg2
import datetime
import pandas as pd
from sqlalchemy import create_engine
from urllib.parse import urlparse


class Option:
    def root_path(self):
        """
        Batchのルートのパス
        """
        path = os.path.abspath(__file__)
        for _ in range(3):
            path = os.path.dirname(path)
        return path

    def option_path(self):
        return os.path.join(self.root_path(), "option")

    def holo_names(self):
        return os.path.join(self.option_path(), "holo_names.csv")


class PsqlBase:
    def __init__(self):
        # スキーマ作成処理
        self.execute_commit("CREATE SCHEMA IF NOT EXISTS holo")

        # テーブル作成処理
        twitter_table = """
            CREATE TABLE IF NOT EXISTS holo.twitter_tweet (
                id int8 NOT NULL,
                tweet_text text,
                tweet_url text,
                like_count int4,
                user_screen_name text,
                created_at timestamptz,
                PRIMARY KEY (id)
            );
        """
        hashtag_table = """
        CREATE TABLE IF NOT EXISTS holo.twitter_hashtag (
            twitter_id int8 NOT NULL,
            hashtag text,
            CONSTRAINT twitter_hashtag_twitter_id_fkey FOREIGN KEY (twitter_id) REFERENCES holo.twitter_tweet(id)
        );
        """
        media_table = """
        CREATE TABLE IF NOT EXISTS holo.twitter_media (
            twitter_id int8 NOT NULL,
            media_type text,
            media_url text,
            thumbnail_url text,
            CONSTRAINT twitter_media_twitter_id_fkey FOREIGN KEY (twitter_id) REFERENCES holo.twitter_tweet(id)
        );
        """
        user_table = """
        CREATE TABLE IF NOT EXISTS holo.twitter_user (
            screen_name text,
            name text,
            profile_image text,
            updated_at timestamptz
        );
        """
        self.execute_commit(twitter_table)
        self.execute_commit(hashtag_table)
        self.execute_commit(media_table)
        self.execute_commit(user_table)

    def db_url(self):
        """
        接続URL
        """
        return "postgresql+psycopg2://sakura0moti:music0@192.168.11.31/holomoti"

    def db_pd_connection(self):
        """
        read_sql用の接続情報
        """
        return create_engine(self.db_url())

    def db_psql_connection(self):
        """
        コミット用の接続情報
        """
        url = self.db_url()
        # URLを解析
        parsed_url = urlparse(url)

        # 必要な情報を取得
        username = parsed_url.username
        password = parsed_url.password
        hostname = parsed_url.hostname
        db_name = parsed_url.path[1:]
        return psycopg2.connect(
            host=hostname, dbname=db_name, user=username, password=password
        )

    def execute_commit(self, query: str, param: dict | None = None):
        """
        クエリを実行するだけ。commitが必要な場合はこっち。
        """
        with self.db_psql_connection() as con:
            cur = con.cursor()
            if param is None:
                cur.execute(query)
            else:
                cur.execute(query, param)

            con.commit()

    def execute_df(self, query: str, param: dict | None = None):
        """
        クエリを実行してデータフレームを取得
        """
        if param is None:
            return pd.read_sql(sql=query, con=self.db_pd_connection())
        else:
            return pd.read_sql(sql=query, con=self.db_pd_connection(), params=param)

    def current_time(self):
        """
        現在の日時を取得。
        create_atやupdate_atの日時セットに。
        """
        return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
