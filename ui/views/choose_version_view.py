import discord
from core.config import ConfigManager
from core.loggers import log_tasks


class ChooseVersion(discord.ui.View):
    def __init__(self, interaction: discord.Interaction):
        super().__init__(timeout=None)
        self.interaction = interaction
    @discord.ui.button(emoji="<:crafting:1012353391952924702>", label="Java Edition", style=discord.ButtonStyle.green, custom_id="Java")
    async def java(self, interaction: discord.Interaction, Button: discord.ui.Button):
        try:
            java = discord.Embed(title="<:crafting:1012353391952924702> How to join on Java Edition! <:crafting:1012353391952924702> (Computer/PC)",
                                description=('<:checkmark:1012353338555248762> **Steps to Follow**:\n'
                                            '> **1** Open your Minecraft Game on any version 1.8+\n'
                                            '> **2** Click "Multiplayer"\n'
                                            '> **3** Click "Add Server"\n'
                                            '> **4** Type in the textbox called "Server Address" with the text: __play.minecadia.com__\n'
                                            '> **5** Click "Done" and join the server!\n'
                                            '\n'
                                            ':scroll: **Server Information**\n'
                                            '> **-** Server Address (IP): __play.minecadia.com__\n'
                                            '> **-** Server Name: Minecadia\n'
                                            '> **-** Recommended Minecraft Version: 1.8.9'),
                                color = discord.Color.from_str(ConfigManager.get('EMBED_COLOR')))
            java.set_image(url="https://i.imgur.com/mCRh0q0.gif")
            await self.interaction.edit_original_response(embed=java, view=None)
            log_tasks.info(f"{interaction.user} ({interaction.user.id}) clicked the {Button.label} {Button.emoji} button")
        
        except Exception as e:
            await interaction.response.send_message(content = f"{Button.label} {Button.emoji} button error {e}", ephemeral = True)
            log_tasks.error(f"{interaction.user} ({interaction.user.id}) failed to click the {Button.label} {Button.emoji} button {e}")
    
    @discord.ui.button(emoji="<:bedrock:1012354397046591559>", label="Bedrock Edition", style=discord.ButtonStyle.green, custom_id="Bedrock")
    async def bedrock(self, interaction: discord.Interaction, Button: discord.ui.Button):
        try:
            bedrock = discord.Embed(title="<:bedrock:1012354397046591559> How to join on Bedrock Edition! <:bedrock:1012354397046591559> (Mobile, Console, etc...)",
                                description=('<:checkmark:1012353338555248762> **Tutorials**\n'
                                                '> :mobile_phone: **Phone/Mobile:** https://bit.ly/BedrockTutorial1\n'
                                                '> :video_game: **Xbox/Playstation:** https://bit.ly/BedrockTutorial2\n'
                                                '> :joystick: **Nintendo Switch:** https://bit.ly/BedrockTutorial3\n'
                                                '\n'
                                                ':scroll: **Server Information**\n'
                                                '> **-** Server Address (IP): __play.minecadia.com__\n'
                                                '> **-** Server Port: 19132\n'
                                                '> **-** Server Name: Minecadia\n'),
                                color = discord.Color.from_str(ConfigManager.get('EMBED_COLOR')))
            await self.interaction.edit_original_response(embed=bedrock, view=None)
            log_tasks.info(f"{interaction.user} ({interaction.user.id}) clicked the {Button.label} {Button.emoji} button")
        
        except Exception as e:
            await interaction.response.send_message(content = f"{Button.label} {Button.emoji} button error {e}", ephemeral = True)
            log_tasks.error(f"{interaction.user} ({interaction.user.id}) failed to click the {Button.label} {Button.emoji} button {e}")
