from discord.ext import commands
from discord import app_commands
import asyncio
import discord


class SuggestionLock(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client
    @app_commands.command(name = "suggestion-lock", description = "Locks all suggestions in a forum")
    @app_commands.describe(forum = "The forum channel to lock")
    @app_commands.guild_only()
    async def suggestion_lock(self, interaction: discord.Interaction, forum: discord.ForumChannel):
        await interaction.response.send_message("⚠️ Locking all threads. Please standby as this may take a few seconds...")

        threads = forum.threads
        tasks = []

        count: int = 0
        for thread in threads:
            if not thread.locked:
                count += 1
                tasks.append(self.process_thread(thread))

        await asyncio.gather(*tasks)
        await interaction.edit_original_response(content = f"✅ Successfully locked `{count}` threads in {forum.mention}.")

    async def process_thread(self, thread: discord.Thread) -> bool:
        """Process a single thread by locking it."""
        await thread.edit(locked = True)
        return True

    


async def setup(client:commands.Bot) -> None:
    await client.add_cog(SuggestionLock(client))