from discord.ext import commands
import discord
import json
from core.config import ConfigManager
from core.loggers import log_tasks
from services.permission_service import is_staff


class Embed(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client

        with open("assets/config.json", "r") as file:
            self.data = json.load(file)

    @commands.Cog.listener()
    async def on_message(self, message):
        try:
            if not await is_staff(message.author, message.guild):
                return
        except Exception:
            return

        try:
            content = message.content
            split = content.split("\n")
            footer = False
            author = False
            title = None
            image = None
            thumbnail = None
            color = None
            replace = None

            if "-announcement" in split:
                content = content.replace("-announcement", "")
            else:
                return

            if "-footer" in split:
                content = content.replace("-footer", "")
                footer = True

            if "-title" in split:
                title_index = split.index("-title")
                title = split[title_index - 1]
                content = content.replace(title, "").replace("-title", "")

            if "-thumbnail" in split:
                thumbnail_index = split.index("-thumbnail")
                thumbnail = split[thumbnail_index - 1]
                content = content.replace(thumbnail, "").replace("-thumbnail", "")

            if "-image" in split:
                image_index = split.index("-image")
                image = split[image_index - 1]
                content = content.replace(image, "").replace("-image", "")

            if "-author" in split:
                content = content.replace("-author", "")
                author = True

            if "-color" in split:
                color_index = split.index("-color")
                color = split[color_index - 1]
                content = content.replace(color, "").replace("-color", "")

            if "-replace" in split:
                replace_index = split.index("-replace")
                replace = split[replace_index - 1]
                content = content.replace(replace, "").replace("-replace", "")

            embed = discord.Embed(description=content, color=discord.Color.from_str(ConfigManager.get("EMBED_COLOR")))

            if title:
                embed.title = title

            if footer:
                embed.timestamp = message.created_at
                embed.set_footer(text=message.author, icon_url=message.author.avatar)

            if color:
                embed.color = discord.Color.from_str(color)

            if author:
                embed.set_author(name=message.author, icon_url=message.author.avatar)

            if image:
                try:
                    embed.set_image(url=image)
                except Exception:
                    pass

            if thumbnail:
                try:
                    embed.set_thumbnail(url=thumbnail)
                except Exception:
                    pass
        
            if replace:
                mg, chn = replace.split("/")
                channel = message.guild.get_channel(int(chn))
                msg = await channel.fetch_message(int(mg))
                await msg.edit(embed=embed)
        
            else:
                await message.channel.send(embed=embed)
                log_tasks.info(f"Embed formatter sent by {message.author} ({message.author.id}) in #{message.channel} ({message.channel.id})")

            await message.delete()
        
        except Exception as e:
            log_tasks.error(f"Error sending embed formatter {e}")


async def setup(client: commands.Bot):
    await client.add_cog(Embed(client))