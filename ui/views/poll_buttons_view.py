import discord
import json
from core.database import execute


class PollButtons(discord.ui.View):
  def __init__(self) -> None:
    super().__init__(timeout=None)

    with open("assets/config.json", "r") as file:
        self.data = json.load(file)
  
  async def handle_button_press(self, interaction: discord.Interaction, num: int, text: str):
      try:
          await interaction.response.send_message("Attempting to add your vote...", ephemeral=True)
          message_id = str(interaction.message.id)
          
          row = await execute("SELECT * FROM polls WHERE message_id = %s", (message_id,))
          row = row[0] if row else None
          
          if not row:
              await interaction.edit_original_response(content="Poll not found.")
              return
          
          option_votes = [row[f'option{index}_votes'].split("___") for index in range(1, 6)]
          user_id = str(interaction.user.id)
          
          async def manage_vote(option_index):
              option_name = row[f'option{option_index+1}_text']
              
              if user_id in option_votes[option_index]:
                  option_votes[option_index].remove(user_id)
                  result = f"Removed your vote on **{option_name}**."
              else:
                  other_voted_option = None
                  for index, item in enumerate(option_votes):
                      if user_id in item:
                          other_voted_option = row[f'option{index+1}_text']
                  if other_voted_option:
                      result = f"Failed! You already have a vote on **{other_voted_option}**. Click it again to remove it!"
                  else:
                      option_votes[option_index].append(user_id)
                      result = f"Added your vote to **{option_name}**."
                      try:
                          from core.analytics import logger as analytics
                          analytics.record_poll_vote(message_id, user_id, option_index)
                      except Exception:
                          pass
              
              combined = "___".join(option_votes[option_index])
              vote_col = f"option{option_index+1}_votes"
              await execute(
                  f"UPDATE polls SET `{vote_col}` = %s WHERE message_id = %s",
                  (combined, message_id),
              )
              return result
          
          if 1 <= num <= 5:
              await interaction.edit_original_response(content=await manage_vote(num-1))

      except Exception as Error:
          await interaction.edit_original_response(content=str(Error))


  @discord.ui.button(label="OptionOne", style=discord.ButtonStyle.gray, disabled=True, custom_id="optionone")
  async def option_one(self, interaction: discord.Interaction, button: discord.ui.Button):
    await self.handle_button_press(interaction, 1, self.option_one.label)
  
  @discord.ui.button(label="OptionTwo", style=discord.ButtonStyle.gray, disabled=True, custom_id="optiontwo")
  async def option_two(self, interaction: discord.Interaction, button: discord.ui.Button):
    await self.handle_button_press(interaction, 2, self.option_two.label)

  @discord.ui.button(label="OptionThree", style=discord.ButtonStyle.gray, disabled=True, custom_id="optionthree")
  async def option_three(self, interaction: discord.Interaction, button: discord.ui.Button):
    await self.handle_button_press(interaction, 3, self.option_three.label)

  @discord.ui.button(label="OptionFour", style=discord.ButtonStyle.gray, disabled=True, custom_id="optionfour")
  async def option_four(self, interaction: discord.Interaction, button: discord.ui.Button):
    await self.handle_button_press(interaction, 4, self.option_four.label)

  @discord.ui.button(label="OptionFive", style=discord.ButtonStyle.gray, disabled=True, custom_id="optionfive")
  async def option_five(self, interaction: discord.Interaction, button: discord.ui.Button):
    await self.handle_button_press(interaction, 5, self.option_five.label)
