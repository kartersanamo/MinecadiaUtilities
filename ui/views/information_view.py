import discord
from core.config import ConfigManager
from core.loggers import log_tasks
from ui.views.choose_version_view import ChooseVersion
from ui.views.role_select_menu_view_sendmessage import RoleSelectMenuView


class InformationView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(discord.ui.Button(label="Store", emoji="🛒", url="https://store.minecadia.com/"))
        self.add_item(discord.ui.Button(label="Pixelmon", emoji="<:Pokemonball:1186027100105347173>", url="https://discord.gg/yDcFQ46mZZ", row=1))
        self.add_item(discord.ui.Button(label="Wiki", emoji="🌐",  url="https://wiki.minecadia.com/", row=1))
        self.add_item(discord.ui.Button(label="Vote", emoji="🗳️",  url="https://www.minecadia.com/vote", row=1))
        self.add_item(discord.ui.Button(label="Support", emoji="🎟️",  url="https://discord.com/channels/680569558754656280/1003467703639613570/1185780691082944673", row=1))

    @discord.ui.button(label="How to Play", style=discord.ButtonStyle.green, emoji="❓", custom_id="Info_1")
    async def how_to_play(self, interaction: discord.Interaction, Button: discord.ui.Button):
        try:
            version = discord.Embed(title="What version of the game do you play?",
                                    description="Please select which version you play down below!", 
                                    color = discord.Color.from_str(ConfigManager.get('EMBED_COLOR')))
            await interaction.response.send_message(ephemeral=True, embed=version, view=ChooseVersion(interaction))
            log_tasks.info(f"{interaction.user} ({interaction.user.id}) clicked the {Button.label} {Button.emoji} button")
        
        except Exception as e:
            await interaction.response.send_message(content = f"{Button.label} {Button.emoji} button error {e}", ephemeral = True)
            log_tasks.error(f"{interaction.user} ({interaction.user.id}) failed to click the {Button.label} {Button.emoji} button {e}")
    
    @discord.ui.button(label="Roles", style=discord.ButtonStyle.grey, emoji="👥", custom_id="Info_4")
    async def server_roles(self, interaction: discord.Interaction, Button: discord.ui.Button):
        try:
            roles = discord.Embed(color=discord.Color.from_str(ConfigManager.get("EMBED_COLOR")), 
                                title="Notification Roles", 
                                description=("Looking to be notified for more? Select one of the roles down below!\n"
                                            "\n"
                                            "🚨 **Events**\n"
                                            "📸 **Sneak Peeks**\n"
                                            "📜 **Changelog**\n"
                                            "🎁 **Giveaways**\n"
                                            "📊 **Polls**\n"
                                            "⚔️ **Factions**\n"
                                            "💙 **Lifesteal**\n"
                                            "🏹 **Kitmap**\n"
                                            "<:treeisland:1215311917917151293> **Skyblock**\n"
                                            "🌳 **SMP**\n"
                                            "🎮 **Games**\n"))
            await interaction.response.send_message(embed=roles, view=RoleSelectMenuView(interaction), ephemeral=True)
            log_tasks.info(f"{interaction.user} ({interaction.user.id}) clicked the {Button.label} {Button.emoji} button")
        
        except Exception as e:
            await interaction.response.send_message(content = f"{Button.label} {Button.emoji} button error {e}", ephemeral = True)
            log_tasks.error(f"{interaction.user} ({interaction.user.id}) failed to click the {Button.label} {Button.emoji} button {e}")

    @discord.ui.button(label="Rules", style=discord.ButtonStyle.grey, emoji="🗒️", custom_id="Info_3")
    async def server_rules(self, interaction: discord.Interaction, Button: discord.ui.Button):
        try:
            rules = discord.Embed(title="<:Minecadia:974713467703545907> Minecadia Discord Rules",
                                color = discord.Color.from_str(ConfigManager.get('EMBED_COLOR')),
                                description=('1. **No Inappropriate Language**\n'
                                            'Any type of derogatory language is not allowed, regardless if its towards a user or not.\n'
                                            '\n'
                                            '2. **No Advertisement**\n'
                                            'Advertising in any way is not allowed (this includes Direct Messages) however, you can put team invite links ONLY in faction-recruitment, however, only 1 can be posted per faction.\n'
                                            '\n'
                                            '3. **No Spamming**\n'
                                            'Spamming/Flooding chat is not allowed.\n'
                                            '\n'
                                            '4. **Direct/Indirect Threats**\n'
                                            'Threats to other users including but not limited to DDoS, Death, Dox, and anything else malicious is strictly prohibited.\n'
                                            '\n'
                                            '5. **Inappropriate Content/Links**\n'
                                            'Any content or links which are inappropriate is disallowed.\n'
                                            '\n'
                                            '6. **Support Room/Ticket Trolling**\n'
                                            'If your intent is to of mess around or wasting staff members time, your perms to join with be revoked.\n'
                                            '\n'
                                            '7. **Use Common Sense**\n'
                                            '\n'
                                            '8. **Misuse of Bots**\n'
                                            'Do no not misuse bot commands, or tickets. Doing so will result in a ban.\n'
                                            '\n'
                                            '9. **No Drama**\n'
                                            'Do not start drama, or arguments here, it isn\'t the place.\n'
                                            '\n'
                                            '`Breaking any of the rules above will result in a punishment.`\n'
                                            '\n'
                                            ':video_game: **In Game Rules**\n'
                                            '> Faction Rules: https://minecadia.com/factions-rules/\n'
                                            '> Kitmap Rules: https://www.minecadia.com/kitmap-rules/\n'
                                            '> Lifesteal Rules: https://www.minecadia.com/lifesteal-rules/\n'
                                            '> Prisons Rules: https://www.minecadia.com/prison-rules/'))
            await interaction.response.send_message(embed=rules, ephemeral=True)
            log_tasks.info(f"{interaction.user} ({interaction.user.id}) clicked the {Button.label} {Button.emoji} button")
        
        except Exception as e:
            await interaction.response.send_message(content = f"{Button.label} {Button.emoji} button error {e}", ephemeral = True)
            log_tasks.error(f"{interaction.user} ({interaction.user.id}) failed to click the {Button.label} {Button.emoji} button {e}")
