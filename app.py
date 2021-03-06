# -*- coding: utf-8 -*-

#  Licensed under the Apache License, Version 2.0 (the "License"); you may
#  not use this file except in compliance with the License. You may obtain
#  a copy of the License at
#
#       https://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#  WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#  License for the specific language governing permissions and limitations
#  under the License.

import os
import sys
import json
from argparse import ArgumentParser

from flask import Flask, request, abort
from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import (
    MessageEvent,
    FollowEvent,
    UnfollowEvent,
    TextMessage,
    TextSendMessage,
    StickerSendMessage,
    QuickReply,
    QuickReplyButton,
    MessageAction,
    RichMenu,
    RichMenuArea,
    RichMenuBounds,
    RichMenuSize,
    URIAction
)

app = Flask(__name__)

# get channel_secret and channel_access_token from your environment variable
channel_secret = os.getenv('LINE_CHANNEL_SECRET', None)
channel_access_token = os.getenv('LINE_CHANNEL_ACCESS_TOKEN', None)
if channel_secret is None:
    print('Specify LINE_CHANNEL_SECRET as environment variable.')
    sys.exit(1)
if channel_access_token is None:
    print('Specify LINE_CHANNEL_ACCESS_TOKEN as environment variable.')
    sys.exit(1)

line_bot_api = LineBotApi(channel_access_token)
handler = WebhookHandler(channel_secret)

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

def db_load(
    user_id: str,
    key: str,
) -> str:
    with open('db.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data[user_id][key]

def db_set(
    user_id: str,
    key: str,
    val: str,
) -> None:
    with open('db.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    data[user_id][key] = val
    with open('db.json', 'w', encoding='utf-8') as f:
        json.dump(data, f)

def db_add_user(
    user_id: str,
) -> None:
    with open('db.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    data[user_id] = {
        'lang': 'none'
    }
    with open('db.json', 'w', encoding='utf-8') as f:
        json.dump(data, f)

def db_del_user(
    user_id: str,
) -> None:
    with open('db.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    data.pop(user_id, None)
    with open('db.json', 'w', encoding='utf-8') as f:
        json.dump(data, f)

def set_rich_menu(event, language):
    line_bot_api.unlink_rich_menu_from_user(event.source.user_id)
    rich_menu_to_create = RichMenu(
        size=RichMenuSize(width=2500, height=833),
        selected=False,
        name="erina richmenu",
        chat_bar_text="Options" if language == "en" else "??????",
        areas=[
            RichMenuArea(
                bounds=RichMenuBounds(x=0, y=0, width=833, height=833),
                action=MessageAction(
                    text="Set Language" if language == "en" else '????????????')
            ),
            RichMenuArea(
                bounds=RichMenuBounds(x=833, y=0, width=833, height=833),
                action=MessageAction(
                    text="Internship Experience" if language == "en" else '????????????')
            ),
            RichMenuArea(
                bounds=RichMenuBounds(x=1666, y=0, width=834, height=833),
                action=MessageAction(
                    text="Lab" if language == "en" else '????????????')
            ),
        ]
    )
    rich_menu_id = line_bot_api.create_rich_menu(rich_menu=rich_menu_to_create)
    if language == "ch":
        with open("./rich-menu-formal-ch.png", 'rb') as f:
            line_bot_api.set_rich_menu_image(rich_menu_id, "image/png", f)
    else:
        with open("./rich-menu-formal-en.png", 'rb') as f:
            line_bot_api.set_rich_menu_image(rich_menu_id, "image/png", f)
    line_bot_api.link_rich_menu_to_user(event.source.user_id, rich_menu_id)

def language_quick_reply(event):
    db_set(
        user_id=event.source.user_id,
        key="lang",
        val="none"
    )
    return TextSendMessage(
        text='Language/??????', 
        quick_reply=QuickReply(
            items=[
                QuickReplyButton(action=MessageAction(label="English", text="English")),
                QuickReplyButton(action=MessageAction(label="??????", text="??????"))
            ]
        )
    )

@handler.add(FollowEvent)
def handle_follow(event):
    db_add_user(event.source.user_id)
    text_message = language_quick_reply(event)
    line_bot_api.reply_message(
        event.reply_token,
        text_message
    )
        
@handler.add(UnfollowEvent)
def handle_unfollow(event):
    db_del_user(event.source.user_id)

@handler.add(MessageEvent, message=TextMessage)
def message_text(event):
    lang = db_load(
        user_id=event.source.user_id,
        key="lang"
    )
    if lang == "none":
        if event.message.text == "??????":
            db_set(
                user_id=event.source.user_id,
                key="lang",
                val="ch",
            )
            text_message = TextSendMessage(text="?????????????????????????????????????????????????????????????????????????????????????????????")
            set_rich_menu(event, "ch")
        elif event.message.text == "English":
            db_set(
                user_id=event.source.user_id,
                key="lang",
                val="en",
            )
            text_message = TextSendMessage(text="Set language to English, \"Options\" will have my experiences and sending message will recieve my self introduction!")
            set_rich_menu(event, "en")
        else:
            text_message = TextSendMessage(text="Please select a language / ???????????????")
        
    else:
        if event.message.text in ["Set Language", "????????????"]:
            text_message = language_quick_reply(event)
        elif event.message.text == "????????????":
            text_message = TextSendMessage(text="????????????????????? Google ??? STEP intern???project ???????????????????????????????????????????????????????????????????????? C++???framework ??? Qt??????????????????????????????????????????????????? code ????????????????????????????????????????????????")
        elif event.message.text == "Internship Experience":
            text_message = TextSendMessage(text="I was a STEP intern at Google last summer vacation, the project is mainly about adding a new function to an internal existing tool. It is written in C++ and uses the framework Qt. I learned a lot about reading other people's code fast and ask for help when needed.")
        elif event.message.text == "????????????":
            text_message = TextSendMessage(text="????????????????????????????????? MiuLab????????? end-to-end spoken language understanding ??? survey ???????????????????????????????????????????????????????????????????????????anomaly detection on autonomous vehicle???????????????????????????????????????????????????????????? speech processing ???????????????????????????")
        elif event.message.text == "Lab":
            text_message = TextSendMessage(text="Last semester I was in prof. Yun-Nung Chen's MiuLab, surveying and experimenting on end-to-end spoken language understanding. This semester I join prof. Chung-Wei Lin's lab, studying anomaly detection on autonomous vehicle. Other than that, I am also in prof. Hung-Yi Lee's Lab, doing experiment on multiple topics related to speech processing.")
        else:
            emoji = [
                {
                    "index": 0,
                    "productId": "5ac22e85040ab15980c9b44f",
                    "emojiId": "065"
                }
            ]
            if lang == 'ch':
                text_message = TextSendMessage(text="$ ????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????", emojis=emoji)
            else:
                text_message = TextSendMessage(text="$ Hi, my name is Erina Wu, currently a junior in National Taiwan University, majoring in Computer Science and Information Engineering. In my free time, I like to exercise or play puzzle for relaxing, I am also a member of the puzzle club at school. Besides, I love desserts, baking them is also one of my favorite thing to do.", emojis=emoji)

    line_bot_api.reply_message(
        event.reply_token,
        text_message
    )

if __name__ == "__main__":
    arg_parser = ArgumentParser(
        usage='Usage: python ' + __file__ + ' [--port <port>] [--help]'
    )
    arg_parser.add_argument('-p', '--port', default=8000, help='port')
    arg_parser.add_argument('-d', '--debug', default=False, help='debug')
    arg_parser.add_argument('-a', '--allow_all', default=False, help='open to Internet')
    options = arg_parser.parse_args()

    with open('db.json', 'w', encoding='utf-8') as f:
        json.dump({}, f)

    app.secret_key = "alskjdalkq,wmnk208hdk?pl"
    app.run(
        debug=options.debug, 
        port=options.port,
        host='0.0.0.0' if options.allow_all else None
    )
