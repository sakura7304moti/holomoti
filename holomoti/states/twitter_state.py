from holomoti.service import twitter_service
from holomoti.service.module.twitter import TweetSearchState, TweetMedia
from holomoti.service.module.utils import HoloName, get_holo_names
import reflex as rx


class TwitterState(rx.State):
    """The app state."""

    text: str = ""
    like_count_text: str = "1000"
    like_count: int = 1000
    hashtag: str = ""
    page_no: int = 1
    total_pages: int = 0
    records: list[TweetSearchState] = []
    is_loading: bool = False
    holo_names: list[HoloName] = get_holo_names()

    def set_text(self, text: str):
        self.text = text

    def set_hashtag(self, hashtag: str):
        self.hashtag = hashtag

    def set_like_count(self, like_count: str):
        self.like_count_text = like_count
        self.like_count = int(like_count)

    def set_page(self, page: int):
        self.page_no = page

    def reset_pageno(self):
        self.page_no = 1

    def reset_hashtag(self):
        self.hashtag = ""

    def on_search_click(self):
        rx.console_log("search start")
        self.is_loading = True
        self.records = twitter_service.search(
            self.text, self.like_count, self.hashtag.replace("#", ""), self.page_no
        )
        self.total_pages = twitter_service.get_total_pages(
            self.text, self.like_count, self.hashtag.replace("#", "")
        )
        self.is_loading = False

    def on_prev_click(self):
        if self.page_no == 1:
            return
        self.page_no -= 1
        self.on_search_click()

    def on_next_click(self):
        if self.total_pages > self.page_no:
            self.page_no += 1
            self.on_search_click()

    def on_click_hashtag(self, hashtag: str):
        if self.text == hashtag:
            return
        self.text = hashtag
        self.page_no = 1
        self.on_search_click()
