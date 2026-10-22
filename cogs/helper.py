from discord.ext import commands
from discord import app_commands
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
  
    @app_commands.command(name="helper", description="Get help for a keyword")
    async def helper(self, interaction: discord.Interaction, keyword: str):
        if await is_staff(interaction.user, interaction.guild) or interaction.channel_id not in ConfigManager.get('HELPER_CHANNELS'):
            return
        try:
            msg = keyword.lower()
            words = msg.split(" ")
            title = None
            description = None
            for keyword, response in ConfigManager.get('HELPER_RESPONSES').items():
                if keyword in words:
                    title = response['Title']
                    description = response['Description']
                    break
            if description:
                embed = discord.Embed(title=title, description=description, color=discord.Color.from_str(ConfigManager.get('EMBED_COLOR')))
                logo_url = self.client.app.embeds.get_logo_url(ConfigManager.get('LOGO'))
                embed.set_thumbnail(url=logo_url)
                embed.set_footer(text=ConfigManager.get('FOOTER'), icon_url=logo_url)
                await interaction.response.send_message(embed=embed, file=discord.File("assets/Logo.png"))
                log_tasks.info(f"Helper message {title} sent to {interaction.user} ({interaction.user.id}) in channel {interaction.channel_id}")
            else:
                await interaction.response.send_message("No helper response matched that keyword.", ephemeral=True)

        except Exception as e:
            log_tasks.error(f"Error sending helper message {e}")


async def setup(client:commands.Bot) -> None:
    await client.add_cog(Helper(client))