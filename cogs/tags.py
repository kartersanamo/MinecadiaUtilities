from discord.ext import commands
from discord import app_commands
import discord
import asyncio
import json
from core.config import ConfigManager
from core.decorators import task


class CreateTagModal(discord.ui.Modal, title="Create a tag"):
    name = discord.ui.TextInput(label="Tag name", max_length=25)
    content = discord.ui.TextInput(label="Tag content", style=discord.TextStyle.paragraph, max_length=4000)

    async def on_submit(self, interaction: discord.Interaction) -> None:
        try:
            with open("assets/tags.json", "r+", encoding="utf-8") as f:
                data = json.load(f)
                data.setdefault("PLAYER_TAGS", {}).setdefault(str(interaction.user.id), {})[str(self.name)] = str(self.content)
                f.seek(0)
                json.dump(data, f, indent=4)
                f.truncate()
            await interaction.response.send_message("`✅` Successfully saved your tag!", ephemeral=True)
        except Exception as error:
            await interaction.response.send_message(f"An error occurred:\n```{error}```", ephemeral=True)


async def tag_autocomplete(interaction: discord.Interaction, current: str):
    tags_data: dict = ConfigManager.load("tags")
    tag_dict = {tag['NAME']: tag['MESSAGE'] for tag in tags_data['TAGS']}
    player_tags: dict = tags_data['PLAYER_TAGS'].get(str(interaction.user.id), {})
    return  [
        app_commands.Choice(name = "➡️ Click here to add a new tag! ⬅️", value = "add_a_tag")
    ] + [
        app_commands.Choice(name = tag, value = tag)
        for tag in list(player_tags.keys()) if current.lower() in tag.lower()
    ] + [
        app_commands.Choice(name = tag, value = tag)
        for tag in list(tag_dict.keys()) if current.lower() in tag.lower()
    ]


class Tags(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client: commands.Bot = client
        self.tags_data: dict = ConfigManager.load("tags")
        self.tag_dict = {tag['NAME']: tag['MESSAGE'] for tag in ConfigManager.load('tags')['TAGS']}

    @task("Create Embed", False)
    async def create_embed(self, tag: str, tag_message: str) -> discord.Embed:
        embed = discord.Embed(
            title = tag,
            description = f"```{tag_message}```",
            color = discord.Color.from_str(ConfigManager.get('EMBED_COLOR'))
        )
        logo_url = self.client.app.embeds.get_logo_url(ConfigManager.get('LOGO'))
        embed.set_footer(text = ConfigManager.get('FOOTER'), icon_url = logo_url)
        return embed

    @task("Tags Command", True) 
    async def tags_command(self, interaction: discord.Interaction, tag: str) -> None:
        if tag == "add_a_tag":
            await interaction.response.send_modal(CreateTagModal())
            return

        else:
            tag_message: str = self.tag_dict.get(tag, None)
            if not tag_message:
                try:
                    tag_message: str = ConfigManager.load('tags')['PLAYER_TAGS'][str(interaction.user.id)][tag]
                except Exception as e:
                    tag_message: str = "Could not find your tag, sorry!"
            tag_embed: discord.Embed = await self.create_embed(tag, tag_message)
            logo_url = self.client.app.embeds.get_logo_url(ConfigManager.get("LOGO"))
            tag_embed.set_footer(text=ConfigManager.get("FOOTER"), icon_url=logo_url)
            await interaction.response.send_message(
                content = "`✅` Here is your tag...",
                embed = tag_embed, 
                ephemeral = True
            )
        self.tags_data: dict = ConfigManager.load("tags")

    @app_commands.command(name = "tags", description = "Sends a presaved tag message")
    @app_commands.autocomplete(tag = tag_autocomplete)
    async def tags(self, interaction: discord.Interaction, tag: str) -> None:
       await self.tags_command(interaction, tag)



async def setup(client:commands.Bot) -> None:
  await client.add_cog(Tags(client))