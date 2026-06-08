import asyncio
import datetime
import json

import discord
import requests
from discord import ui

from core.config import ConfigManager
from core.loggers import log_tasks
from ui.sync_support import get_verified_role, refresh_verify_panel


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


def _sync_headers() -> dict[str, str]:
    return {"X-Auth-Token": ConfigManager.get("SYNC_AUTH")}


def _sync_put(user_id: int, code: int) -> requests.Response:
    return requests.put(
        f"https://api-public.minecadia.net/discord/{user_id}",
        headers=_sync_headers(),
        json={"sync_code": code},
        timeout=15,
    )


def _sync_get(user_id: int) -> requests.Response:
    return requests.get(
        f"https://api-public.minecadia.net/discord/{user_id}",
        headers=_sync_headers(),
        timeout=15,
    )


class EnterCode(ui.Modal, title="Enter your verification code below"):
    code = ui.TextInput(
        label="What is the code that was provided to you?",
        style=discord.TextStyle.short,
        max_length=12,
    )

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        try:
            try:
                code = int(str(self.code.value).strip())
            except (TypeError, ValueError):
                log_tasks.warning(
                    f"{interaction.user} ({interaction.user.id}) entered an invalid code "
                    f"'{self.code.value}'"
                )
                await interaction.edit_original_response(
                    content="Invalid verification code. Please try again."
                )
                return

            response = await asyncio.to_thread(_sync_put, interaction.user.id, code)

            if response.status_code == 404:
                log_tasks.warning(
                    f"{interaction.user} ({interaction.user.id}) attempted to sync, "
                    "but their account was not found (404)."
                )
                await interaction.edit_original_response(
                    content=(
                        "Account not found. Please ensure you have registered before syncing."
                    )
                )
                return

            try:
                response_data = _parse_json_safe(response.text)
            except (requests.exceptions.JSONDecodeError, json.JSONDecodeError, ValueError) as e:
                log_tasks.error(
                    f"JSON decode error for {interaction.user.id} (sync submit): {e}"
                )
                await interaction.edit_original_response(
                    content="Received invalid data from sync service. Please try again later."
                )
                return

            if not response_data.get("success"):
                log_tasks.error(
                    f"Could not verify {interaction.user} ({interaction.user.id}) "
                    f"due to an invalid response from API {response_data}"
                )
                await interaction.edit_original_response(
                    content="Invalid verification code. Please try again."
                )
                return

            guild = interaction.guild
            if guild is None:
                await interaction.edit_original_response(
                    content="This command can only be used in a server."
                )
                return

            verified_role = get_verified_role(guild)
            if verified_role is None:
                await interaction.edit_original_response(
                    content="Verified role is not configured. Please contact staff."
                )
                return

            member = guild.get_member(interaction.user.id)
            if member is None:
                try:
                    member = await guild.fetch_member(interaction.user.id)
                except discord.HTTPException:
                    member = None
            if member is None:
                await interaction.edit_original_response(
                    content="Could not resolve your server membership. Try again."
                )
                return

            await member.add_roles(verified_role, reason="Minecadia account sync")
            await interaction.edit_original_response(
                content=(
                    "You have successfully completed the verification process and "
                    "**synced** your account."
                )
            )

            profile_response = await asyncio.to_thread(_sync_get, interaction.user.id)
            if profile_response.status_code == 404:
                log_tasks.warning(
                    f"{interaction.user} ({interaction.user.id}) attempted to fetch synced "
                    "data, but their account was not found (404)."
                )
                await interaction.edit_original_response(
                    content=(
                        "Account synced, but profile lookup failed. Please contact support "
                        "if your nickname did not update."
                    )
                )
                return

            try:
                profile_data = _parse_json_safe(profile_response.text)
            except (requests.exceptions.JSONDecodeError, json.JSONDecodeError, ValueError) as e:
                log_tasks.error(
                    f"JSON decode error for {interaction.user.id} (sync fetch): {e}"
                )
                return

            username = profile_data.get("response", {}).get("username")
            if not username:
                return

            logs_channel_id = int(ConfigManager.get("SYNC_LOGS_CHANNEL_ID") or 0)
            logs_channel = guild.get_channel(logs_channel_id)
            if isinstance(logs_channel, discord.TextChannel):
                description = (
                    f"{interaction.user.mention} ({interaction.user.id}) has **SYNCED** "
                    f"their account with the following IGN: **{username}**"
                )
                embed = discord.Embed(
                    title="Sync Account Log",
                    description=description,
                    color=discord.Color.from_str(ConfigManager.get("EMBED_COLOR")),
                    timestamp=datetime.datetime.now(datetime.timezone.utc),
                )
                await logs_channel.send(embed=embed)

            try:
                await member.edit(nick=str(username)[:32], reason="Minecadia account sync")
            except discord.Forbidden:
                log_tasks.warning(
                    f"Could not change {interaction.user} ({interaction.user.id})'s nickname "
                    "due to missing permissions."
                )
                await interaction.edit_original_response(
                    content=(
                        "You have successfully completed the verification process and "
                        "**synced** your account.\n"
                        "`Note: I could not change your nickname due to missing permissions.`"
                    )
                )

            log_tasks.info(
                f"Successfully synced {interaction.user} ({interaction.user.id}) "
                f"with the IGN of '{username}'"
            )

        except Exception as e:
            log_tasks.error(
                f"Could not verify {interaction.user} ({interaction.user.id}) due to {e}"
            )
            try:
                await interaction.edit_original_response(
                    content="Failed! I could not verify your account. Please try again later."
                )
            except discord.HTTPException:
                pass
        finally:
            await refresh_verify_panel(interaction)
