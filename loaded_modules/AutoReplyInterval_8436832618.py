from .. import loader, utils
import asyncio
import re

@loader.tds
class AutoReplyInterval(loader.Module):
    strings = {"name": "AutoReplyInterval"}

    async def client_ready(self, client, db):
        self.client = client
        self.db = db
        self.tasks = {}

    def get_data(self):
        return self.db.get("AutoReplyInterval", "data", {})

    def save_data(self, data):
        self.db.set("AutoReplyInterval", "data", data)

    async def autoreplycmd(self, message):
        args = utils.get_args_raw(message)

        match = re.match(r'"(.+?)"\s+(\d+)', args)
        if not match:
            await message.edit('Usage: .autoreply "text" minutes')
            return

        text = match.group(1)
        minutes = int(match.group(2))

        if minutes <= 0:
            await message.edit("Interval must be > 0")
            return

        reply = await message.get_reply_message()
        reply_id = reply.id if reply else None

        chat_id = str(message.chat_id)

        data = self.get_data()
        data[chat_id] = {
            "text": text,
            "interval": minutes,
            "reply_id": reply_id
        }
        self.save_data(data)

        if chat_id in self.tasks:
            self.tasks[chat_id].cancel()

        self.tasks[chat_id] = asyncio.create_task(
            self.loop_task(chat_id)
        )

        await message.edit(f"Started auto reply every {minutes} min")

    async def stopreplycmd(self, message):
        chat_id = str(message.chat_id)

        data = self.get_data()
        if chat_id in data:
            del data[chat_id]
            self.save_data(data)

        if chat_id in self.tasks:
            self.tasks[chat_id].cancel()
            del self.tasks[chat_id]

        await message.edit("Stopped auto reply")

    async def loop_task(self, chat_id):
        await asyncio.sleep(1)

        data = self.get_data()

        if chat_id not in data:
            return

        text = data[chat_id]["text"]
        interval = data[chat_id]["interval"]
        reply_id = data[chat_id]["reply_id"]

        while True:
            try:
                if reply_id:
                    await self.client.send_message(
                        int(chat_id),
                        text,
                        reply_to=reply_id
                    )
                else:
                    await self.client.send_message(
                        int(chat_id),
                        text
                    )

                await asyncio.sleep(interval * 60)

            except asyncio.CancelledError:
                break
            except Exception:
                await asyncio.sleep(interval * 60)