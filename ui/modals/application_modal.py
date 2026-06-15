import random
import requests
import datetime
import discord
import gspread
import os
from core.config import ConfigManager
from core.loggers import log_tasks


def _collect_modal_answers(modal: discord.ui.Modal, answers: dict, user_id: int) -> None:
    if user_id not in answers:
        answers[user_id] = {}
    for child in modal.children:
        if isinstance(child, discord.ui.Label):
            answers[user_id][child.text] = child.component.value
        elif isinstance(child, discord.ui.TextInput):
            answers[user_id][child.custom_id] = child.value


class ApplicationModal(discord.ui.Modal):
    def __init__(self, interaction: discord.Interaction, rank: str, role: str, step: int, answers: dict = None): # rank = custom_id of first button. role = custom_id of second button
        self.interaction: discord.Interaction = interaction
        self.rank: int = rank
        self.role: str = role
        self.step: int = step
        self.application_data: dict = ConfigManager.load("applications")
        self.total_steps: int = len(ConfigManager.load('applications')['Ranks'][self.rank]['roles'][self.role]['steps'])
        self.step_data = ConfigManager.load('applications')['Ranks'][self.rank]['roles'][self.role]['steps'][self.step - 1]
        self.application_name: str = ConfigManager.load('applications')['Ranks'][self.rank]['roles'][self.role]['label']
        self.answers: dict = answers if answers is not None else {}
        custom_id = str(random.randint(0, 50000000000))
        super().__init__(
            title = f"({self.step}/{self.total_steps}) {self.step_data['label']}",
            timeout = None,
            custom_id = custom_id
        )
        self.add_fields()
    
    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer()
        _collect_modal_answers(self, self.answers, interaction.user.id)
        # Is not the final step yet
        if self.step < self.total_steps:
            from ui.views.step_buttons_modal import StepButtons

            self.step += 1
            view: discord.View = StepButtons(self.interaction, self.rank, self.role, self.step, self.answers)
            step_embed = discord.Embed(
                title = f"{self.application_name} Application Process",
                description = ConfigManager.load('applications')['General']['APPLICATION_PROCESS_MESSAGE'],
                color = discord.Color.from_str(ConfigManager.get('EMBED_COLOR'))
            )
            logo_url = interaction.client.app.embeds.get_logo_url(ConfigManager.get("LOGO"))
            step_embed.set_footer(text = ConfigManager.get("FOOTER"), icon_url = logo_url)
            for child in self.answers[interaction.user.id].keys():
                step_embed.add_field(
                    name = child, 
                    value = self.answers[interaction.user.id][child], 
                    inline = False
                )
            await self.interaction.edit_original_response(view = view, embed = step_embed)
        # Is the final step
        else:
            spreadsheet_name: str = ConfigManager.load('applications')['Ranks'][self.rank]['spreadsheet_name']
            telegram_chat_id: int = ConfigManager.load('applications')['Ranks'][self.rank]['telegram_chat_id']
            credentials: str = os.getenv('GOOGLE_SHEETS_CREDENTIALS') or ConfigManager.load('applications')['General'].get('GOOGLE_SHEETS_CREDENTIALS', '')
            telegram_bot_token: str = os.getenv('TELEGRAM_BOT_TOKEN') or ConfigManager.load('applications')['General'].get('TELEGRAM_BOT_TOKEN', '')

            try:
                if not credentials:
                    raise ValueError("GOOGLE_SHEETS_CREDENTIALS is not configured")
                service_account = gspread.service_account(filename=credentials)
                spreadsheet = service_account.open(spreadsheet_name)
                wkst = spreadsheet.worksheet(ConfigManager.load('applications')['Ranks'][self.rank]['roles'][self.role.lower()]['label'])
                body = ["Pending", datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), f"{interaction.user.name} ({interaction.user.id})"]
                body.extend(list(self.answers[interaction.user.id].values()))
                wkst.append_row(body, table_range = "D4:O4")
            except Exception as e:
                err = str(e)
                if "invalid_grant" in err or "Invalid JWT Signature" in err:
                    log_tasks.error(
                        "Google Sheets auth failed: the service account key in "
                        "GOOGLE_SHEETS_CREDENTIALS is invalid or revoked. Regenerate the "
                        "JSON key in Google Cloud Console and replace the credentials file."
                    )
                else:
                    log_tasks.error(f"Error updating Google Sheet: {e}")

            # Send telegram notification to the correct group chat
            try:
                telegram_message: str = f"{self.application_name} {interaction.user.name} ({interaction.user.id})\n"
                for question in self.answers[interaction.user.id].keys():
                    telegram_message += f"{question}\n\t{self.answers[interaction.user.id][question]}\n\n"
                payload = {
                    'chat_id':telegram_chat_id, 
                    'text': telegram_message
                }
                response = requests.post(
                    ConfigManager.load('applications')['General']['TELEGRAM_POST_URL'].replace("{token}", telegram_bot_token),
                    json=payload
                )

                if response.status_code != 200:
                    print(f"Telegram API response status: {response.status_code}")
                    print(f"Error details: {response.text}")

                    try:
                        error_data = response.json()
                        if 'parameters' in error_data and 'migrate_to_chat_id' in error_data['parameters']:
                            new_chat_id = error_data['parameters']['migrate_to_chat_id']
                            payload['chat_id'] = new_chat_id
                            retry_response = requests.post(
                                ConfigManager.load('applications')['General']['TELEGRAM_POST_URL'].replace("{token}", telegram_bot_token),
                                json=payload
                            )
                            if retry_response.status_code != 200:
                                print(f"Retry failed: {retry_response.text}")
                    except Exception as inner_e:
                        print(f"Error processing Telegram error response: {inner_e}")

            except Exception as e:
                print(f"Error sending Telegram message: {e}")

            # Update the final embed for the player
            try:
                final_embed = discord.Embed(
                    title = ConfigManager.load('applications')['General']['APPLICATION_SUBMITTED_TITLE'],
                    color = discord.Color.from_str(ConfigManager.get('EMBED_COLOR')),
                    description = ConfigManager.load('applications')['General']['APPLICATION_SUBMITTED_MESSAGE'].replace('{self.role}', self.application_name)
                )
                logo_url = interaction.client.app.embeds.get_logo_url(ConfigManager.get("LOGO"))
                final_embed.set_footer(text = ConfigManager.get("FOOTER"), icon_url = logo_url)
                for child in self.answers[interaction.user.id].keys():
                    final_embed.add_field(
                        name = child,
                        value = self.answers[interaction.user.id][child],
                        inline = False
                    )
                await self.interaction.edit_original_response(view = None, embed = final_embed)
            except Exception as e:
                print(f"Error sending Discord response: {e}")
    
    def add_fields(self):
        for field in self.step_data['questions']:
            question = discord.ui.TextInput(
                placeholder = field['label'],
                style = discord.TextStyle.long if field['length'] == 'long' else discord.TextStyle.short,
                max_length = 1024
            )
            self.add_item(discord.ui.Label(text=field['label'], component=question))
