import discord
from core.config import ConfigManager


class StepButtons(discord.ui.View):
    def __init__(self, interaction: discord.Interaction, rank: str, role: str, step: int, answers: dict = None): # rank = custom_id of first button. role = custom_id of second button
        self.interaction: discord.Interaction = interaction
        self.rank: int = rank
        self.role: str = role
        self.step: int = step
        self.answers: dict = answers if answers is not None else {}
        print(self.answers)
        self.application_data: dict = ConfigManager.load("applications")
        super().__init__(timeout = None)
        self.add_buttons()

    def add_buttons(self):
        # Add go back button
        button = discord.ui.Button(
            label = f"Questions {self.step}/{len(ConfigManager.load('applications')['Ranks'][self.rank]['roles'][self.role]['steps'])}",
            custom_id = "prompt_question",
            style = discord.ButtonStyle.green
        )
        button.callback = self.send_modal
        self.add_item(button)
        # Add go forward button
    
    async def send_modal(self, interaction: discord.Interaction):
        from ui.modals.application_modal import ApplicationModal

        await interaction.response.send_modal(ApplicationModal(self.interaction, self.rank, self.role, self.step, self.answers))
