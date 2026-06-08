from discord import ui
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


class EnterCode(ui.Modal):
    def __init__(self) -> None:
        super().__init__(title="Enter your verification code below", timeout=None, custom_id="enter_code_modal")

        self.add_item(ui.TextInput(label="What is the code that was provided to you?", style=discord.TextStyle.short))
    async def on_submit(self, interaction: discord.Interaction):
        try:
            await interaction.response.send_message(content="Checking your verification code...", ephemeral=True)

            try:
                code = int(self.children[0].value)

            except Exception:
                log_tasks.warning(f"{interaction.user} ({interaction.user.id}) entered an invalid code '{self.children[0].value}'")
                return await interaction.edit_original_response(content="Invalid verification code. Please try again.")

            headers = {"X-Auth-Token": ConfigManager.get("SYNC_AUTH")}
            response = requests.put(f"https://api-public.minecadia.net/discord/{interaction.user.id}", headers=headers, json={"sync_code": code})

            if response.status_code == 404:
                log_tasks.warning(f"{interaction.user} ({interaction.user.id}) attempted to sync, but their account was not found (404).")
                return await interaction.edit_original_response(content="Account not found. Please ensure you have registered before syncing.")

            try:
                response_data = _parse_json_safe(response.text)
            except (requests.exceptions.JSONDecodeError, json.JSONDecodeError, ValueError) as e:
                log_tasks.error(f"JSON decode error for {interaction.user.id} (sync submit): {e}")
                return await interaction.edit_original_response(content="Received invalid data from sync service. Please try again later.")

            if response_data.get('success'):
                role = discord.utils.get(interaction.guild.roles, name="Verified")
                await interaction.user.add_roles(role)
                await interaction.edit_original_response(content="You have successfully completed the verification process and **synced** your account.")

                response = requests.get(f"https://api-public.minecadia.net/discord/{interaction.user.id}", headers=headers)

                if response.status_code == 404:
                    log_tasks.warning(f"{interaction.user} ({interaction.user.id}) attempted to fetch synced data, but their account was not found (404).")
                    return await interaction.edit_original_response(content="Account not found after syncing. Please contact support.")

                try:
                    response_data = _parse_json_safe(response.text)
                except (requests.exceptions.JSONDecodeError, json.JSONDecodeError, ValueError) as e:
                    log_tasks.error(f"JSON decode error for {interaction.user.id} (sync fetch): {e}")
                    return await interaction.edit_original_response(content="Received invalid data from sync service. Please try again later.")
                username: str = response_data['response']['username']
                description = f"{interaction.user.mention} ({interaction.user.id}) has **SYNCED** their account with the following IGN: **{username}**"
                embed = discord.Embed(title="Sync Account Log", description=description, color=discord.Color.from_str(ConfigManager.get("EMBED_COLOR")), timestamp=datetime.datetime.utcnow())
                logs_channel = interaction.guild.get_channel(918928087582916699)
                await logs_channel.send(embed=embed)

                try:
                    await interaction.user.edit(nick=username)

                except Exception:
                    log_tasks.warning(f"Could not change {interaction.user} ({interaction.user.id})'s nickname due to missing permissions.")
                    await interaction.edit_original_response(content="You have successfully completed the verification process and **synced** your account.\n`ERROR: I could not change your nickname due to missing permissions.`")

                log_tasks.info(f"Successfully synced {interaction.user} ({interaction.user.id}) with the IGN of '{username}'")

            else:
                log_tasks.error(f"Could not verify {interaction.user} ({interaction.user.id}) due to an invalid response from API {response_data}")
                return await interaction.edit_original_response(content="Invalid verification code. Please try again.")

        except Exception as e:
            log_tasks.error(f"Could not verify {interaction.user} ({interaction.user.id}) due to {e}")
            await interaction.edit_original_response(content=f"Failed! I could not verify your account. \n```{e}```")
