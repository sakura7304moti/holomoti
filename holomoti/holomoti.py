from pandas import DataFrame
import reflex as rx

from rxconfig import config
from holomoti.service import twitter_service
from holomoti.service.module.twitter import TweetSearchState, TweetMedia
from holomoti.service.module.utils import HoloName, get_holo_names


class State(rx.State):
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


def image_card(medias: list[TweetMedia]):
    return rx.vstack(
        rx.foreach(
            medias,
            lambda m: rx.image(
                src=m.url,
                max_width="700px",
                width="100%",
                max_height="70vh",
                height="100%",
                object_fit="contain",
                object_position="center",
            ),
        )
    )


def tweet_card(state: TweetSearchState) -> rx.Component:
    return rx.box(
        rx.hstack(
            rx.avatar(src=state.userIcon),
            rx.vstack(
                rx.flex(
                    rx.foreach(
                        state.tweet_split,
                        lambda t: rx.cond(
                            t.type == "hashtag",
                            rx.text(
                                t.text,
                                color_scheme="blue",
                                cursor="pointer",
                                margin="0 4px",
                                _hover={"color": "orange", "transition": "0.5s"},
                                on_click=[
                                    State.on_click_hashtag(t.text),
                                    rx.call_script(
                                        "document.getElementById('page_title').scrollIntoView()"
                                    ),
                                    rx.toast.success(
                                        f"キーワード : {t.text}",
                                        position="top-center",
                                    ),
                                ],
                            ),
                            rx.text(t.text),
                        ),
                    ),
                    flex_wrap="wrap",
                ),
                image_card(state.medias),
            ),
        ),
        margin_bottom="24px",
    )


def index() -> rx.Component:
    # Welcome Page (Index)
    return rx.container(
        rx.vstack(
            rx.heading("ファンアート検索", size="6", id="page_title"),
            rx.form.root(
                rx.flex(
                    rx.input(
                        placeholder="キーワード",
                        value=State.text,
                        on_change=State.set_text,
                        width="150px",
                    ),
                    rx.select.root(
                        rx.select.trigger(
                            placeholder="ハッシュタグ",
                            width="150px",
                        ),
                        rx.select.content(
                            rx.select.group(
                                rx.foreach(
                                    State.holo_names,
                                    lambda s: rx.select.item(
                                        rx.hstack(
                                            rx.avatar(src=s.url, size="2"),
                                            rx.text(
                                                s.hashtag,
                                                color_scheme="gray",
                                                size="4",
                                                weight="light",
                                            ),
                                            margin_top="8px",
                                        ),
                                        rx.divider(
                                            width="250px",
                                            margin_bottom="4px",
                                        ),
                                        value=s.hashtag,
                                        height="40px",
                                        cursor="pointer",
                                        _hover={
                                            "background_color": rx.color("blue", 3)
                                        },
                                        style={"[data-selected]": {"height": "10px"}},
                                    ),
                                )
                            ),
                        ),
                        rx.cond(
                            State.hashtag != "",
                            rx.icon_button(
                                "circle-x",
                                color_scheme="gray",
                                on_click=State.reset_hashtag,
                            ),
                        ),
                        value=State.hashtag,
                        on_change=State.set_hashtag,
                    ),
                    rx.select(
                        ["100", "1000", "5000", "10000", "20000", "50000"],
                        value=State.like_count_text,
                        on_change=State.set_like_count,
                        placeholder="♡",
                    ),
                    rx.button(
                        "検索",
                        rx.icon("search", size=20, stroke_width=1.8),
                        cursor="pointer",
                        type="submit",
                        id="search_btn",
                    ),
                    wrap="wrap",
                    spacing="4",
                ),
                on_submit=[State.on_search_click, State.reset_pageno],
            ),
            rx.container(
                rx.foreach(State.records, tweet_card),
            ),
            rx.cond(
                State.total_pages > 1,
                rx.container(
                    rx.hstack(
                        rx.cond(
                            State.page_no > 1,
                            rx.icon(
                                "circle-arrow-left",
                                color_scheme="cyan",
                                size=40,
                                cursor="pointer",
                                on_click=[
                                    State.on_prev_click,
                                    rx.call_script(
                                        "document.getElementById('page_title').scrollIntoView()"
                                    ),
                                    rx.toast.success(
                                        f"ページ {State.page_no - 1} / {State.total_pages}",
                                        position="top-center",
                                    ),
                                ],
                            ),
                        ),
                        rx.text(
                            f"{State.page_no} / {State.total_pages}",
                            size="5",
                            padding_top="4px",
                        ),
                        rx.icon(
                            "circle-arrow-right",
                            color_scheme="cyan",
                            size=40,
                            cursor="pointer",
                            on_click=[
                                State.on_next_click,
                                rx.call_script(
                                    "document.getElementById('page_title').scrollIntoView()"
                                ),
                                rx.toast.success(
                                    f"ページ {State.page_no + 1} / {State.total_pages}",
                                    position="top-center",
                                ),
                            ],
                        ),
                    ),
                    border="1px solid",
                    border_radius="20px",
                    max_height="80px",
                ),
            ),
            spacing="5",
            justify="start",
            align_items="start",
            min_height="100vh",
        ),
        background_image="url('https://hololive.hololivepro.com/wp-content/themes/hololive/images/fixed_bg.jpg')",
        align_items="start",
        text_align="left",
    )


app = rx.App()
app.add_page(index, title="ホロ餅 twitter")
