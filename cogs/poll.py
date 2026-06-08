from discord.ext import commands
from discord import app_commands
from typing import Literal
import discord

from core.config import ConfigManager
from core.database import execute
from ui.views.poll_buttons_view import PollButtons
class Poll(commands.Cog):
  def __init__(self, client: commands.Bot):
    self.client = client
  @app_commands.command(name="poll", description="Creates a new poll for members to vote on")
  @app_commands.checks.has_any_role(*ConfigManager.get("ADMIN_ROLES"))
  @app_commands.describe(title="The title of the poll", channel="The channel to send the poll to", option1_text="The text of the first poll button", option1color="Text color of the first poll button")
  async def poll(self, interaction: discord.Interaction, title:str, channel:discord.TextChannel, 
                 option1_text:str, option1color:Literal['Grey', 'Blue', 'Green', 'Red'], 
                 option2_text:str, option2color:Literal['Grey', 'Blue', 'Green', 'Red'], 
                 option3_text:str=None, option3color:Literal['Grey', 'Blue', 'Green', 'Red']=None, 
                 option4_text:str=None, option4color:Literal['Grey', 'Blue', 'Green', 'Red']=None, 
                 option5_text:str=None, option5color:Literal['Grey', 'Blue', 'Green', 'Red']=None):
    if interaction.guild is None:
            return await interaction.response.send_message(content="Commands cannot be ran in DMs!", ephemeral=True)
    def check(m):
      return m.author == interaction.user and m.channel == interaction.channel
      
    await interaction.response.send_message(content="Creating your poll... Please follow the instructions", ephemeral=True)

    embed = discord.Embed(color=discord.Color.from_str(ConfigManager.get("EMBED_COLOR")), description="Send the content of your poll description. Discord markdown is supported.")

    requesting_description = await interaction.channel.send(embed=embed)
    poll_description = await interaction.client.wait_for("message", check=check)
    option3_text = option3_text if option3_text else ""
    option4_text = option4_text if option4_text else ""
    option5_text = option5_text if option5_text else ""

    embed = discord.Embed(title=f"{title}", description=poll_description.content, color=discord.Color.from_str(ConfigManager.get("EMBED_COLOR")))
    logo_url = self.client.app.embeds.get_logo_url(ConfigManager.get("LOGO"))
    embed.set_footer(text=ConfigManager.get("FOOTER"), icon_url=logo_url)

    ButtonView = PollButtons()

    options = [
        {"text": option1_text, "color": COLOR_TO_STYLE.get(option1color)},
        {"text": option2_text, "color": COLOR_TO_STYLE.get(option2color)},
        {"text": option3_text, "color": COLOR_TO_STYLE.get(option3color)},
        {"text": option4_text, "color": COLOR_TO_STYLE.get(option4color)},
        {"text": option5_text, "color": COLOR_TO_STYLE.get(option5color)},
    ]

    buttons = [ButtonView.option_one, ButtonView.option_two, ButtonView.option_three, ButtonView.option_four, ButtonView.option_five]

    for i in range(5):
        button = buttons[i]
        option = options[i]
          
        if option["text"] and option["color"]:
            button.label = option["text"]
            button.style = option["color"]
            button.disabled = False

        else:
            ButtonView.remove_item(button)
            
    poll = await channel.send(embed=embed, view=ButtonView)
    import time as _time
    _ts = int(_time.time())
    await execute(
        "INSERT INTO polls (message_id, title, channel_id, option1_text, option2_text, option3_text, option4_text, option5_text, "
        "option1_votes, option2_votes, option3_votes, option4_votes, option5_votes, created_at) "
        "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, '', '', '', '', '', %s)",
        (poll.id, title, channel.id, option1_text, option2_text, option3_text, option4_text, option5_text, _ts),
    )
    await poll_description.delete()
    await requesting_description.delete()
      
    await interaction.edit_original_response(content=f"Poll Sent! {channel.mention}")



async def setup(client:commands.Bot) -> None:
  await client.add_cog(Poll(client))