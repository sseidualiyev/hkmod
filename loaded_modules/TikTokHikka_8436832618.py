# © damirTAG TikTok module wrapped for Hikka userbot
# Compatible with Hikka 1.x and 2.x

import asyncio
import aiohttp
import os
import re
import logging
import ffmpeg

from typing import Optional, Union, Literal, List, Dict
from dataclasses import dataclass, field
from tqdm.asyncio import tqdm
from .. import loader, utils


# ─────────────────────────────────────────────────────────────
#  Original TikTok client code (unchanged)
# ─────────────────────────────────────────────────────────────

@dataclass
class data:
    dir_name: str
    media: Union[str, List[str]]
    type: str

@dataclass
class metadata(data):
    metadata: Dict[str, Union[int, float]] = field(default_factory=dict)

    @property
    def height(self): return self.metadata.get('height')

    @property
    def width(self): return self.metadata.get('width')

    @property
    def duration(self): return self.metadata.get('duration')


class TikTok:
    def __init__(self, host: Optional[str] = None):
        self.headers = {
            'User-Agent':
                'Mozilla/5.0 (iPad; U; CPU OS 3_2 like Mac OS X; en-us)'
                ' AppleWebKit/531.21.10 (KHTML, like Gecko)'
                ' Version/4.0.4 Mobile/7B334b Safari/531.21.10'
        }
        self.host = host or "https://www.tikwm.com/"
        self.session = None

        self.data_endpoint = "api"
        self.search_videos_keyword_endpoint = "api/feed/search"
        self.search_videos_hashtag_endpoint = "api/challenge/search"

        self.logger = logging.getLogger("TikTok")
        self.logger.setLevel(logging.ERROR)

        self.result = None
        self.link = None

    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    @staticmethod
    def get_url(text: str) -> Optional[str]:
        urls = re.findall(r'https?://\S+', text)
        return urls[0] if urls else None

    async def _makerequest(self, endpoint: str, params: dict) -> dict:
        async with self.session.get(
            os.path.join(self.host, endpoint),
            params=params,
            headers=self.headers
        ) as response:
            response.raise_for_status()
            data = await response.json()
            return data.get("data", {})

    async def _ensure_data(self, link: str):
        if self.result is None or self.link != link:
            self.result = await self.fetch(link)
            self.link = link

    async def fetch(self, link: str):
        url = self.get_url(link)
        return await self._makerequest(self.data_endpoint, {"url": url, "hd": 1})

    async def _download_file(self, url: str, path: str):
        async with self.session.get(url) as response:
            response.raise_for_status()
            with open(path, "wb") as f:
                async for chunk in response.content.iter_any():
                    f.write(chunk)

    async def image(self, download_dir=None):
        download_dir = download_dir or self.result["id"]
        os.makedirs(download_dir, exist_ok=True)

        tasks = []
        for i, url in enumerate(self.result['images']):
            path = os.path.join(download_dir, f"image_{i+1}.jpg")
            tasks.append(self._download_file(url, path))

        await asyncio.gather(*tasks)

        return data(
            dir_name=download_dir,
            media=[os.path.join(download_dir, f"image_{i+1}.jpg")
                   for i in range(len(self.result['images']))],
            type="images"
        )

    def _get_video_dimensions(self, file):
        try:
            probe = ffmpeg.probe(file)
            video_stream = next(s for s in probe['streams']
                                if s['codec_type'] == 'video')
            return video_stream['width'], video_stream['height']
        except:
            return None, None

    async def video(self, filename=None, hd=False):
        url = self.result['hdplay'] if hd else self.result['play']
        filename = filename or f"tiktok_{self.result['id']}.mp4"

        async with self.session.get(url) as response:
            response.raise_for_status()
            with open(filename, "wb") as f:
                async for chunk in response.content.iter_any():
                    f.write(chunk)

        width, height = self._get_video_dimensions(filename)

        return metadata(
            dir_name=os.getcwd(),
            media=filename,
            type="video",
            metadata={
                "duration": self.result.get("duration"),
                "width": width,
                "height": height
            }
        )

    async def download(self, link, filename=None, hd=False):
        await self._ensure_data(link)

        if "images" in self.result:
            return await self.image(filename)

        return await self.video(filename, hd)


# ─────────────────────────────────────────────────────────────
#  Hikka wrapper module
# ─────────────────────────────────────────────────────────────

class TikTokHikka(loader.Module):
    """TikTok download module by damirTAG (wrapped for Hikka)"""

    strings = {"name": "TikTokHikka"}

    async def tiktokcmd(self, message):
        """
        .tiktok <link> — download TikTok video
        """
        link = utils.get_args_raw(message)
        if not link:
            return await message.reply("❌ Provide a TikTok link!")

        await message.edit("⏬ Downloading TikTok video...")

        async with TikTok() as tt:
            result = await tt.download(link)

        await message.reply(
            f"✔️ **Downloaded**\n"
            f"📁 File: `{result.media}`\n"
            f"📏 {result.metadata.get('width')}×{result.metadata.get('height')}"
        )

        await message.client.send_file(
            message.chat_id,
            result.media,
            reply_to=message.id
        )

    async def tiktokimgcmd(self, message):
        """
        .tiktokimg <link> — download TikTok images
        """
        link = utils.get_args_raw(message)
        if not link:
            return await message.reply("❌ Provide a TikTok link!")

        await message.edit("⏬ Downloading images...")

        async with TikTok() as tt:
            result = await tt.download(link)

        if result.type != "images":
            return await message.edit("❌ This TikTok is not a photo post.")

        for img in result.media:
            await message.client.send_file(message.chat_id, img, reply_to=message.id)

        await message.edit(f"✔️ Downloaded {len(result.media)} images.")

    async def tiksearchcmd(self, message):
        """
        .tiksearch <keyword> — search TikTok videos
        """
        keyword = utils.get_args_raw(message)
        if not keyword:
            return await message.reply("❌ Enter search keyword!")

        await message.edit(f"🔍 Searching TikTok for `{keyword}`...")

        async with TikTok() as tt:
            results = await tt.search("keyword", keyword)

        text = "\n".join(
            f"• {v.get('title','<no title>')}\n{v['play']}"
            for v in results[:10]
        )

        await message.edit("📄 **Search results:**\n\n" + text)


# Module ready for use in Hikka ✔️