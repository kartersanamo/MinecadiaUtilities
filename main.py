import os
from pathlib import Path

os.chdir(Path(__file__).resolve().parent)

from ui.views.applications_view import Applications
from ui.views.information_view import InformationView
from ui.views.poll_buttons_view import PollButtons
from ui.views.confirm_buttons_view import ConfirmButtons
from ui.views.sync_buttons_view import SyncButtons
from discord.ext import commands
from discord import app_commands
import discord
from dotenv import load_dotenv
from core.app import BotApp
from core.config import ConfigManager
from core.decorators import task
from core.loggers import log_commands, log_tasks

load_dotenv()

from core.errors.setup import wire_bot



COG_FILES = [file.split(".")[0].title() for file in os.listdir("cogs/") if file.endswith(".py")]


class Client(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix='.', intents=discord.Intents().all())
        wire_bot(self, bot_name="Utilities", log_commands=log_commands, log_tasks=log_tasks)
    
    @task("Setup Cogs")
    async def setup_cogs(self):
        for ext in COG_FILES:
            log_tasks.info(f"Loaded cog {ext}.py")
            await self.load_extension("cogs." + ext.lower())
        from core.analytics.register import register_command_tracking

        await register_command_tracking(self)

    @task("Add Views")
    async def add_views(self):
        views: list[discord.ui.View] = [
            ConfirmButtons(), SyncButtons() , InformationView(), Applications(), PollButtons()
        ]
        for view in views:
            log_tasks.info(f"Added view {view.__class__.__name__}")
            self.add_view(view)

    @task("Update Presence")
    async def update_presence(self):
        presence = ConfigManager.get("PRESENCE")
        await client.change_presence(activity = discord.Game(name = presence))
        log_tasks.info(f"Updated the bot's presence to {presence}")

    @task("Remove Help")
    async def remove_help(self):
        client.remove_command("help")

    @task("Sync Command Tree")
    async def sync_command_tree(self) -> list[discord.app_commands.AppCommand]:
        from core.guild_command_sync import sync_guild_commands

        return await sync_guild_commands(self, log=log_tasks)

    @task("Setup Hook")
    async def setup_hook(self):
        from core.errors.setup import wire_bot_async_setup

        await wire_bot_async_setup(self, bot_name="Utilities", log_tasks=log_tasks)
        self.app = BotApp.from_bot(self)
        await self.setup_cogs()
        await self.add_views()
    
    @task("Logging in")
    async def on_ready(self):
        await self.update_presence()
        await self.remove_help()
        await self.sync_command_tree()
        log_tasks.info(f"Logged in as {client.user} ({client.user.id})")


client = Client()

@task("Utilities Reload Command", True)
async def utilities_reload_command(interaction: discord.Interaction, cog: str):
    if interaction.guild is None:
        return await interaction.response.send_message(content = "Commands cannot be ran in DMs!", ephemeral = True)
    if cog not in COG_FILES:
        await interaction.response.send_message(f"Invalid cog name **{cog}.py**", ephemeral = True)
        return
    await client.reload_extension(f"cogs.{cog.lower()}")
    synced = await client.sync_command_tree()
    await interaction.response.send_message(
        f"Successfully reloaded **{cog}.py** and synced **{len(synced)}** slash commands.",
        ephemeral=True,
    )

async def cog_autocomplete(_: discord.Interaction, current: str):
    return [
        app_commands.Choice(name = cog, value = cog)
        for cog in COG_FILES if current.lower() in cog.lower()
    ]

@client.tree.command(name="utilities-reload", description="Reloads a Cog Class")
@app_commands.autocomplete(cog=cog_autocomplete)
async def utilitiesreload(interaction: discord.Interaction, cog: str):
    await utilities_reload_command(interaction, cog)


@client.tree.command(
    name="utilities-sync",
    description="Re-register slash commands with Discord (fixes signature mismatches)",
)
@app_commands.checks.has_any_role(*ConfigManager.all()["ADMIN_ROLES"])
async def utilitiessync(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    synced = await client.sync_command_tree()
    await interaction.followup.send(
        f"Synced **{len(synced)}** global commands with Discord. "
        "Old commands may take a minute to disappear.",
        ephemeral=True,
    )

TOKEN = os.getenv("DISCORD_TOKEN")
if not TOKEN:
    raise ValueError("Set DISCORD_TOKEN in .env")

if __name__ == "__main__":
    client.run(TOKEN)