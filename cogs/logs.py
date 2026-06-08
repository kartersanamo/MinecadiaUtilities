from discord.ext import commands
import discord
import json
from core.loggers import log_commands, log_tasks


class Logs(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client
    
        with open("assets/config.json", "r") as file:
            self.data = json.load(file)

    @commands.Cog.listener()
    async def on_interaction(self, interaction: discord.Interaction):
        try:
            # Slash command ran
            if interaction.type == discord.InteractionType.application_command:
                name = f"/{interaction.command.name}"
                try:
                    for option in interaction.data.get('options'):
                        name += f" {option['name']}:{option['value']}"
                except KeyError:
                    pass
                log_commands.info(f"{interaction.user} ({interaction.user.id}) ran {name} in #{interaction.channel} ({interaction.channel.id}) {not interaction.command_failed}")

            # Component interaction (button press usually)
            # DISABLED as I will log this on every individual button press or select menu
            # elif interaction.type == discord.InteractionType.component:
            #    log_tasks.info(f"{interaction.user} ({interaction.user.id}) clicked a button/select menu in #{interaction.channel} ({interaction.channel.id})")
            
            # Modal submission
            elif interaction.type == discord.InteractionType.modal_submit:
                log_tasks.info(f"{interaction.user} ({interaction.user.id}) submitted a modal in #{interaction.channel} ({interaction.channel.id})")
        except Exception:
            pass

async def setup(client:commands.Bot) -> None:
    await client.add_cog(Logs(client))