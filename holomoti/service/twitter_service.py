# ファンアートの検索モジュール
from holomoti.service.module import twitter

def search(text:str, page_no:int) -> list[twitter.TweetSearchState]:
    return twitter.search(text, page_no)

def get_total_pages(text:str) -> int:
    return twitter.get_total_pages(text)