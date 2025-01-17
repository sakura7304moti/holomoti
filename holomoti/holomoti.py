import reflex as rx

from rxconfig import config
from holomoti.service import twitter_service
from holomoti.service.module.twitter import TweetSearchState, TweetMedia


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
            rx.vstack(rx.text(state.tweet), image_card(state.medias)),
        ),
        margin_bottom="16px",
    )


def index() -> rx.Component:
    # Welcome Page (Index)
    return rx.container(
        rx.vstack(
            rx.heading("twitter検索", size="6"),
            rx.form.root(
                rx.hstack(
                    rx.input(placeholder="キーワード", on_change=State.set_text),
                    rx.button("検索", cursor="pointer", type="submit"),
                ),
                on_submit=State.on_search_click,
            ),
            rx.container(rx.foreach(State.records, tweet_card)),
            spacing="5",
            justify="start",
            min_height="100vh",
        ),
        background_image="url('https://hololive.hololivepro.com/wp-content/themes/hololive/images/fixed_bg.jpg')",
    )


app = rx.App()
app.add_page(index)
