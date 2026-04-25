# hikka_tiktok_auto_final.py

import re
import aiohttp
import tempfile
import os

from telethon.tl.types import DocumentAttributeVideo
from .. import loader, utils


TT_REGEX = r"(https?://(?:www\.)?tiktok\.com/[^\s]+)"
IG_REGEX = r"(https?://(?:www\.)?instagram\.com/[^\s]+)"


@loader.tds
class TikTokAutoMod(loader.Module):
    """Auto TikTok/Instagram downloader (REAL media fix)"""

    strings = {"name": "TTMediaFinal"}

    def __init__(self):
        self.config = loader.ModuleConfig(
            "chats",
            [],
            lambda: "Chats where enabled"
        )

    async def client_ready(self, client, db):
        self.client = client

    def extract_links(self, text):
        return re.findall(TT_REGEX, text) + re.findall(IG_REGEX, text)

    async def fetch(self, url):
        api = f"https://www.tikwm.com/api/?url={url}&hd=1"

        async with aiohttp.ClientSession() as session:
            async with session.get(api) as resp:
                data = await resp.json()

        return data.get("data", {})

    async def download_temp(self, url, filename):
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                if resp.status != 200:
                    return None

                path = os.path.join(tempfile.gettempdir(), filename)

                with open(path, "wb") as f:
                    f.write(await resp.read())

                return path

    async def enabledcmd(self, message):
        chat = utils.get_chat_id(message)
        chats = self.config["chats"]

        if chat in chats:
            chats.remove(chat)
            text = "❌ Выключено"
        else:
            chats.append(chat)
            text = "✅ Включено"

        self.config["chats"] = chats
        await utils.answer(message, text)

    async def watcher(self, message):
        if not message.text:
            return

        chat = utils.get_chat_id(message)
        if chat not in self.config["chats"]:
            return

        links = self.extract_links(message.text)
        if not links:
            return

        for link in links:
            try:
                data = await self.fetch(link)
            except:
                continue

            # 📸 IMAGES
            if "images" in data:
                for i, img in enumerate(data["images"]):
                    filename = f"image_{i}.jpg"
                    path = await self.download_temp(img, filename)

                    if not path:
                        continue

                    try:
                        await self.client.send_file(
                            message.chat_id,
                            path,
                            reply_to=message.id,
                            force_document=False
                        )
                    except:
                        pass

                    try:
                        os.remove(path)
                    except:
                        pass

            # 🎥 VIDEO (NO WATERMARK)
            if "play" in data:
                filename = "video.mp4"
                path = await self.download_temp(data["play"], filename)

                if not path:
                    continue

                try:
                    await self.client.send_file(
                        message.chat_id,
                        path,
                        reply_to=message.id,
                        attributes=[
                            DocumentAttributeVideo(
                                duration=0,
                                w=720,
                                h=1280,
                                supports_streaming=True
                            )
                        ],
                        force_document=False
                    )
                except:
                    pass

                try:
                    os.remove(path)
                except:
                    pass