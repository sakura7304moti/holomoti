import time
import reflex as rx

from rxconfig import config
from holomoti.service import twitter_service
from holomoti.service.module.twitter import TweetSearchState, TweetMedia


class State(rx.State):
    """The app state."""

    text: str = ""
    like_count_text: str = "100"
    like_count: int = 100
    page_no: int = 1
    total_pages: int = 0
    records: list[TweetSearchState] = []
    is_loading: bool = False

    def set_text(self, text: str):
        self.text = text

    def set_like_count(self, like_count: str):
        self.like_count_text = like_count
        self.like_count = int(like_count)

    def set_page(self, page: int):
        self.page_no = page

    def on_search_click(self):
        self.is_loading = True
        self.records = twitter_service.search(self.text, self.like_count, self.page_no)
        self.total_pages = twitter_service.get_total_pages(self.text, self.like_count)
        self.is_loading = False

    def on_click_hashtag(self, hashtag: str):
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
                                on_click=State.on_click_hashtag(t.text),
                            ),
                            rx.text(t.text),
                        ),
                    ),
                    flex_wrap="wrap",
                ),
                image_card(state.medias),
            ),
        ),
        margin_bottom="16px",
    )


def index() -> rx.Component:
    # Welcome Page (Index)
    return rx.container(
        rx.vstack(
            rx.heading("ファンアート検索", size="6"),
            rx.form.root(
                rx.hstack(
                    rx.input(
                        placeholder="キーワード",
                        value=State.text,
                        on_change=State.set_text,
                    ),
                    rx.select(
                        ["100", "1000", "5000", "10000", "20000", "50000"],
                        value=State.like_count_text,
                        on_change=State.set_like_count,
                        placeholder="♡",
                    ),
                    rx.button("検索", cursor="pointer", type="submit"),
                ),
                on_submit=State.on_search_click,
            ),
            rx.container(rx.foreach(State.records, tweet_card)),
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
