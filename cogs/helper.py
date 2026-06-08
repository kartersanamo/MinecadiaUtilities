from discord.ext import commands
import discord
import typing
from core.config import ConfigManager
from core.loggers import log_tasks
from services.permission_service import is_staff


class Helper(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client
        self._cd = commands.CooldownMapping.from_cooldown(1, 180.0, commands.BucketType.member)
    def get_ratelimit(self, message: discord.Message) -> typing.Optional[int]:
        bucket = self._cd.get_bucket(message)
        return bucket.update_rate_limit()
  
    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or await is_staff(message.author, message.guild) or message.channel.id not in ConfigManager.get('HELPER_CHANNELS'):
            return
        try:
            msg = message.content.lower()
            words = msg.split(" ")
            title = None
            description = None
            for keyword, response in ConfigManager.get('HELPER_RESPONSES').items():
                if keyword in words:
                    title = response['Title']
                    description = response['Description']
                    break
            if description:
                ratelimit = self.get_ratelimit(message)
                if ratelimit:
                    log_tasks.info(f"Cannot send helper message {title} as {message.author} ({message.author.id}) in {message.channel} ({message.channel.id}) is on cooldown")
                    return
                embed = discord.Embed(title=title, description=description, color=discord.Color.from_str(ConfigManager.get('EMBED_COLOR')))
                logo_url = self.client.app.embeds.get_logo_url(ConfigManager.get('LOGO'))
                embed.set_thumbnail(url=logo_url)
                embed.set_footer(text=ConfigManager.get('FOOTER'), icon_url=logo_url)
                await message.reply(embed=embed, file=discord.File("assets/Logo.png"))
                log_tasks.info(f"Helper message {title} replied to {message.author} ({message.author.id}) in {message.channel} ({message.channel.id})")

        except Exception as e:
            log_tasks.error(f"Error sending helper message {e}")


async def setup(client:commands.Bot) -> None:
    await client.add_cog(Helper(client))