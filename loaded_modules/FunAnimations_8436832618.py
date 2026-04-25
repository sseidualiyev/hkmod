# -*- coding: utf-8 -*-
# FunAnimations — safe animated effects for Hikka

import asyncio
import random
from .. import loader, utils

@loader.tds
class FunAnimations(loader.Module):
    """Animated emoji & text effects (safe & stable)"""

    strings = {"name": "FunAnimations"}

    # ---------------- LAUGH ----------------
    @loader.command()
    async def laugh(self, message):
        """<number> — growing laugh 😂"""
        args = utils.get_args_raw(message)

        if not args.isdigit():
            return await message.edit("❌ <b>Usage:</b> <code>.laugh 10</code>")

        n = int(args)
        if not 1 <= n <= 50:
            return await message.edit("❌ Number must be between 1 and 50")

        text = ""
        for _ in range(n):
            text += "😂"
            await message.edit(text)
            await asyncio.sleep(1.1)

    # ---------------- TYPING ----------------
    @loader.command()
    async def typing(self, message):
        """<text> — typing effect"""
        text = utils.get_args_raw(message)

        if not text:
            return await message.edit("❌ <b>Usage:</b> <code>.typing hello</code>")

        out = ""
        for ch in text:
            out += ch
            await message.edit(utils.escape_html(out) + "▌")
            await asyncio.sleep(0.12)

        await message.edit(utils.escape_html(out))

    # ---------------- GLITCH ----------------
    @loader.command()
    async def glitch(self, message):
        """<text> — glitch effect (safe)"""
        text = utils.get_args_raw(message)

        if not text:
            return await message.edit("❌ <b>Usage:</b> <code>.glitch hello</code>")

        glitch_chars = "!@#$%^&*()_+=-~"
        base = list(text)

        for _ in range(6):
            frame = [
                random.choice(glitch_chars) if random.random() < 0.35 else c
                for c in base
            ]
            await message.edit(utils.escape_html("".join(frame)))
            await asyncio.sleep(0.25)

        # Stabilization phase
        for i in range(len(base)):
            frame = base[:i + 1] + [
                random.choice(glitch_chars)
                for _ in range(len(base) - i - 1)
            ]
            await message.edit(utils.escape_html("".join(frame)))
            await asyncio.sleep(0.15)

        # Final edit, only if changed
        final_text = utils.escape_html(text)
        if message.raw_text != final_text:
            await message.edit(final_text)


    # ---------------- COUNTDOWN ----------------
    @loader.command()
    async def countdown(self, message):
        """<number> — countdown animation"""
        args = utils.get_args_raw(message)

        if not args.isdigit():
            return await message.edit("❌ <b>Usage:</b> <code>.countdown 5</code>")

        n = int(args)
        if not 1 <= n <= 20:
            return await message.edit("❌ Number must be 1–20")

        for i in range(n, 0, -1):
            await message.edit(f"⏳ {i}")
            await asyncio.sleep(1)

        await message.edit("🚀 GO!")

    # ---------------- PULSE ----------------
    @loader.command()
    async def pulse(self, message):
        """<text> — pulsing animation"""
        text = utils.get_args_raw(message)

        if not text:
            return await message.edit("❌ <b>Usage:</b> <code>.pulse hello</code>")

        text = utils.escape_html(text)
        for _ in range(4):
            await message.edit(f"✨ {text} ✨")
            await asyncio.sleep(0.5)
            await message.edit(text)
            await asyncio.sleep(0.5)

    # ---------------- VANISH ----------------
    @loader.command()
    async def vanish(self, message):
        """<text> — appears then vanishes"""
        text = utils.get_args_raw(message)

        if not text:
            return await message.edit("❌ <b>Usage:</b> <code>.vanish hello</code>")

        await message.edit(utils.escape_html(text))
        await asyncio.sleep(2)
        await message.edit("​")  # invisible character