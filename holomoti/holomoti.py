import reflex as rx

from rxconfig import config
from holomoti.service import twitter_service
from holomoti.service.module.twitter import TweetSearchState


class State(rx.State):
    """The app state."""

    text: str = ""
    page_no: int = 1
    total_pages: int = 0
    records: list[TweetSearchState] = []
    is_loading: bool = False

    def set_text(self, text: str):
        self.text = text

    def on_search_click(self):
        self.is_loading = True
        self.records = twitter_service.search(self.text, self.page_no)
        self.total_pages = twitter_service.get_total_pages(self.text)
        self.is_loading = False


def tweet_card(state: TweetSearchState) -> rx.Component:
    return rx.box(rx.text(state.tweet))


def index() -> rx.Component:
    # Welcome Page (Index)
    return rx.container(
        rx.vstack(
            rx.heading("twitter検索", size="6"),
            rx.hstack(
                rx.input(placeholder="キーワード", on_change=State.set_text),
                rx.button(
                    "検索",
                    on_click=State.on_search_click,
                    cursor="pointer",
                ),
            ),
            rx.container(rx.foreach(State.records, tweet_card)),
            spacing="5",
            justify="start",
            min_height="100vh",
        ),
        background_image="url('https://hololive.hololivepro.com/wp-content/themes/hololive/images/fixed_bg.jpg')",
        background_size="cover",  # 画像を画面いっぱいに表示
        background_position="center",  # 画像の位置を中央に
        background_repeat="no-repeat",  # 画像の繰り返しを防止
    )


app = rx.App()
app.add_page(index)
