from discord.ext import commands
from discord import app_commands
from typing import Literal
import asyncio
import discord
from ui.views.paginator import Paginator


class SuggestionList(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client
    @app_commands.command(name="suggestion-list", description="Shows all of the suggestions in a forum")
    @app_commands.describe(forum="The forum channel to check", sort_by="What to sort the threads by")
    @app_commands.guild_only()
    async def suggestion_list(self, interaction: discord.Interaction, forum: discord.ForumChannel, sort_by: Literal['Date', 'Reactions'] = 'Reactions'):
        data = []
        await interaction.response.send_message("⚠️ Sorting through threads. Please standby as this may take a few seconds...")

        threads = forum.threads
        tasks = []

        for thread in threads:
            if not thread.locked:
                tasks.append(self.process_thread(thread, sort_by))

        # Process all threads asynchronously
        results = await asyncio.gather(*tasks)
        data.extend(results)

        # Remove None entries (in case a thread was skipped)
        data = [item for item in data if item is not None]
        
        # Sort data
        data.sort(key=lambda x: x[0], reverse=(sort_by == 'Reactions'))

        # Format for display
        sorted_data = [item[1] for item in data]
        paginate = Paginator()
        paginate.title = f"Suggestion List for {forum.name}"
        paginate.count = True
        paginate.data = sorted_data
        paginate.sep = 20
        await paginate.send(interaction)

    async def process_thread(self, thread: discord.Thread, sort_by: str):
        """Process a single thread and return data for sorting."""
        reaction_count = 0
        timestamp = int(thread.created_at.timestamp())

        # Fetch the first message
        try:
            async for message in thread.history(limit=1, oldest_first=True):
                starter_message = message
                for reaction in starter_message.reactions:
                    if reaction.emoji == "✅":
                        reaction_count = reaction.count
                break
        except discord.HTTPException:
            return None  # Skip thread if fetching message fails

        if sort_by == 'Date':
            return (timestamp, f"<t:{timestamp}:R> {reaction_count} {thread.mention}")
        elif sort_by == 'Reactions':
            return (reaction_count, f"<t:{timestamp}:R> {reaction_count} {thread.mention}")

    


async def setup(client:commands.Bot) -> None:
    await client.add_cog(SuggestionList(client))