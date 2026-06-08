from urllib.request import Request, urlopen
from discord.ext import commands
from discord import app_commands
import discord
import json
from core.config import ConfigManager


class PlayerCount(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client

        with open("assets/config.json", "r") as file:
            self.data = json.load(file)

    @app_commands.command(name="player-count", description="Displays the current player count on the Minecadia Network")
    @app_commands.guild_only()
    async def playercount(self, interaction: discord.Interaction):
        response = Request(
            url = 'https://api.mcsrvstat.us/2/play.minecadia.com',
            headers = {'User-Agent': 'Mozilla/5.0'}
        )
        data = str(urlopen(response).read())
        player_count = data.split('"players":{"online":')[1].split(',"max":')[0]

        embed = discord.Embed(title=f"There are **{player_count}** players online!", color=discord.Color.from_str(ConfigManager.get("EMBED_COLOR")))
        await interaction.response.send_message(embed=embed)



async def setup(client:commands.Bot) -> None:
    await client.add_cog(PlayerCount(client))