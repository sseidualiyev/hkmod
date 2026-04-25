# -*- coding: utf-8 -*-
# Hikka Bybit Price Tracker + Futures Calculator

import aiohttp
import asyncio
import math
from .. import loader, utils

@loader.tds
class BybitFutures(loader.Module):
    """Bybit price tracker + futures PnL & liquidation calculator"""

    strings = {"name": "BybitFutures"}

    def __init__(self):
        self._task = None
        self._prices = []

    # ---------- SYMBOL PARSER ----------
    def _parse_symbol(self, text: str):
        text = text.upper().replace("/", "").replace(" ", "")
        if not text.endswith("USDT"):
            text += "USDT"
        return text

    # ---------- BYBIT PRICE ----------
    async def _fetch_price(self, symbol: str):
        url = "https://api.bybit.com/v5/market/tickers"
        params = {
            "category": "linear",
            "symbol": symbol
        }

        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as r:
                data = await r.json()
                if data.get("retCode") != 0:
                    return None
                return data["result"]["list"][0]

    # ---------- GRAPH ----------
    def _sparkline(self, data, length=8):
        blocks = "▁▂▃▄▅▆▇█"
        if not data:
            return ""
        mn, mx = min(data), max(data)
        if mn == mx:
            return blocks[0] * min(len(data), length)
        return "".join(
            blocks[min(7, int((v - mn) / (mx - mn) * 7))]
            for v in data[-length:]
        )

    # ---------- PRICE ----------
    @loader.command()
    async def price(self, message):
        """<coin> — Bybit price"""
        raw = utils.get_args_raw(message)
        if not raw:
            return await message.edit("❌ Usage: <code>.price sol/usdt</code>")

        symbol = self._parse_symbol(raw)
        data = await self._fetch_price(symbol)
        if not data:
            return await message.edit("❌ Pair not found")

        price = float(data["lastPrice"])
        change = float(data["price24hPcnt"]) * 100

        base = symbol.replace("USDT", "")
        await message.edit(
            f"🪙 <b>{base}/USDT</b>\n"
            f"💵 Price: <b>{price}</b>\n"
            f"{'📈' if change >= 0 else '📉'} 24h: <b>{change:.2f}%</b>"
        )

    # ---------- TRACK ----------
    @loader.command()
    async def track(self, message):
        """<coin> <seconds> — live Bybit tracking"""
        args = utils.get_args(message)
        if len(args) < 2:
            return await message.edit("❌ Usage: <code>.track btc 30</code>")

        symbol = self._parse_symbol(args[0])
        interval = int(args[1])

        if self._task:
            self._task.cancel()

        self._prices = []

        async def runner():
            while True:
                data = await self._fetch_price(symbol)
                if not data:
                    await message.edit("❌ Fetch failed")
                    return

                price = float(data["lastPrice"])
                change = float(data["price24hPcnt"]) * 100
                self._prices.append(price)

                graph = self._sparkline(self._prices)
                base = symbol.replace("USDT", "")

                await message.edit(
                    f"🪙 <b>{base}/USDT</b>\n"
                    f"💵 <b>{price}</b>\n"
                    f"{'📈' if change >= 0 else '📉'} 24h: {change:.2f}%\n\n"
                    f"<code>{graph}</code>\n"
                    f"⏱ Every {interval}s"
                )
                await asyncio.sleep(interval)

        self._task = asyncio.create_task(runner())

    @loader.command()
    async def untrack(self, message):
        """Stop tracking"""
        if self._task:
            self._task.cancel()
            self._task = None
            await message.edit("✅ Tracking stopped")
        else:
            await message.edit("ℹ️ No active tracking")

    # ---------- FUTURES CALCULATIONS ----------
    def _calc(self, mode, lev, dep, entry, tp, sl=None):
        position = dep * lev

        if mode == "long":
            pnl = (tp - entry) / entry * position
            liq = entry * (1 - 1 / lev)
            sl_pnl = (sl - entry) / entry * position if sl else None
        else:
            pnl = (entry - tp) / entry * position
            liq = entry * (1 + 1 / lev)
            sl_pnl = (entry - sl) / entry * position if sl else None

        return pnl, liq, sl_pnl

    # ---------- LONG ----------
    @loader.command()
    async def long(self, message):
        """<lev> <deposit> <entry> <tp> [sl]"""
        args = utils.get_args(message)
        if len(args) < 4:
            return await message.edit(
                "❌ Usage:\n<code>.long 15 15 0.022389 0.01650</code>"
            )

        lev, dep, entry, tp = map(float, args[:4])
        sl = float(args[4]) if len(args) > 4 else None

        pnl, liq, sl_pnl = self._calc("long", lev, dep, entry, tp, sl)

        text = (
            f"📈 <b>LONG</b>\n"
            f"💰 Deposit: {dep}$\n"
            f"⚙️ Leverage: {lev}x\n"
            f"🎯 TP PnL: <b>{pnl:.2f}$</b>\n"
            f"☠️ Liquidation: <b>{liq:.6f}</b>\n"
        )

        if sl:
            text += f"🛑 SL PnL: {sl_pnl:.2f}$"

        await message.edit(text)

    # ---------- SHORT ----------
    @loader.command()
    async def short(self, message):
        """<lev> <deposit> <entry> <tp> [sl]"""
        args = utils.get_args(message)
        if len(args) < 4:
            return await message.edit(
                "❌ Usage:\n<code>.short 15 15 0.022389 0.01650</code>"
            )

        lev, dep, entry, tp = map(float, args[:4])
        sl = float(args[4]) if len(args) > 4 else None

        pnl, liq, sl_pnl = self._calc("short", lev, dep, entry, tp, sl)

        text = (
            f"📉 <b>SHORT</b>\n"
            f"💰 Deposit: {dep}$\n"
            f"⚙️ Leverage: {lev}x\n"
            f"🎯 TP PnL: <b>{pnl:.2f}$</b>\n"
            f"☠️ Liquidation: <b>{liq:.6f}</b>\n"
        )

        if sl:
            text += f"🛑 SL PnL: {sl_pnl:.2f}$"

        await message.edit(text)