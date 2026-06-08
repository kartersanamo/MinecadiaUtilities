import discord
from core.config import ConfigManager
from ui.modals.application_modal import ApplicationModal
from ui.views.step_buttons_modal import StepButtons

interactions: dict[int, discord.Interaction] = {}


class ApplyButtons(discord.ui.View):
    def __init__(self, interaction: discord.Interaction, rank: str):
        interactions.update({
            interaction.user.id: interaction
        })
        self.rank: str = rank # Rank == custom_id of button pressed: 'qa', 'staff'
        self.application_data: dict = ConfigManager.load("applications")
        super().__init__(timeout = None)
        self.add_buttons()
    
    def add_buttons(self):
        for role in list(ConfigManager.load('applications')['Ranks'][self.rank]['roles'].keys()):
            button = discord.ui.Button(
                emoji = ConfigManager.load('applications')['Ranks'][self.rank]['roles'][role]['emoji'],
                label = ConfigManager.load('applications')['Ranks'][self.rank]['roles'][role]['label'],
                custom_id = ConfigManager.load('applications')['Ranks'][self.rank]['roles'][role]['custom_id'],
                style = discord.ButtonStyle.gray
            )
            button.callback = self.handle_role_press
            self.add_item(button)
    
    async def handle_role_press(self, interaction: discord.Interaction):
        custom_id: str = interaction.data.get("custom_id")
        button_label: str = ConfigManager.load('applications')['Ranks'][self.rank]['label']
        await interaction.response.send_modal(ApplicationModal(interactions.get(interaction.user.id), self.rank, custom_id, 1))
        step_one_embed = discord.Embed(
            title = f"{button_label} Application Process",
            description = ConfigManager.load('applications')['General']['APPLICATION_PROCESS_MESSAGE'],
            color = discord.Color.from_str(ConfigManager.get('EMBED_COLOR'))
        )
        logo_url = interaction.client.app.embeds.get_logo_url(ConfigManager.get("LOGO"))
        step_one_embed.set_footer(text=ConfigManager.get("FOOTER"), icon_url = logo_url)
        await interactions.get(interaction.user.id).edit_original_response(embed = step_one_embed, view = StepButtons(interactions.get(interaction.user.id), self.rank, custom_id, 1)) # self.rank == 'qa', 'staff' | Button.custom_id == 'factions', 'kitmap', 'lifesteal', 'youtuber', 'streamer', 'tiktoker'
