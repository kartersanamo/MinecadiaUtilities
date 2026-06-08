import datetime
import discord
import json
from core.config import ConfigManager


class PollsSelectMenuView(discord.ui.View):
  def __init__(self):
    super().__init__(timeout=None)
    self.title: str
    self.interaction: discord.Interaction 

    with open("assets/config.json", "r") as file:
        self.data = json.load(file)

  async def manage_vote(self, interaction: discord.Interaction, action: str):
    select = SelectOption(interaction, self.interaction, self.title, action)
    await select.setup_options()  
    option_select_view = discord.ui.View() 
    option_select_view.add_item(select) 
    await interaction.response.send_message(view=option_select_view, ephemeral=True)

  async def close(self, interaction: discord.Interaction):
    try:
      await interaction.response.send_message(content= "Requesting poll closure...", ephemeral=True)
      
      close_poll_embed = discord.Embed(color=discord.Color.from_str(ConfigManager.get("EMBED_COLOR")), title="Close Poll Request", description="Are you sure that you want to close this poll? Closing any poll is `irreversible`, and will be unable to be further voted on or managed. All information of this poll will be lost after confirmation. You will receive a report sent of the final results. Please select below how you would like your report of the poll results (if any.)", timestamp=datetime.datetime.utcnow())
      logo_url = interaction.client.app.embeds.get_logo_url(ConfigManager.get("LOGO"))
      close_poll_embed.set_footer(text=ConfigManager.get("FOOTER"), icon_url=logo_url)
      
      close_view = ConfirmCloseView()
      close_view.add_item(ConfirmClose(self.interaction, interaction, self.title))
      await interaction.edit_original_response(content=None, embed=close_poll_embed, view=close_view)
    
    except Exception as Error:
      await interaction.edit_original_response(content=Error)

  @discord.ui.button(label="Close this poll",style=discord.ButtonStyle.red, disabled=True, custom_id="close_poll", row=0)
  async def close_poll(self, interaction:discord.Interaction, button: discord.ui.Button):
    await self.close(interaction)
  
  @discord.ui.button(label="+1 Vote", style=discord.ButtonStyle.gray, disabled=True, custom_id="add_one", row=1)
  async def add_one(self, interaction:discord.Interaction, button: discord.ui.Button):
    await self.manage_vote(interaction, "add a vote to")

  @discord.ui.button(label="-1 Vote", style=discord.ButtonStyle.gray, disabled=True, custom_id="remove_one", row=1)
  async def remove_one(self, interaction:discord.Interaction, button: discord.ui.Button):
    await self.manage_vote(interaction, "remove a vote from")
