import discord
import json
from core.database import execute
from services.poll_service import update_original


class RemoveMember(discord.ui.Select):
  def __init__(self, interaction: discord.Interaction, old_interaction: discord.Interaction, title: str, option: str, old_votes: str, which_vote: str):
    self.interaction = interaction
    self.old_interaction = old_interaction
    self.title = title
    self.option = option
    self.old_votes = old_votes
    self.which_vote = which_vote
    self.member_votes = [discord.utils.get(interaction.guild.members, id=int(vote)) for vote in self.old_votes.split("___") if vote]
    options = [discord.SelectOption(label=member_obj.display_name) for member_obj in list(set(self.member_votes))]
    super().__init__(placeholder=f"Select a member to remove their vote...", options=options)

    with open("assets/config.json", "r") as file:
        self.data = json.load(file)

  async def callback(self, interaction: discord.Interaction):
    member_object = discord.utils.get(interaction.guild.members, name=self.values[0])
    new_votes = self.old_votes.replace("___"+str(member_object.id), "", 1)
    await execute(
        f"UPDATE polls SET `option{self.which_vote}_votes` = %s WHERE `title` = %s",
        (new_votes, self.title),
    )
    await self.interaction.edit_original_response(view=None, content=f"Successly removed one of **{self.values[0]}**'s votes for the option **{self.option}** in the poll `{self.title}`.") 
    await self.old_interaction.edit_original_response(embed=await update_original(interaction, self.title))
