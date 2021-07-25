
from telegram.ext.dispatcher import run_async
from telegram.ext import CommandHandler, CallbackContext
from telegram import Update, Bot
from telegram import ParseMode, InlineKeyboardMarkup, InlineKeyboardButton
from skylee import dispatcher, client
import requests
import math
import time
import telegraph
from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Update
from telethon import events

async def nhentai(_, message):
    if len(message.command) < 2:
        await message.delete()
        return
    query = message.text.split(None, 1)[1]
    title, tags, artist, total_pages, post_url, cover_image = nhentai_data(
        query)
    await message.reply_text(
        f"<code>{title}</code>\n\n<b>Tags:</b>\n{tags}\n<b>Artists:</b>\n{artist}\n<b>Pages:</b>\n{total_pages}",
        reply_markup=InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        "Read Here",
                        url=post_url
                    )
                ]
            ]
        )
    )

def nhentai_data(noombers):
    url = f"https://nhentai.net/api/gallery/{noombers}"
    res = requests.get(url).json()
    pages = res["images"]["pages"]
    info = res["tags"]
    title = res["title"]["english"]
    links = []
    tags = ""
    artist = ''
    total_pages = res['num_pages']
    extensions = {
        'j': 'jpg',
        'p': 'png',
        'g': 'gif'
    }
    for i, x in enumerate(pages):
        media_id = res["media_id"]
        temp = x['t']
        file = f"{i+1}.{extensions[temp]}"
        link = f"https://i.nhentai.net/galleries/{media_id}/{file}"
        links.append(link)

    for i in info:
        if i["type"] == "tag":
            tag = i['name']
            tag = tag.split(" ")
            tag = "_".join(tag)
            tags += f"#{tag} "
        if i["type"] == "artist":
            artist = f"{i['name']} "

    post_content = "".join(f"<img src={link}><br>" for link in links)

    post = telegraph.create_page(
        f"{title}",
        html_content=post_content,
        author_name="@Chizurumanagementbot",
        author_url="https://t.me/Chizurumanagementbot"
    )
    return title, tags, artist, total_pages, post['url'], links[0]
  
NHENTAI_HANDLER = nhentai, events.NewMessage(pattern="^[!/]nhentai$")
client.add_event_handler(*NHENTAI_HANDLER)
