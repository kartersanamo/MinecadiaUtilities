import discord


class RemoveMemberView(discord.ui.View):
  def __init__(self):
    super().__init__(timeout=None)
