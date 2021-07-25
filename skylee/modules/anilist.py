
# Copyright (C) 2020-2021 DragSama. All rights reserved. Source code available under the AGPL.
#
# This file is part of AniFluidBot.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.

# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

# Uses Time Formatter from Uniborg: https://github.com/SpEcHiDe/UniBorg/blob/master/uniborg/utils.py

from telegram.ext.dispatcher import run_async
from telegram.ext import CommandHandler, CallbackContext
from telegram import Update, Bot
from telegram import ParseMode, InlineKeyboardMarkup, InlineKeyboardButton
from skylee import dispatcher, telethn
import requests
import math
import time
import telegraph
from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Update
from telethon import events


def shorten(description, info="anilist.co"):
    msg = ""
    if len(description) > 700:
        description = description[0:500] + "...."
        msg += f"\n*Description*: _{description}_[Read More]({info})"
    else:
        msg += f"\n*Description*:_{description}_"
    return (
        msg.replace("<br>", "")
        .replace("</br>", "")
        .replace("<i>", "")
        .replace("</i>", "")
    )



# Time formatter from Uniborg: https://github.com/SpEcHiDe/UniBorg/blob/master/uniborg/utils.py

def t(milliseconds: int) -> str:
    """Inputs time in milliseconds, to get beautified time,
    as string"""
    seconds, milliseconds = divmod(int(milliseconds), 1000)
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    days, hours = divmod(hours, 24)
    tmp = (
        ((str(days) + " Days, ") if days else "")
        + ((str(hours) + " Hours, ") if hours else "")
        + ((str(minutes) + " Minutes, ") if minutes else "")
        + ((str(seconds) + " Seconds, ") if seconds else "")
        + ((str(milliseconds) + " ms, ") if milliseconds else "")
    )
    return tmp[:-2]


airing_query = """
    query ($id: Int,$search: String) { 
      Media (id: $id, type: ANIME,search: $search) { 
        id
        episodes
        title {
          romaji
          english
          native
        }
        nextAiringEpisode {
           airingAt
           timeUntilAiring
           episode
        } 
      }
    }
    """

fav_query = """
query ($id: Int) { 
      Media (id: $id, type: ANIME) { 
        id
        title {
          romaji
          english
          native
        }
     }
}
"""

anime_query = """
   query ($id: Int,$search: String) { 
      Media (id: $id, type: ANIME,search: $search) { 
        id
        title {
          romaji
          english
          native
        }
        description (asHtml: false)
        startDate{
            year
          }
          episodes
          season
          type
          format
          status
          duration
          siteUrl
          studios{
              nodes{
                   name
              }
          }
          trailer{
               id
               site 
               thumbnail
          }
          averageScore
          genres
          bannerImage
      }
    }
"""
character_query = """
    query ($query: String) {
        Character (search: $query) {
               id
               name {
                     first
                     last
                     full
               }
               siteUrl
               image {
                        large
               }
               description
        }
    }
"""

manga_query = """
query ($id: Int,$search: String) { 
      Media (id: $id, type: MANGA,search: $search) { 
        id
        title {
          romaji
          english
          native
        }
        description (asHtml: false)
        startDate{
            year
          }
          type
          format
          status
          siteUrl
          averageScore
          genres
          bannerImage
      }
    }
"""


url = "https://graphql.anilist.co"


@run_async
def airing(update: Update, context: CallbackContext):
    message = update.effective_message
    search_str = message.text.split(" ", 1)
    if len(search_str) == 1:
        message.reply_text("Tell Anime Name :) ( /airing <anime name>)")
        return
    variables = {"search": search_str[1]}
    response = requests.post(
        url, json={"query": airing_query, "variables": variables}
    ).json()["data"]["Media"]
    msg = f"*Name*: *{response['title']['romaji']}*(`{response['title']['native']}`)\n*ID*: `{response['id']}`"
    if response["nextAiringEpisode"]:
        time = response["nextAiringEpisode"]["timeUntilAiring"] * 1000
        time = t(time)
        msg += f"\n*Episode*: `{response['nextAiringEpisode']['episode']}`\n*Airing In*: `{time}`"
    else:
        msg += f"\n*Episode*:{response['episodes']}\n*Status*: `N/A`"
    message.reply_text(msg, parse_mode=ParseMode.MARKDOWN)


@run_async
def anime(update: Update, context: CallbackContext):
    message = update.effective_message
    search = message.text.split(" ", 1)
    if len(search) == 1:
        return
    else:
        search = search[1]
    variables = {"search": search}
    json = (
        requests.post(url, json={"query": anime_query, "variables": variables})
        .json()["data"]
        .get("Media", None)
    )
    if json:
        msg = f"*{json['title']['romaji']}*(`{json['title']['native']}`)\n*Type*: {json['format']}\n*Status*: {json['status']}\n*Episodes*: {json.get('episodes', 'N/A')}\n*Duration*: {json.get('duration', 'N/A')} Per Ep.\n*Score*: {json['averageScore']}\n*Genres*: `"
        for x in json["genres"]:
            msg += f"{x}, "
        msg = msg[:-2] + "`\n"
        msg += "*Studios*: `"
        for x in json["studios"]["nodes"]:
            msg += f"{x['name']}, "
        msg = msg[:-2] + "`\n"
        info = json.get("siteUrl")
        trailer = json.get("trailer", None)
        anime_id = json["id"]
        if trailer:
            trailer_id = trailer.get("id", None)
            site = trailer.get("site", None)
            if site == "youtube":
                trailer = "https://youtu.be/" + trailer_id
        description = (
            json.get("description", "N/A")
            .replace("<i>", "")
            .replace("</i>", "")
            .replace("<br>", "")
        )
        msg += shorten(description, info)
        image = json.get("bannerImage", None)
        if trailer:
            buttons = [
                [
                    InlineKeyboardButton("More Info", url=info),
                    InlineKeyboardButton("Trailer 🎬", url=trailer),
                ],
                [
                    InlineKeyboardButton(
                        "Add to Favorites", callback_data=f"fav_({anime_id})"
                    )
                ],
            ]
        else:
            buttons = [
                [InlineKeyboardButton("More Info", url=info)],
                [
                    InlineKeyboardButton(
                        "Add to Favorites", callback_data=f"fav_({anime_id})"
                    )
                ],
            ]
        if image:
            try:
                message.reply_photo(
                    photo=image,
                    caption=msg,
                    parse_mode=ParseMode.MARKDOWN,
                    reply_markup=InlineKeyboardMarkup(buttons),
                )
            except:
                msg += f" [〽️]({image})"
                message.reply_text(
                    msg,
                    parse_mode=ParseMode.MARKDOWN,
                    reply_markup=InlineKeyboardMarkup(buttons),
                )
        else:
            message.reply_text(
                msg,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=InlineKeyboardMarkup(buttons),
            )


@run_async
def character(update: Update, context: CallbackContext):
    message = update.effective_message
    search = message.text.split(" ", 1)
    if len(search) == 1:
        message.reply_text("Format : /character < character name >")
        return
    search = search[1]
    variables = {"query": search}
    json = (
        requests.post(url, json={"query": character_query, "variables": variables})
        .json()["data"]
        .get("Character", None)
    )
    if json:
        msg = f"*{json.get('name').get('full')}*(`{json.get('name').get('native')}`)\n"
        description = f"{json['description']}"
        site_url = json.get("siteUrl")
        msg += shorten(description, site_url)
        image = json.get("image", None)
        if image:
            image = image.get("large")
            message.reply_photo(photo=image, caption=msg, parse_mode=ParseMode.MARKDOWN)
        else:
            message.reply_text(msg, parse_mode=ParseMode.MARKDOWN)


@run_async
def manga(update: Update, context: CallbackContext):
    message = update.effective_message
    search = message.text.split(" ", 1)
    if len(search) == 1:
        message.reply_text("Format : /manga < manga name >")
        return
    search = search[1]
    variables = {"search": search}
    json = (
        requests.post(url, json={"query": manga_query, "variables": variables})
        .json()["data"]
        .get("Media", None)
    )
    msg = ""
    if json:
        title, title_native = (
            json["title"].get("romaji", False),
            json["title"].get("native", False),
        )
        start_date, status, score = (
            json["startDate"].get("year", False),
            json.get("status", False),
            json.get("averageScore", False),
        )
        if title:
            msg += f"*{title}*"
            if title_native:
                msg += f"(`{title_native}`)"
        if start_date:
            msg += f"\n*Start Date* - `{start_date}`"
        if status:
            msg += f"\n*Status* - `{status}`"
        if score:
            msg += f"\n*Score* - `{score}`"
        msg += "\n*Genres* - "
        for x in json.get("genres", []):
            msg += f"{x}, "
        msg = msg[:-2]
        info = json["siteUrl"]
        buttons = [[InlineKeyboardButton("More Info", url=info)]]
        image = json.get("bannerImage", False)
        msg += f"_{json.get('description', None)}_"
        if image:
            try:
                message.reply_photo(
                    photo=image,
                    caption=msg,
                    parse_mode=ParseMode.MARKDOWN,
                    reply_markup=InlineKeyboardMarkup(buttons),
                )
            except:
                msg += f" [〽️]({image})"
                message.reply_text(
                    msg,
                    parse_mode=ParseMode.MARKDOWN,
                    reply_markup=InlineKeyboardMarkup(buttons),
                )
        else:
            message.reply_text(
                msg,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=InlineKeyboardMarkup(buttons),
            )


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

AIRING_HANDLER = CommandHandler("airing", airing)
ANIME_HANDLER = CommandHandler("anime", anime)
CHARACTER_HANDLER = CommandHandler("character", character)
MANGA_HANDLER = CommandHandler("manga", manga)
NHENTAI_HANDLER = nhentai, events.NewMessage(pattern="^[!/]nhentai$")

dispatcher.add_handler(AIRING_HANDLER)
dispatcher.add_handler(ANIME_HANDLER)
dispatcher.add_handler(MANGA_HANDLER)
dispatcher.add_handler(NHENTAI_HANDLER)
dispatcher.add_handler(CHARACTER_HANDLER)

telethn.add_event_handler(*NHENTAI_HANDLER)

__help__ = """
Get information about anime, manga or characters from [AniList](anilist.co) and [MyAnimeList](myanimelist.net).
*Available commands:*
 ~ `/anime` <anime>: returns information about the anime from Anilist.
 ~ `/character` <character>: returns information about the character from Anilist.
 ~ `/manga` <manga>: returns information about the manga from Anilist.
 ~ `/airing` <anime>: returns anime airing info.
 ~ `/nhentai` <ID>: returns information from nhentai in telegraph page.
 """
__mod_name__ = "Anime"
