# ファンアートの検索モジュール
from holomoti.service.module import twitter


def search(
    text: str, like_count: int, hashtag: str, page_no: int
) -> list[twitter.TweetSearchState]:
    return twitter.search(text, like_count, hashtag, page_no)


def get_total_pages(
    text: str,
    like_count: int,
    hashtag: str,
) -> int:
    return twitter.get_total_pages(text, like_count, hashtag)
