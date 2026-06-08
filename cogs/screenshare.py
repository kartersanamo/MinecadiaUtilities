from discord.ext import commands
from discord import app_commands
from discord import Webhook
from typing import Literal
import datetime
import discord
import aiohttp
import json
from core.config import ConfigManager
from core.database import execute
from services.poll_service import is_found


with open("assets/config.json", "r") as file:
    data = json.load(file)


class Screenshare(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client
        self.screenshares = {}
    
        with open("assets/config.json", "r") as file:
            self.data = json.load(file)

    async def send_webhook(self, session, url, embed, username, avatar_url=None):
        webhook = Webhook.from_url(url, session = session)
        return await webhook.send(
            embed = embed, 
            username = username, 
            avatar_url = avatar_url, 
            wait = True
        )

    @app_commands.command(name="start-screenshare", description="Starts a screenshare with a player")
    @app_commands.describe(user="The discord user to start the screenshare with", 
                           reason="The reason that you are screensharing this user")
    @app_commands.guild_only()
    async def startscreenshare(self, interaction: discord.Interaction, user: discord.Member, reason: str):
        await interaction.response.send_message("Starting a screenshare with the user...", ephemeral=True)

        if user.id in self.screenshares:
            information = self.screenshares[user.id]

            screensharer = discord.utils.get(interaction.guild.members, id=int(information['screensharer']))
            started_at = await self.client.app.time_format.seconds_to_format(int(float(datetime.datetime.utcnow().timestamp())) - information['started_at'])
            channel = discord.utils.get(interaction.guild.voice_channels, id=int(information['channel_id']))

            embed = discord.Embed(title="Error Starting Screenshare",
                                  color=discord.Color.from_str(ConfigManager.get("EMBED_COLOR")),
                                  description=(f"Failed! {user.mention} is already being screenshared.\n"
                                                "\n"
                                                f"`Screensharer` {screensharer.mention}\n"
                                                f"`Started` {started_at} Ago\n"
                                                f"`Channel` {channel.mention}\n"
                                                f"`Reason` {information['reason']}")
                                  )

            logo_url = self.client.app.embeds.get_logo_url(ConfigManager.get("LOGO"))
            embed.set_footer(text=ConfigManager.get("FOOTER"), icon_url=logo_url)

            return await interaction.edit_original_response(content=None, embed=embed)

        verified = discord.utils.get(interaction.guild.roles, name="Verified")
        ss_verified = discord.utils.get(interaction.guild.roles, name="SS Verified")

        overwrites = {
            user: discord.PermissionOverwrite(view_channel=True, connect=True, speak=True, stream=True),
            interaction.user: discord.PermissionOverwrite(view_channel=True, connect=True, speak=True, stream=True),
            ss_verified: discord.PermissionOverwrite(view_channel=True, connect=True, speak=True, stream=True),
            verified: discord.PermissionOverwrite(view_channel=False, connect=False, speak=False, stream=False),
            interaction.guild.default_role: discord.PermissionOverwrite(view_channel=False, connect=False, speak=False, stream=False)
        }

        channel = await interaction.guild.create_voice_channel(
            name=user.display_name,
            reason="Screensharing",
            position=0,
            user_limit=3,
            overwrites=overwrites
        )
        self.screenshares[user.id] = {'screensharer': interaction.user.id,
                                      'started_at': int(float(datetime.datetime.utcnow().timestamp())),
                                      'channel_id': channel.id,
                                  'reason': reason}
        embed = discord.Embed(title="Screenshare Started",
                              color=discord.Color.from_str(ConfigManager.get("EMBED_COLOR")), 
                              description=(f"`Screensharer` {interaction.user.mention} ({interaction.user.name})\n"
                                            f"`Member` {user.mention} ({user.name})\n"
                                            f"`Channel` {channel.mention}\n"
                                            f"`Reason` {reason}")
                              )
        logo_url = self.client.app.embeds.get_logo_url(ConfigManager.get("LOGO"))
        embed.set_footer(text=ConfigManager.get("FOOTER"), icon_url=logo_url)

        await interaction.edit_original_response(content="Successfully began your screenshare!")
        await interaction.channel.send(embed=embed)
    
    @app_commands.command(name="stop-screenshare", description="Stops a screenshare with a player")
    @app_commands.describe(user="The discord user to stop the screenshare with", 
                           ign="The IGN of the user that you just screenshared", 
                           outcome="The outcome of the screenshare. Guilty or Innocent", 
                           proof="Proof of the ban if guilty")
    @app_commands.guild_only()
    async def stopscreenshare(self, interaction: discord.Interaction, user:discord.Member, ign:str, outcome:Literal['Guilty', 'Innocent'], proof:str=None):
        if user.id not in self.screenshares:
            return await interaction.response.send_message("Failed! This user is not being screenshared right now.", ephemeral=True)

        await interaction.response.send_message(content="Attempting to end this screenshare...", ephemeral=True)

        ss_information = self.screenshares[user.id]
        proof = "N/A" if not proof else proof
        screensharer = discord.utils.get(interaction.guild.members, id=int(ss_information['screensharer']))
        channel = discord.utils.get(interaction.guild.voice_channels, id=int(ss_information['channel_id']))

        await channel.delete(reason="Screenshare complete")

        current_screenshares = await is_found(interaction.user, "screenshares")

        await execute(
            "UPDATE staff_statistics SET `screenshares` = %s WHERE `user_id` = %s",
            (current_screenshares + 1, interaction.user.id),
        )
        async with aiohttp.ClientSession() as session:
            proof_text = f"\n`Proof` {proof}"
            length = await self.client.app.time_format.seconds_to_format(int(float(datetime.datetime.utcnow().timestamp())) - ss_information['started_at'])
            description = f"`Discord` {user.display_name} ({user.id})\n`IGN` {ign}\n`Reason` {ss_information['reason']}\n`Outcome` {outcome}\n`Length` {length}{proof_text}"
            timestamp = datetime.datetime.utcnow()
            embed = discord.Embed(
                title="Screenshare Log",
                color=discord.Color.from_str(ConfigManager.get("EMBED_COLOR")),
                description=description,
                timestamp=timestamp,
            )
            embed.set_author(name=interaction.user.display_name, icon_url=interaction.user.avatar)
            log_message = await self.send_webhook(session, ConfigManager.get("SCREENSHARES_WEBHOOK"), embed, "Screenshare Logs")

        embed = discord.Embed(title="Stopped Screenshare",
                              color=discord.Color.from_str(ConfigManager.get("EMBED_COLOR")),
                              description=(f"`Screensharer` {screensharer.mention} ({screensharer.name})\n"
                                          f"`Member` {user.mention} ({user.name})\n"
                                          f"`Reason` {ss_information['reason']}\n"
                                          f"`Length` {length}\n"
                                          f"`IGN` {ign}\n"
                                          f"`Outcome` {outcome}\n"
                                          f"`Proof` {proof}\n"
                                          f"`Log` [Jump to Message]({log_message.jump_url})"))

        logo_url = self.client.app.embeds.get_logo_url(ConfigManager.get("LOGO"))
        embed.set_footer(text=ConfigManager.get("FOOTER"), icon_url=logo_url)

        del self.screenshares[user.id]

        await interaction.edit_original_response(content="Successfully ended your screenshare!")
        await interaction.channel.send(embed=embed)
  


async def setup(client:commands.Bot) -> None:
    await client.add_cog(Screenshare(client))