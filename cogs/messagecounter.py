from discord.ext import commands
import discord
import time
import json
import re
from core.config import ConfigManager
from core.database import execute
from core.loggers import log_tasks
from core.analytics import logger as analytics
from services.permission_service import is_staff
from services.poll_service import is_found


class MessageCounter(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client
    
        with open("assets/config.json", "r") as file:
            self.data = json.load(file)
    
    async def get_number(self):
        row = await execute("SELECT COUNT(*) FROM `tickets`")
        return int(row[0]['COUNT(*)']) + 1

    @commands.Cog.listener()
    async def on_message(self, message):
        try:
            if message.author.bot:
                if message.author.id == ConfigManager.get('GIVEAWAY_BOT_ID') and "Congratulations" in message.content:
                    ids: list[int] = [int(match) for match in re.findall(r'<@(\d+)>', message.content)]
                    prize: str = message.content.split('won the ')[1]
                    category = self.client.get_channel(ConfigManager.get('DISCORD_SUPPORT_CATEGORY_ID'))
                    for id in ids:
                        user = message.guild.get_member(id)
                        channel = await message.guild.create_text_channel(category = category, name = "giveaway-winner", overwrites = category.overwrites)
                        await channel.set_permissions(user, view_channel = True, send_messages = True)
                        number = await self.get_number()
                        await execute(
                            "INSERT INTO `tickets` (`channel_id`, `owner_id`, `type`, `opened_at`, `number`, `is_active`, `closed_by_id`, `closed_at`, `reason`, `name`, `transcript`, `privated`) "
                            "VALUES (%s, %s, %s, %s, %s, %s, NULL, NULL, NULL, NULL, NULL, %s)",
                            (channel.id, user.id, "Giveaway Rewards", int(time.time()), number, 1, "Admin"),
                        )
                        embed = discord.Embed(color = discord.Color.from_str(ConfigManager.get('EMBED_COLOR')),
                                            description = f"Hey {user.mention}!\n \nYou have created a new ticket!\n**Type:** Giveaway Rewards ({prize})\n \nThis ticket has been automatically created for you by a staff member. Please provide any information they require.\n \n**One of our staff members will be with you shortly.**")
                        await channel.send(content = user.mention)
                        await channel.send(embed = embed)
                return
            if not await is_staff(message.author, message.guild):
                return
            if not message.channel.category or message.channel.category.id not in ConfigManager.get("TICKET_CATEGORIES"):
                return
            message_count = await is_found(message.author, "messages_sent")
            characters_sent = await is_found(message.author, "characters_sent")
            await execute(
                "UPDATE staff_statistics SET `messages_sent` = %s WHERE `user_id` = %s",
                (message_count + 1, message.author.id),
            )
            await execute(
                "UPDATE staff_statistics SET `characters_sent` = %s WHERE `user_id` = %s",
                (characters_sent + len(message.content), message.author.id),
            )
            if analytics:
                analytics.increment_total_stat(str(message.author.id), "messages_sent", 1)
                analytics.increment_total_stat(
                    str(message.author.id),
                    "characters_sent",
                    len(message.content or ""),
                )
                analytics.record_staff_message(
                    message.author.id,
                    message.channel.id,
                    len(message.content or ""),
                )
            # log_tasks.info(f"Message sent by {message.author} ({message.author.id}) in #{message.channel} ({message.channel.id}) {message_count+1} Messages {characters_sent+len(message.content)} Characters")
        
        except Exception as e:
            log_tasks.error(f"Error updating message count {e}")


async def setup(client:commands.Bot) -> None:
    await client.add_cog(MessageCounter(client))