import datetime
from urllib.parse import urlparse
import pandas as pd
import psycopg2
from sqlalchemy import create_engine
from batch.service.module import utils as batch_utils
import reflex as rx


def get_holo_names():
    opt = batch_utils.Option()
    df = pd.read_csv(opt.holo_names())
    records = []
    for _, row in df.iterrows():
        m = HoloName()
        m.name = row["name"]
        m.hashtag = row["hashtag"]
        m.url = row["url"]
        records.append(m)
    return records


class HoloName(rx.Base):
    name: str = ""
    hashtag: str = ""
    url: str = ""


class PsqlBase:
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
