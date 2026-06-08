import datetime
import discord
import json
from core.config import ConfigManager
from core.database import execute
from services.poll_service import create_embed_field, get_poll_info, return_polls


class ConfirmClose(discord.ui.Select):
  def __init__(self, old_interaction: discord.Interaction, interaction: discord.Interaction, title: str):
    self.old_interaction = old_interaction
    self.interaction = interaction
    self.title = title
    options = [discord.SelectOption(label="Results Sent Here & No Names"),
               discord.SelectOption(label="Results Sent Here & Names"),
               discord.SelectOption(label="Results Sent In Poll Channel & No Names"),
               discord.SelectOption(label="Results Sent In Poll Channel & Names"),
               discord.SelectOption(label="Cancel")]
    super().__init__(placeholder="Please choose an option below...", options=options)

    with open("assets/config.json", "r") as file:
        self.data = json.load(file)

  async def reset_manager(self, interaction: discord.Interaction):
    poll_manager_embed = discord.Embed(title="Poll Manager", description="Loading poll information on `Awaiting Selection`...", color=discord.Color.from_str(ConfigManager.get("EMBED_COLOR")), timestamp=datetime.datetime.utcnow())
    logo_url = interaction.client.app.embeds.get_logo_url(ConfigManager.get("LOGO"))
    poll_manager_embed.set_footer(text=ConfigManager.get("FOOTER"), icon_url=logo_url)
    poll_manager_embed.set_image(url=logo_url)

    all_polls = return_polls()
    if not all_polls:
      poll_manager_embed.description = "Failed! There are no polls open right now."
      poll_manager_embed.set_image(url=None)
      return await self.old_interaction.edit_original_response(content=None, embed=poll_manager_embed, view=None)
    
    select_menu_view = PollsSelectMenuView()

    buttons = select_menu_view.children
    for child in buttons:
      select_menu_view.remove_item(child)
      
    select_menu_view.add_item(PollsSelectMenu(interaction))
    for button in buttons:
      button.row = 1
      select_menu_view.add_item(button)
  
    await self.old_interaction.edit_original_response(content=None, embed=poll_manager_embed, view=select_menu_view)

  async def callback(self, interaction: discord.Interaction):
    try:
      await interaction.response.defer()
      await self.interaction.edit_original_response(content="Attempting to close the poll. *(this usually takes around 10 seconds)*", embed=None, view=None)
      
      chosen_option = self.values[0]
      
      if chosen_option == "Cancel":
        return await self.interaction.edit_original_response(content="Successfully cancelled closing this poll!", view=None, embed=None)
      
      poll_info = get_poll_info(self.title)
    
      message = None
      for channel in interaction.guild.channels:
        try:
          message = await channel.fetch_message(int(poll_info['message_id']))
          channel = channel
          break

        except Exception:
          continue
      
      if message:
        await message.edit(view=ClosedPoll())

        results_embed = discord.Embed(title="Poll Results!", description=f"Here are the poll results for the poll `{self.title}`...", color=discord.Color.from_str(ConfigManager.get("EMBED_COLOR")), timestamp=datetime.datetime.utcnow())
        logo_url = interaction.client.app.embeds.get_logo_url(ConfigManager.get("LOGO"))
        results_embed.set_footer(text=ConfigManager.get("FOOTER"), icon_url=logo_url)
        
        names = False if "No" in chosen_option else True
        for value in list(poll_info.keys()):
          if (("text" in value)==True) and ((poll_info[value]!="")==True):
            results_embed.add_field(**await create_embed_field(interaction, poll_info, ''.join(num for num in value if num.isdigit()), names))

        await execute("DELETE FROM polls WHERE `message_id` = %s", (poll_info["message_id"],))
        
        result_channel = channel if "Poll" in chosen_option else interaction.channel

        await result_channel.send(embed=results_embed)
        await self.reset_manager(interaction)
        await self.interaction.edit_original_response(content=f"Successfully closed this poll! {chosen_option}", view=None, embed=None)

      else:
        return await interaction.edit_original_response(content="Failed! Poll message not found!")

    except Exception as Error:
      await interaction.edit_original_response(content=Error)
