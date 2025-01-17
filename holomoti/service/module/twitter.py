# ファンアートの検索モジュール
from holomoti.service.module.utils import PsqlBase
import reflex as rx
import math

PAGE_SIZE = 20


class TweetMedia(rx.Base):
    """ツイートのメディア"""

    tweetId: int = 0
    url: str = ""
    thumbnail: str = ""
    mediaType: str = ""


class TweetSearchState(rx.Base):
    """検索結果"""

    id: int = 0
    tweet: str = ""
    userId: str = ""
    userName: str = ""
    source: str = ""
    medias: list[TweetMedia] = []


def get_base_medias(ids: list[int]):
    ids_text = ",".join(str(x) for x in ids)
    query = f"""
    SELECT
        md.twitter_id as "tweetId",
        md.media_url as "url",
        md.thumbnail_url as "thumbnail",
        md.media_type as "mediaType"
    from holo.twitter_media as md
    where md.twitter_id in({ids_text}) 
    """
    model = PsqlBase()
    df = model.execute_df(query)
    return df


def get_medias(id: int) -> list[TweetMedia]:
    """ツイートのメディアを取得"""
    query = f"""
    SELECT
        md.twitter_id as "tweetId",
        md.media_url as "url",
        md.thumbnail_url as "thumbnail",
        md.media_type as "mediaType"
    from holo.twitter_media as md
    where md.twitter_id = {id}
    """
    model = PsqlBase()
    df = model.execute_df(query)
    results = []
    for _, row in df.iterrows():
        media = TweetMedia()
        media.tweetId = row["tweetId"]
        media.url = row["url"]
        media.thumbnail = row["thumbnail"]
        media.mediaType = row["mediaType"]
        results.append(media)

    return results


def search(text: str, page_no: int) -> list[TweetSearchState]:
    """ツイートを検索する。今は画像だけ。"""
    query = """
    SELECT
        tw.id as "id",
        tw.tweet_text as "tweet",
        max(us.screen_name) as "userId",
        max(us.name) as "userName",
        tw.tweet_url as "source"
    from 
        holo.twitter_tweet as tw
        LEFT JOIN holo.twitter_media as md on tw.id = md.twitter_id
        LEFT JOIN holo.twitter_hashtag as hs ON tw.id = hs.twitter_id
        LEFT JOIN holo.twitter_user as us ON tw.user_screen_name = us.screen_name
    where 
        md.media_type = 'image'
        AND 
        (
            tw.tweet_text like %(keyword)s
            OR hs.hashtag like %(keyword)s
            OR us.name like %(keyword)s
        )
    group by tw.id
    order by tw.created_at desc
    offset %(offset)s limit %(pagesize)s
    """
    args = {
        "keyword": f"%{text}%",
        "offset": max(page_no - 1, 0) * PAGE_SIZE,
        "pagesize": PAGE_SIZE,
    }
    model = PsqlBase()
    df = model.execute_df(query, args)
    ids = df["id"].astype(int).tolist()
    media_base_df = get_base_medias(ids)

    results = []
    for _, row in df.iterrows():
        tweet_state = TweetSearchState()
        tweet_state.id = row["id"]
        tweet_state.tweet = row["tweet"]
        tweet_state.userId = row["userId"]
        tweet_state.userName = row["userName"]
        tweet_state.source = row["source"]
        media_df = media_base_df[media_base_df["tweetId"] == row["id"]]
        media = []
        for _, mrow in media_df.iterrows():
            m = TweetMedia()
            m.tweetId = mrow["tweetId"]
            m.url = mrow["url"]
            m.thumbnail = mrow["thumbnail"]
            m.mediaType = mrow["mediaType"]
            media.append(m)
        # tweet_state.medias = get_medias(int(row["id"]))
        tweet_state.medias = media
        results.append(tweet_state)

    return results


def get_total_pages(text: str) -> int:
    # 総件数取得用クエリ
    query = """
    SELECT 
        COUNT(DISTINCT tw.id) as total
    FROM 
        holo.twitter_tweet as tw
        LEFT JOIN holo.twitter_media as md ON tw.id = md.twitter_id
        LEFT JOIN holo.twitter_hashtag as hs ON tw.id = hs.twitter_id
        LEFT JOIN holo.twitter_user as us ON tw.user_screen_name = us.screen_name
    WHERE 
        md.media_type = 'image'
        AND 
        (
            tw.tweet_text LIKE %(keyword)s
            OR hs.hashtag LIKE %(keyword)s
            OR us.name LIKE %(keyword)s
        )
    """

    args = {
        "keyword": f"%{text}%",
    }
    model = PsqlBase()
    df = model.execute_df(query, args)
    total_count = df["total"][0] if not df.empty else 0

    # 総ページ数計算（1ページあたりPAGE_SIZE件）
    total_pages = math.ceil(total_count / PAGE_SIZE) if total_count > 0 else 1
    return total_pages
