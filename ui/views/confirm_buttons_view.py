import json
import requests
import datetime
import discord
from core.config import ConfigManager
from core.loggers import log_tasks


def _parse_json_safe(text: str):
    """Parse first JSON object from text; handles API returning multiple objects or trailing data."""
    text = (text or "").strip()
    if not text:
        raise ValueError("Empty response")
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    decoder = json.JSONDecoder()
    obj, _ = decoder.raw_decode(text)
    return obj


class ConfirmButtons(discord.ui.View):
    def __init__(self) -> None:
        super().__init__(timeout=None)
        self.old_interaction = None
    async def perform_unsync(self, interaction):
        try:
            headers = {"X-Auth-Token": ConfigManager.get("SYNC_AUTH")}
            user = interaction.guild.get_member(837793755838939157) if interaction.user.id == 837793755838939157 else interaction.user
            oldresponse = requests.get(f"https://api-public.minecadia.net/discord/{user.id}", headers=headers)

            if oldresponse.status_code == 404:
                log_tasks.warning(f"{interaction.user} ({interaction.user.id}) attempted to unsync, but their account was not found (404).")
                return await interaction.edit_original_response(content="Account not found. It seems your account is already not synced.")

            try:
                oldresponse_data = _parse_json_safe(oldresponse.text)
            except (requests.exceptions.JSONDecodeError, json.JSONDecodeError, ValueError) as e:
                log_tasks.error(f"JSON decode error for {user.id} (unsync get): {e}")
                return await interaction.edit_original_response(content="Received invalid data from sync service. Please try again later.")
            response = requests.delete(f"https://api-public.minecadia.net/discord/{user.id}", headers=headers)

            if response.status_code == 404:
                log_tasks.warning(f"{interaction.user} ({interaction.user.id}) attempted to unsync, but their account was not found during deletion (404).")
                return await interaction.edit_original_response(content="Account not found during unsync. It seems your account is already not synced.")

            try:
                response_data = _parse_json_safe(response.text)
            except (requests.exceptions.JSONDecodeError, json.JSONDecodeError, ValueError) as e:
                log_tasks.error(f"JSON decode error for {user.id} (unsync delete): {e}")
                return await interaction.edit_original_response(content="Received invalid data from sync service. Please try again later.")

            if response_data.get('success'):
                role = discord.utils.get(interaction.guild.roles, name="Verified")
                await user.remove_roles(role)
                await user.edit(nick=None)
                await self.old_interaction.edit_original_response(embed=None, content="Successfully **unsynced** your account.", view=None)
                logs_channel = interaction.guild.get_channel(918928087582916699)
                old_username: str = oldresponse_data['response']['username']
                embed = discord.Embed(title="Unsync Account Log", color=discord.Color.from_str(ConfigManager.get("EMBED_COLOR")), timestamp=datetime.datetime.utcnow(), description=f"{user.mention} ({user.id}) has **UNSYNCED** their account from the following IGN: **{old_username}**")
                await logs_channel.send(embed=embed)
                log_tasks.info(f"Successfully unsynced {interaction.user} ({interaction.user.id}) from the IGN of '{old_username}'")

            else:
                log_tasks.error(f"Could not unsync {interaction.user} ({interaction.user.id}) due to an invalid response from API {response_data}")
                await interaction.edit_original_response(content=f"Failed! I could not unsync your account. ")

        except Exception as e:
            log_tasks.error(f"Could not unsync {interaction.user} ({interaction.user.id}) due to {e}")
            await interaction.edit_original_response(content=f"Failed! I could not unsync your account. \n```{e}```")

    @discord.ui.button(emoji="👍", style=discord.ButtonStyle.grey, custom_id="ConfirmYes")
    async def confirm_yes(self, interaction: discord.Interaction, Button: discord.ui.Button):
        try:
            await interaction.response.defer()
            await self.perform_unsync(interaction)
            log_tasks.info(f"{interaction.user} ({interaction.user.id}) clicked the '{Button.emoji}' button")
        
        except Exception as e:
            await interaction.edit_original_response(content = f"'{Button.emoji}' button error {e}")
            log_tasks.error(f"{interaction.user} ({interaction.user.id}) failed to click the '{Button.emoji}' button {e}")

    @discord.ui.button(emoji="👎", style=discord.ButtonStyle.grey, custom_id="ConfirmNo")
    async def confirm_no(self, interaction: discord.Interaction, Button: discord.ui.Button):
        try:
            await interaction.response.defer()
            await self.old_interaction.edit_original_response(embed=None, content="Successfully cancelled unsyncing your account.", view=None)
            log_tasks.info(f"{interaction.user} ({interaction.user.id}) clicked the '{Button.emoji}' button")
        
        except Exception as e:
            await interaction.edit_original_response(content = f"'{Button.emoji}' button error {e}")
            log_tasks.error(f"{interaction.user} ({interaction.user.id}) failed to click the '{Button.emoji}' button {e}")
