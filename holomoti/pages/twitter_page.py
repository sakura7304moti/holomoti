from pandas import DataFrame
import reflex as rx

from rxconfig import config
from holomoti.service import twitter_service
from holomoti.service.module.twitter import TweetSearchState, TweetMedia
from holomoti.service.module.utils import HoloName, get_holo_names

from holomoti.states.twitter_state import TwitterState


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
                                    TwitterState.on_click_hashtag(t.text),
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


def page() -> rx.Component:
    # Twitterのページ
    return rx.container(
        rx.vstack(
            rx.heading("ファンアート検索", size="6", id="page_title"),
            rx.form.root(
                rx.flex(
                    rx.input(
                        placeholder="キーワード",
                        value=TwitterState.text,
                        on_change=TwitterState.set_text,
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
                                    TwitterState.holo_names,
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
                            TwitterState.hashtag != "",
                            rx.icon_button(
                                "circle-x",
                                color_scheme="gray",
                                on_click=TwitterState.reset_hashtag,
                            ),
                        ),
                        value=TwitterState.hashtag,
                        on_change=TwitterState.set_hashtag,
                    ),
                    rx.select(
                        ["100", "1000", "5000", "10000", "20000", "50000"],
                        value=TwitterState.like_count_text,
                        on_change=TwitterState.set_like_count,
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
                on_submit=[TwitterState.on_search_click, TwitterState.reset_pageno],
            ),
            rx.container(
                rx.foreach(TwitterState.records, tweet_card),
            ),
            rx.cond(
                TwitterState.total_pages > 1,
                rx.container(
                    rx.hstack(
                        rx.cond(
                            TwitterState.page_no > 1,
                            rx.icon(
                                "circle-arrow-left",
                                color_scheme="cyan",
                                size=40,
                                cursor="pointer",
                                on_click=[
                                    TwitterState.on_prev_click,
                                    rx.call_script(
                                        "document.getElementById('page_title').scrollIntoView()"
                                    ),
                                    rx.toast.success(
                                        f"ページ {TwitterState.page_no - 1} / {TwitterState.total_pages}",
                                        position="top-center",
                                    ),
                                ],
                            ),
                        ),
                        rx.text(
                            f"{TwitterState.page_no} / {TwitterState.total_pages}",
                            size="5",
                            padding_top="4px",
                        ),
                        rx.icon(
                            "circle-arrow-right",
                            color_scheme="cyan",
                            size=40,
                            cursor="pointer",
                            on_click=[
                                TwitterState.on_next_click,
                                rx.call_script(
                                    "document.getElementById('page_title').scrollIntoView()"
                                ),
                                rx.toast.success(
                                    f"ページ {TwitterState.page_no + 1} / {TwitterState.total_pages}",
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
        align_items="start",
        text_align="left",
    )
