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
                (characters_sent, message.author.id),
            )
            if analytics:
                analytics.increment_total_stat(str(message.author.id), "messages_sent", 1)
                analytics.increment_total_stat(
                    str(message.author.id),
                    "characters_sent",
                    0,
                )
                analytics.record_staff_message(
                    message.author.id,
                    message.channel.id,
                    0,
                )
            # log_tasks.info(f"Message sent by {message.author} ({message.author.id}) in #{message.channel} ({message.channel.id}) {message_count+1} Messages {characters_sent+len(message.content)} Characters")
        
        except Exception as e:
            log_tasks.error(f"Error updating message count {e}")


async def setup(client:commands.Bot) -> None:
    await client.add_cog(MessageCounter(client))