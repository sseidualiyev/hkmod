from .. import loader, utils
import os
import shutil

@loader.tds
class PlaylistManager(loader.Module):
    """Local Playlist Manager"""

    strings = {
        "name": "PlaylistManager"
    }

    async def client_ready(self, client, db):
        self.client = client
        self.db = db
        self.base_path = "playlists"
        os.makedirs(self.base_path, exist_ok=True)

    def get_playlists(self):
        return self.db.get("PlaylistManager", "playlists", {})

    def save_playlists(self, data):
        self.db.set("PlaylistManager", "playlists", data)

    async def plcreatecmd(self, message):
        name = utils.get_args_raw(message)
        if not name:
            await message.edit("Provide playlist name")
            return

        playlists = self.get_playlists()
        if name in playlists:
            await message.edit("Playlist already exists")
            return

        playlists[name] = []
        self.save_playlists(playlists)

        os.makedirs(os.path.join(self.base_path, name), exist_ok=True)
        await message.edit(f"Playlist '{name}' created")

    async def pladdcmd(self, message):
        name = utils.get_args_raw(message)
        reply = await message.get_reply_message()

        if not name or not reply or not reply.audio:
            await message.edit("Reply to an audio file and specify playlist name")
            return

        playlists = self.get_playlists()
        if name not in playlists:
            await message.edit("Playlist not found")
            return

        file_path = await reply.download_media(file=os.path.join(self.base_path, name))

        file_name = os.path.basename(file_path)
        playlists[name].append(file_name)
        self.save_playlists(playlists)

        await message.edit(f"Added: {file_name}")

    async def pllistcmd(self, message):
        playlists = self.get_playlists()
        if not playlists:
            await message.edit("No playlists created")
            return

        text = "Playlists:\n"
        for p in playlists:
            text += f"- {p} ({len(playlists[p])} songs)\n"

        await message.edit(text)

    async def plsongs_cmd(self, message):
        name = utils.get_args_raw(message)
        playlists = self.get_playlists()

        if name not in playlists:
            await message.edit("Playlist not found")
            return

        songs = playlists[name]
        if not songs:
            await message.edit("Playlist is empty")
            return

        text = f"Songs in {name}:\n"
        for i, s in enumerate(songs, 1):
            text += f"{i}. {s}\n"

        await message.edit(text)

    async def pldelcmd(self, message):
        args = utils.get_args(message)
        if len(args) != 2:
            await message.edit("Usage: .pldel <playlist> <number>")
            return

        name, index = args
        playlists = self.get_playlists()

        if name not in playlists:
            await message.edit("Playlist not found")
            return

        try:
            index = int(index) - 1
            song = playlists[name].pop(index)
        except:
            await message.edit("Invalid song number")
            return

        file_path = os.path.join(self.base_path, name, song)
        if os.path.exists(file_path):
            os.remove(file_path)

        self.save_playlists(playlists)
        await message.edit(f"Deleted: {song}")

    async def pluploadcmd(self, message):
        name = utils.get_args_raw(message)
        playlists = self.get_playlists()

        if name not in playlists:
            await message.edit("Playlist not found")
            return

        songs = playlists[name]
        if not songs:
            await message.edit("Playlist is empty")
            return

        await message.edit(f"Uploading {len(songs)} songs...")

        for song in songs:
            path = os.path.join(self.base_path, name, song)
            if os.path.exists(path):
                await self.client.send_file(message.to_id, path)

        await message.edit("Upload completed")