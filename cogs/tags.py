from discord.ext import commands
from discord import app_commands
import discord
import asyncio
import json
from core.config import ConfigManager
from core.decorators import task


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
            name_of_tag_embed = discord.Embed(
                title = "Name of Tag",
                description = "Please enter the name of your tag below.\nType `CANCEL` to cancel the process.",
                color = discord.Color.from_str(ConfigManager.get("EMBED_COLOR"))
            )
            logo_url = self.client.app.embeds.get_logo_url(ConfigManager.get("LOGO"))
            name_of_tag_embed.set_footer(text=ConfigManager.get("FOOTER"), icon_url=logo_url)
            await interaction.response.send_message(embed = name_of_tag_embed)
            
            while True:
                def name_check(m: discord.Message):
                    return m.author == interaction.user and m.channel == interaction.channel

                name_message = await interaction.client.wait_for('message', check=name_check)
                content = name_message.content.strip()

                if content.lower() == "cancel":
                    await name_message.delete()
                    tag_creation_cancelled_embed = discord.Embed(
                        description="`❌` Tag creation cancelled.",
                        color=discord.Color.from_str(ConfigManager.get("EMBED_COLOR"))
                    )
                    await interaction.edit_original_response(embed=tag_creation_cancelled_embed, view=None)
                    return

                if len(content) > 25:
                    await name_message.delete()
                    warning = await interaction.followup.send("`⚠️` Tag name must be 25 characters or fewer.")
                    await asyncio.sleep(3)
                    await warning.delete()
                    continue 

                name = content
                await name_message.delete()
                break

            tag_content_embed = discord.Embed(
                title = name,
                description = f"Please enter the content of your new tag below. \nType `CANCEL` to cancel the process.",
                color = discord.Color.from_str(ConfigManager.get("EMBED_COLOR"))
            )
            logo_url = self.client.app.embeds.get_logo_url(ConfigManager.get("LOGO"))
            tag_content_embed.set_footer(text=ConfigManager.get("FOOTER"), icon_url=logo_url)
            await interaction.edit_original_response(embed = tag_content_embed)

            def content_check(m: discord.Message):
                return m.author == interaction.user and m.channel == interaction.channel and m.content.lower() != "cancel"
            
            content_message = await interaction.client.wait_for('message', check = content_check)
            content = content_message.content.strip()
            await content_message.delete()
            if content.lower() == "cancel":
                tag_creation_cancelled_embed = discord.Embed(
                    description="`❌` Tag creation cancelled.",
                    color=discord.Color.from_str(ConfigManager.get("EMBED_COLOR"))
                )
                await interaction.edit_original_response(embed=tag_creation_cancelled_embed, view=None)
                return

            try:
                with open("assets/tags.json", "r+", encoding = "utf-8") as f:
                    data = json.load(f)
                    user_id = str(interaction.user.id)

                    if "PLAYER_TAGS" not in data:
                        data["PLAYER_TAGS"] = {}

                    if user_id not in data["PLAYER_TAGS"]:
                        data["PLAYER_TAGS"][user_id] = {}

                    data["PLAYER_TAGS"][user_id][name] = content

                    f.seek(0)
                    json.dump(data, f, indent=4)
                    f.truncate()

                confirmation_embed = discord.Embed(
                    title = name,
                    description = f"```{content}```",
                    color = discord.Color.from_str(ConfigManager.get("EMBED_COLOR"))
                )
                logo_url = self.client.app.embeds.get_logo_url(ConfigManager.get("LOGO"))
                confirmation_embed.set_footer(text=ConfigManager.get("FOOTER"), icon_url=logo_url)
                await interaction.edit_original_response(
                    content = "`✅` Successfully saved your tag!",
                    embed = confirmation_embed
                )

            except Exception as e:
                error_embed = discord.Embed(
                    title = "Error Saving Tag",
                    description = f"An error occurred:\n```{e}```",
                    color = discord.Color.from_str(ConfigManager.get("EMBED_COLOR"))
                )
                logo_url = self.client.app.embeds.get_logo_url(ConfigManager.get("LOGO"))
                error_embed.set_footer(text=ConfigManager.get("FOOTER"), icon_url=logo_url)
                await interaction.edit_original_response(embed = error_embed)

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