# Heartify transitional hearts module for Hikka
# Writes each step of the text with rotating heart emojis

from .. import loader, utils
import asyncio

class HeartifyMod(loader.Module):
    """Transitional hearts for every letter of the text"""
    strings = {"name": "Heartify"}

    async def heartifycmd(self, message):
        """
        .heartify <text>
        Creates transitional heart message for each letter.
        """
        text = utils.get_args_raw(message)

        if not text:
            return await message.edit("❌ Please provide English text.\nExample: `.heartify Hello`")

        # full set of nice hearts
        hearts = [
            "❤️", "🩷", "💗", "💖", "💕", "💞", "💘", "💝",
            "💙", "💚", "💛", "🧡", "💜", "🤍", "🖤", "🤎"
        ]

        output = ""
        await message.edit("✨ Starting heartify...")

        for i, char in enumerate(text):
            heart = hearts[i % len(hearts)]  # cycle through hearts
            output += char
            await asyncio.sleep(0.2)  # smooth transition
            await message.edit(f"{heart} {output}")

        await message.edit(f"💫 **Finished:** {output}")