import discord
import json
from core.database import execute
from services.poll_service import get_poll_info, update_original


class SelectOption(discord.ui.Select):
  def __init__(self, interaction: discord.Interaction, old_interaction: discord.Interaction, title: str, action: str):
        self.interaction = interaction
        self.old_interaction = old_interaction
        self.title = title
        self.action = action

        with open("assets/config.json", "r") as file:
            self.data = json.load(file)

        super().__init__(placeholder=f"Select an item to {self.action}...", options=[discord.SelectOption(label = "Temp")])

  async def setup_options(self):
        opt = await self.return_options(self.title)
        options = [discord.SelectOption(label=label) for label in opt]
        self.options = options 

  async def return_options(self, title: str):
        row = await execute("SELECT * FROM polls WHERE `title` = %s", (title,))
        row = row[0] if row else None
        
        options = []
        if row:
            for i in range(1, 6):
                if row.get(f"option{i}_text"):
                    options.append(row[f"option{i}_text"])
        return options
  
  async def callback(self, interaction: discord.Interaction):
    await interaction.response.defer()
    option = self.values[0]
    poll_information = get_poll_info(self.title)
    for value in list(poll_information.keys()):
      if option==poll_information[value]:
        which_vote = value.replace("option", "").split("_")[0]
        old_votes = poll_information[f"option{which_vote}_votes"]
        break
    if self.action=="add a vote to":
      await execute(
          f"UPDATE polls SET `option{which_vote}_votes` = %s WHERE `title` = %s",
          (old_votes + "___988616371917180929", self.title),
      )
      await self.old_interaction.edit_original_response(embed=await update_original(interaction, self.title))
      await self.interaction.edit_original_response(view=None, content=f"Successly added a vote to `{self.title}` for **{option}**.")
    elif self.action=="remove a vote from":
      if old_votes=="" or old_votes=="___":
        await self.interaction.edit_original_response(view=None, content="Failed! This option has no votes on it.")
      else:
        member_select_view = RemoveMemberView()
        member_select_view.add_item(RemoveMember(self.interaction, self.old_interaction, self.title, option, old_votes, which_vote))
        await self.interaction.edit_original_response(view=member_select_view)
