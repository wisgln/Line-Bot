from flask import Flask, request, abort

from linebot.v3 import WebhookHandler
from linebot.v3.exceptions import InvalidSignatureError
from linebot.v3.messaging import Configuration
from linebot.v3.webhooks import (
    MessageEvent,
    FollowEvent,
    PostbackEvent,
    TextMessageContent,
    LocationMessageContent
)

from config.settings import LINE_CHANNEL_SECRET, LINE_CHANNEL_ACCESS_TOKEN
from handlers.message_handler import handle_text_message
from handlers.postback_handler import handle_postback_event
from handlers.location_handler import handle_location_message

app = Flask(__name__)

configuration = Configuration(access_token=LINE_CHANNEL_ACCESS_TOKEN)
line_handler = WebhookHandler(LINE_CHANNEL_SECRET)


@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    try:
        line_handler.handle(body, signature)
    except InvalidSignatureError:
        app.logger.info("Invalid signature. Please check your channel access token/channel secret.")
        abort(400)

    return 'OK'


@line_handler.add(FollowEvent)
def handle_follow(event):
    print(f'Got {event.type} event')


@line_handler.add(MessageEvent, message=TextMessageContent)
def handle_message(event):
    handle_text_message(event, configuration)


@line_handler.add(PostbackEvent)
def handle_postback(event):
    handle_postback_event(event, configuration)


@line_handler.add(MessageEvent, message=LocationMessageContent)
def handle_location(event):
    handle_location_message(event, configuration)


if __name__ == "__main__":
    app.run()