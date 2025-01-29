from pandas import DataFrame
import reflex as rx

from holomoti.pages.twitter_page import page as twitter


app = rx.App(
    style={
        "background_image": "url('https://hololive.hololivepro.com/wp-content/themes/hololive/images/fixed_bg.jpg')",
        "color": "black",
    },
)
app.add_page(twitter, title="ホロ餅 twitter", route="/")
