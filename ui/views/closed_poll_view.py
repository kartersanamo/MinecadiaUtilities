import discord


class ClosedPoll(discord.ui.View):
  def __init__(self):
    super().__init__(timeout=None)
  
  @discord.ui.button(label="Poll has been closed!", style=discord.ButtonStyle.grey, disabled=True, custom_id="poll_has_been_closed")
  async def closed_poll(self, interaction: discord.Interaction, button: discord.ui.Button):
    pass
