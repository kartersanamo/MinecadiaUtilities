import datetime
import discord
import json
from core.config import ConfigManager
from services.poll_service import create_embed_field, get_poll_info, return_polls


class PollsSelectMenu(discord.ui.Select):
  def __init__(self, interaction: discord.Interaction):
    self.interaction = interaction

    labels = [row['title'] for row in return_polls()]
    options = [discord.SelectOption(label=label) for label in labels]
    super().__init__(placeholder="Select a poll to manage...", options=options)

    with open("assets/config.json", "r") as file:
        self.data = json.load(file)

  async def update_buttons(self, view: discord.ui.View):
    view.close_poll.disabled = False
    view.add_one.disabled = False
    view.remove_one.disabled = False

  async def callback(self, interaction: discord.Interaction):
    try:
      await interaction.response.defer()
      
      choice = self.values[0]
      poll_information = get_poll_info(choice)

      new_embed = discord.Embed(title="Poll Manager", description=f"Loading poll information on `{choice}`...", color=discord.Color.from_str(ConfigManager.get("EMBED_COLOR")), timestamp=datetime.datetime.utcnow())
      logo_url = interaction.client.app.embeds.get_logo_url(ConfigManager.get("LOGO"))
      new_embed.set_footer(text=ConfigManager.get("FOOTER"), icon_url=logo_url)
      
      for value in list(poll_information.keys()):
        if (("text" in value)==True) and ((poll_information[value]!="")==True):
          new_embed.add_field(**await create_embed_field(interaction, poll_information, ''.join(num for num in value if num.isdigit()), True))

      select_menu_view = PollsSelectMenuView()
      select_menu_view.title = choice
      await self.update_buttons(select_menu_view)

      select_menu_view.interaction = self.interaction

      buttons = select_menu_view.children
      for child in buttons:
        select_menu_view.remove_item(child)
      
      select_menu_view.add_item(PollsSelectMenu(self.interaction))
      for button in buttons:
        button.row = 1
        select_menu_view.add_item(button)
      
      await self.interaction.edit_original_response(embed=new_embed, view=select_menu_view)

    except Exception as Error:
      await interaction.edit_original_response(content=Error)
