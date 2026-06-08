from discord.ext import commands
from discord import app_commands
import datetime
import discord

from core.config import ConfigManager
from services.poll_service import return_polls
from ui.views.polls_select_menu_view import PollsSelectMenu
from ui.views.polls_select_menu_view_managepolls import PollsSelectMenuView

class ManagePolls(commands.Cog):
  def __init__(self, client: commands.Bot):
    self.client = client
  @app_commands.command(name="manage-polls", description="Manages all of the currently opened polls")
  @app_commands.checks.has_any_role(*ConfigManager.get("ADMIN_ROLES"))
  async def manage_polls(self, interaction: discord.Interaction):
    if interaction.guild is None:
            return await interaction.response.send_message(content="Commands cannot be ran in DMs!", ephemeral=True)
    await interaction.response.send_message(content="Loading poll manager...", ephemeral=True)
        
    poll_manager_embed = discord.Embed(title="Poll Manager", description="Loading poll information on `Awaiting Selection`...", color=discord.Color.from_str(ConfigManager.get("EMBED_COLOR")), timestamp=datetime.datetime.utcnow())
    logo_url = self.client.app.embeds.get_logo_url(ConfigManager.get("LOGO"))
    poll_manager_embed.set_footer(text=ConfigManager.get("FOOTER"), icon_url=logo_url)
    poll_manager_embed.set_image(url=logo_url)

    all_polls = return_polls()
    if not all_polls:
      poll_manager_embed.description = "Failed! There are no polls open right now."
      poll_manager_embed.set_image(url=None)
      return await interaction.edit_original_response(content=None, embed=poll_manager_embed)
      
    select_menu_view = PollsSelectMenuView()

    buttons = select_menu_view.children
    for child in buttons:
      select_menu_view.remove_item(child)
      
    select_menu_view.add_item(PollsSelectMenu(interaction))
    for button in buttons:
      button.row = 1
      select_menu_view.add_item(button)
  
    await interaction.edit_original_response(content=None, embed=poll_manager_embed, view=select_menu_view)


async def setup(client:commands.Bot) -> None:
  await client.add_cog(ManagePolls(client))