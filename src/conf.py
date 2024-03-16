import os
from linebot import LineBotApi

YOUR_CHANNEL_ACCESS_TOKEN = os.environ["MERCARI_CHANNEL_ACCESS_TOKEN"]
line_bot_api = LineBotApi(YOUR_CHANNEL_ACCESS_TOKEN)

# user id
tomo_id = os.environ["TID"]
hide_id = os.environ["HID"]

# Webhook URL
URL = "https://okihid.serveo.net/static/"

# capture size
WIDTH = 1920
HEIGHT = 1080
PREV_WIDTH = 240
PREV_HEIGHT = 240
