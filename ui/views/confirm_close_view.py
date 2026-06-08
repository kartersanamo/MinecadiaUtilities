import discord


class ConfirmCloseView(discord.ui.View):
  def __init__(self):
    super().__init__(timeout=None)
