from ui.views.sync_buttons_view import SyncButtons
from discord.ext import commands
from discord import app_commands
from typing import Literal
import discord
from core.config import ConfigManager
from ui.views.applications_view import Applications
from ui.views.information_view import InformationView


def build_sync_embed() -> discord.Embed:
    embed = discord.Embed(
        title="Account Verification",
        color=discord.Color.from_str(ConfigManager.get("EMBED_COLOR")),
        description=(
            "In order to receive support from our staff team, you will need to verify yourself first. "
            "This is a quick process — do not be worried.\n"
            "\n"
            "**Steps**\n"
            "> **1)** Connect to **`play.minecadia.com`**\n"
            "> **2)** Type **`/sync`** in one of our lobbies\n"
            "> **3)** Copy the code, return to Discord, and click the green **Sync Account** button\n"
            "> **4)** Enter your sync code in the pop-up, press submit, and you're done!\n"
            "\n"
            "*Wish to unlink your account? Press the red **Unsync Account** button.*"
        ),
    )
    embed.add_field(
        name="Can't join play.minecadia.com?",
        value=(
            "Connect to **`sync.minecadia.com`** instead, type **`/sync`** in chat to receive your code, "
            "then come back here and click **Sync Account** below."
        ),
        inline=False,
    )
    return embed


class SendMessage(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client
        self.application_data: dict = ConfigManager.load("applications")
        
    @app_commands.command(name="send-message", description="Sends a message prompt.")
    @app_commands.describe(option="The message that you'd wish to send")
    @app_commands.guild_only()
    async def sendmessage(self, interaction: discord.Interaction, option: Literal["Sync", "Information", "Applications"]):
        await interaction.response.send_message(content="Sending your message...", ephemeral=True)
        embeds = {
              "Sync": [
                {"embed": build_sync_embed(),
                  "view": SyncButtons(),
                  "image": "https://i.imgur.com/rxRI82O.png"
                }
              ],
              "Information": [
                 {"embed": discord.Embed(color=discord.Color.from_str(ConfigManager.get('EMBED_COLOR')),
                                         description=("## Welcome to the Minecadia Discord! <:minecadia_2:1444800686372950117>\n"
                                                      '\n'
                                                      "We are one of the largest cross-platform compatible Minecraft networks - The home of Factions, Kitmap, Lifesteal SMP, Pixelmon, Skyblock and much more to come.\n"
                                                      '\n'
                                                      "Click the buttons down below for more information.")),
                  "view": InformationView(),
                  "image": "https://i.imgur.com/jpz6llc.png"
                 }
              ],
              "Applications": [
                 {"embed": discord.Embed(color=discord.Color.from_str(ConfigManager.get('EMBED_COLOR')),
                                         title = ConfigManager.load('applications')['Main_Embed']['title'],
                                         description = ConfigManager.load('applications')['Main_Embed']['description'].replace('{staff_status}', ConfigManager.load('applications')['Ranks']['staff']['status']).replace('{qa_status}', ConfigManager.load('applications')['Ranks']['qa']['status'])), # ADD FOR MEDIA .replace('{media_status}', ConfigManager.load('applications')['Ranks']['media']['status'])
                  "view": Applications(),
                  "image": ConfigManager.load('applications')['Main_Embed']['image']
                 }
              ]
        }
        chosen_embed = embeds.get(option, [])

        for embed in chosen_embed:
            embed_obj = embed['embed']
            if embed['image']:
               embed_obj.set_image(url=embed['image'])
            await interaction.channel.send(embed=embed_obj, view=embed['view'])
        await interaction.edit_original_response(content="Successfully sent your message!")



async def setup(client:commands.Bot) -> None:
    await client.add_cog(SendMessage(client))