import asyncio
import json
import requests
import datetime
import discord
from core.config import ConfigManager
from core.loggers import log_tasks
from ui.modals.enter_code_modal import EnterCode
from ui.views.confirm_buttons_view import ConfirmButtons
from ui.sync_support import get_verified_role, reply_ephemeral


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


def _fetch_discord_sync(user_id: int, headers: dict) -> requests.Response:
    return requests.get(
        f"https://api-public.minecadia.net/discord/{user_id}",
        headers=headers,
        timeout=10,
    )


class SyncButtons(discord.ui.View):
    def __init__(self) -> None:
        super().__init__(timeout=None)
        self.headers = {"X-Auth-Token": ConfigManager.get("SYNC_AUTH")}

    async def is_user_eligible(self, interaction):
        return interaction.user.joined_at.timestamp() + 900 <= datetime.datetime.now().timestamp()

    @discord.ui.button(label="Sync Account", style=discord.ButtonStyle.green, custom_id="Sync")
    async def sync_button(self, interaction: discord.Interaction, Button: discord.ui.Button):
        try:
            if not await self.is_user_eligible(interaction):
                log_tasks.warning(
                    f"{interaction.user} ({interaction.user.id}) has not been in the server "
                    "for 15 minutes to sync yet"
                )
                await reply_ephemeral(
                    interaction,
                    content=(
                        "You must be in this discord server for at least **fifteen minutes** "
                        "to sync. Please try again later!"
                    ),
                )
                return

            # Discord requires a response within 3 seconds — open the modal immediately.
            # Sync status / already-synced checks run in the modal submit handler.
            await interaction.response.send_modal(EnterCode())
            log_tasks.info(
                f"{interaction.user} ({interaction.user.id}) clicked the '{Button.label}' button"
            )

        except discord.NotFound:
            log_tasks.warning(
                f"Sync button interaction expired for {interaction.user} ({interaction.user.id})"
            )
        except Exception as e:
            log_tasks.error(
                f"{interaction.user} ({interaction.user.id}) failed to click the "
                f"'{Button.label}' button: {e}"
            )
            await reply_ephemeral(
                interaction,
                content="An unexpected error occurred. Please try again later.",
            )

    @discord.ui.button(label="Unsync Account", style=discord.ButtonStyle.red, custom_id="Unsync")
    async def unsync_button(self, interaction: discord.Interaction, Button: discord.ui.Button):
        try:
            if not await self.is_user_eligible(interaction):
                log_tasks.warning(
                    f"{interaction.user} ({interaction.user.id}) has not been in the server "
                    "for 15 minutes to unsync yet"
                )
                await reply_ephemeral(
                    interaction,
                    content=(
                        "You must be in this discord server for at least **fifteen minutes** "
                        "to unsync. Please try again later!"
                    ),
                )
                return

            await interaction.response.defer(ephemeral=True)

            original_response = await asyncio.to_thread(
                _fetch_discord_sync, interaction.user.id, self.headers
            )

            if original_response.status_code == 404:
                role = get_verified_role(interaction.guild)
                if role and role in interaction.user.roles:
                    await interaction.user.remove_roles(role)
                await reply_ephemeral(interaction, content="You are not currently synced.")
                log_tasks.info(
                    f"{interaction.user} ({interaction.user.id}) clicked the '{Button.label}' button"
                )
                return

            if original_response.status_code != 200:
                log_tasks.error(
                    f"API returned status {original_response.status_code} for {interaction.user.id}"
                )
                await reply_ephemeral(
                    interaction,
                    content="Unable to check sync status. Please try again later.",
                )
                return

            if not original_response.text or original_response.text.strip() == "":
                log_tasks.error(f"Empty response from API for {interaction.user.id}")
                await reply_ephemeral(
                    interaction,
                    content="Received invalid response from sync service. Please try again later.",
                )
                return

            try:
                response = _parse_json_safe(original_response.text)
            except (requests.exceptions.JSONDecodeError, json.JSONDecodeError, ValueError) as json_err:
                log_tasks.error(f"JSON decode error for {interaction.user.id}: {json_err}")
                await reply_ephemeral(
                    interaction,
                    content="Received invalid data from sync service. Please try again later.",
                )
                return

            if response.get('success'):
                embed = discord.Embed(
                    description="Are you sure you'd like to **unsync** your account?",
                    color=discord.Color.from_str(ConfigManager.get("EMBED_COLOR")),
                )
                logo_url = interaction.client.app.embeds.get_logo_url(ConfigManager.get("LOGO"))
                embed.set_footer(text=ConfigManager.get("FOOTER"), icon_url=logo_url)

                buttons = ConfirmButtons()
                buttons.old_interaction = interaction

                await reply_ephemeral(interaction, embed=embed, view=buttons)
            else:
                role = get_verified_role(interaction.guild)
                if role and role in interaction.user.roles:
                    await interaction.user.remove_roles(role)
                await reply_ephemeral(interaction, content="You are not currently synced.")

            log_tasks.info(
                f"{interaction.user} ({interaction.user.id}) clicked the '{Button.label}' button"
            )

        except requests.exceptions.Timeout:
            await reply_ephemeral(
                interaction,
                content="The sync service is taking too long to respond. Please try again later.",
            )
            log_tasks.error(
                f"Timeout when checking sync status for {interaction.user} ({interaction.user.id})"
            )

        except requests.exceptions.RequestException as req_err:
            await reply_ephemeral(
                interaction,
                content="Unable to connect to sync service. Please try again later.",
            )
            log_tasks.error(
                f"Request error for {interaction.user} ({interaction.user.id}): {req_err}"
            )

        except discord.Forbidden:
            await reply_ephemeral(
                interaction,
                content="I don't have permission to manage your roles.",
            )
            log_tasks.error(
                f"Missing permissions to remove role from {interaction.user} ({interaction.user.id})"
            )

        except Exception as e:
            await reply_ephemeral(
                interaction,
                content="An unexpected error occurred. Please try again later.",
            )
            log_tasks.error(
                f"{interaction.user} ({interaction.user.id}) failed to click the "
                f"'{Button.label}' button: {e}"
            )
