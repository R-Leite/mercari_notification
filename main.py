#!/usr/local/bin/python3.6

from flask import Flask, request, abort

from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage, ImageSendMessage
)
import re
import os
import time
import json
import picamera
from datetime import datetime
from PIL import Image
import sys
sys.path.append("./src")

import conf as conf

app = Flask(__name__)

# environment
YOUR_CHANNEL_ACCESS_TOKEN = os.environ["YOUR_CHANNEL_ACCESS_TOKEN"]
YOUR_CHANNEL_SECRET = os.environ["YOUR_CHANNEL_SECRET"]

handler = WebhookHandler(YOUR_CHANNEL_SECRET)

@app.route("/callback", methods=['POST'])
def callback():
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']

    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    # handle webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return 'OK'

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):

    # receive message
    m = event.message.text

    # time
    pat1 = "なんじ"
    pat2 = "何時"
    if re.search(pat1, m) or re.search(pat2, m):
        msg = TextSendMessage(text="現在の時刻は {} です".format(datetime.now().strftime("%Y/%m/%d %H:%M:%S")))
        conf.line_bot_api.reply_message(event.reply_token, msg)


if __name__ == "__main__":
#    app.run()
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
