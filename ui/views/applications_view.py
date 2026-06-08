import discord
from core.config import ConfigManager
from ui.views.apply_buttons_modal import ApplyButtons


class Applications(discord.ui.View):
    def __init__(self):
        super().__init__(timeout = None)
        self.application_data: dict = ConfigManager.load("applications")
        self.add_buttons()

    def add_buttons(self):
        for rank in list(ConfigManager.load('applications')['Ranks'].keys()):
            button = discord.ui.Button(
                emoji = ConfigManager.load('applications')['Ranks'][rank]['emoji'],
                label = ConfigManager.load('applications')['Ranks'][rank]['label'],
                custom_id = ConfigManager.load('applications')['Ranks'][rank]['custom_id'],
                style = discord.ButtonStyle.gray
            )
            button.callback = self.handle_application_press
            self.add_item(button)


    async def handle_application_press(self, interaction: discord.Interaction):
        custom_id: str = interaction.data.get("custom_id")
        button_label: str = ConfigManager.load('applications')['Ranks'][custom_id]['label']
        confirmation_message = discord.Embed(
            title = f"{button_label} Application",
            description = f"Hello {interaction.user.mention}, you've selected the **{button_label} Application**.\n\n"
                           f"{ConfigManager.load('applications')['Ranks'][custom_id]['message']}",
            color = discord.Color.from_str(ConfigManager.get('EMBED_COLOR')))
        
        logo_url = interaction.client.app.embeds.get_logo_url(ConfigManager.get("LOGO"))
        confirmation_message.set_footer(text=ConfigManager.get("FOOTER"), icon_url=logo_url)
        await interaction.response.send_message(embed = confirmation_message, ephemeral = True, view = ApplyButtons(interaction, custom_id)) # Button.custom_id == 'qa', 'staff'
