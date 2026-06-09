import datetime
import json

import discord
import requests

from core.config import ConfigManager
from core.loggers import log_tasks
from ui.sync_support import get_verified_role


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
                role = get_verified_role(interaction.guild)
                if role and role in user.roles:
                    await user.remove_roles(role)
                await user.edit(nick=None)
                await self.old_interaction.edit_original_response(
                    embed=None,
                    content="Successfully **unsynced** your account.",
                    view=None,
                )
                old_username: str = oldresponse_data['response']['username']
                from core.logging.http_client import post_audit_log

                await post_audit_log(
                    event_type="account.unsync",
                    title="Account Unsynced",
                    summary=(
                        f"{user.mention} ({user.id}) unsynced "
                        f"from IGN **{old_username}**"
                    ),
                    actor_id=user.id,
                    guild_id=interaction.guild.id if interaction.guild else None,
                    source_bot="Utilities",
                    metadata={"ign": old_username},
                )
                log_tasks.info(f"Successfully unsynced {interaction.user} ({interaction.user.id}) from the IGN of '{old_username}'")

            else:
                log_tasks.error(
                    f"Could not unsync {interaction.user} ({interaction.user.id}) due to an "
                    f"invalid response from API {response_data}"
                )
                await interaction.edit_original_response(
                    content="Failed! I could not unsync your account."
                )

        except Exception as e:
            log_tasks.error(
                f"Could not unsync {interaction.user} ({interaction.user.id}) due to {e}"
            )
            await interaction.edit_original_response(
                content="Failed! I could not unsync your account. Please try again later."
            )

    @discord.ui.button(emoji="👍", style=discord.ButtonStyle.grey, custom_id="ConfirmYes")
    async def confirm_yes(self, interaction: discord.Interaction, Button: discord.ui.Button):
        try:
            await interaction.response.defer(ephemeral=True)
            await self.perform_unsync(interaction)
            log_tasks.info(
                f"{interaction.user} ({interaction.user.id}) clicked the '{Button.emoji}' button"
            )

        except Exception as e:
            await interaction.edit_original_response(
                content="Something went wrong while unsyncing. Please try again."
            )
            log_tasks.error(
                f"{interaction.user} ({interaction.user.id}) failed to click the "
                f"'{Button.emoji}' button {e}"
            )

    @discord.ui.button(emoji="👎", style=discord.ButtonStyle.grey, custom_id="ConfirmNo")
    async def confirm_no(self, interaction: discord.Interaction, Button: discord.ui.Button):
        try:
            await interaction.response.defer(ephemeral=True)
            await self.old_interaction.edit_original_response(
                embed=None,
                content="Successfully cancelled unsyncing your account.",
                view=None,
            )
            await interaction.edit_original_response(
                content="Unsync cancelled.",
                embed=None,
                view=None,
            )
            log_tasks.info(
                f"{interaction.user} ({interaction.user.id}) clicked the '{Button.emoji}' button"
            )

        except Exception as e:
            await interaction.edit_original_response(
                content="Something went wrong. Please try again."
            )
            log_tasks.error(
                f"{interaction.user} ({interaction.user.id}) failed to click the "
                f"'{Button.emoji}' button {e}"
            )
