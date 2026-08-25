from discord.ext import commands
from discord import app_commands
from typing import Literal
import asyncio
import discord
from ui.views.paginator import Paginator

# Limit concurrent history fetches to avoid Discord global rate limits.
_HISTORY_CONCURRENCY = 5


class SuggestionList(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client

    @app_commands.command(name="suggestion-list", description="Shows all of the suggestions in a forum")
    @app_commands.describe(forum="The forum channel to check", sort_by="What to sort the threads by")
    @app_commands.guild_only()
    async def suggestion_list(
        self,
        interaction: discord.Interaction,
        forum: discord.ForumChannel,
        sort_by: Literal["Date", "Reactions"] = "Reactions",
    ):
        await interaction.response.send_message(
            "⚠️ Sorting through threads. Please standby as this may take a few seconds..."
        )

        threads = [thread for thread in forum.threads if not thread.locked]
        semaphore = asyncio.Semaphore(_HISTORY_CONCURRENCY)
        results = await asyncio.gather(
            *(self.process_thread(thread, sort_by, semaphore) for thread in threads)
        )

        data = [item for item in results if item is not None]
        data.sort(key=lambda x: x[0], reverse=(sort_by == "Reactions"))

        sorted_data = [item[1] for item in data] or ["No data found."]
        paginate = Paginator()
        paginate.title = f"Suggestion List for {forum.name}"
        paginate.count = True
        paginate.data = sorted_data
        paginate.sep = 20
        await paginate.send(interaction)

    async def process_thread(
        self,
        thread: discord.Thread,
        sort_by: str,
        semaphore: asyncio.Semaphore,
    ):
        """Process a single thread and return data for sorting."""
        reaction_count = 0
        timestamp = int(thread.created_at.timestamp())

        async with semaphore:
            try:
                async for message in thread.history(limit=1, oldest_first=True):
                    for reaction in message.reactions:
                        if reaction.emoji == "✅":
                            reaction_count = reaction.count
                    break
            except discord.HTTPException:
                return None

        if sort_by == "Date":
            return (timestamp, f"<t:{timestamp}:R> {reaction_count} {thread.mention}")
        return (reaction_count, f"<t:{timestamp}:R> {reaction_count} {thread.mention}")


async def setup(client: commands.Bot) -> None:
    await client.add_cog(SuggestionList(client))
