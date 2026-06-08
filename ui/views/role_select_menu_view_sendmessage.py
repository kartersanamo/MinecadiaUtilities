import discord
from ui.views.role_select_menu_view import RoleSelectMenu


class RoleSelectMenuView(discord.ui.View):
    def __init__(self, interaction: discord.Interaction):
        super().__init__(timeout=None)
        self.interaction = interaction
        self.add_item(RoleSelectMenu(self.interaction))
