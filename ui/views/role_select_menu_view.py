import discord
from core.config import ConfigManager
from core.loggers import log_tasks


def _role_emoji_config_entry(entry):
    """Return (emoji, role_id) from a ROLE_EMOJIS value (str or {emoji, id})."""
    if isinstance(entry, dict):
        return entry.get("emoji"), entry.get("id")
    return entry, None


class RoleSelectMenu(discord.ui.Select):
    def __init__(self, interaction: discord.Interaction):
        self.interaction = interaction
        options = []
        for label, entry in ConfigManager.get("ROLE_EMOJIS").items():
            emoji, _ = _role_emoji_config_entry(entry)
            options.append(discord.SelectOption(label=label, emoji=emoji))
        options.append(discord.SelectOption(label="Remove Roles", emoji="❌"))
        super().__init__(
            options=options,
            placeholder="Select your desired roles...",
            custom_id="1",
            max_values=min(len(options), 25),
        )

    async def callback(self, interaction: discord.Interaction):
        try:
            await self.interaction.edit_original_response(content="Assigning your roles...", view=None, embed=None)
            user = interaction.user
            role_objects = {}
            for label, entry in ConfigManager.get("ROLE_EMOJIS").items():
                _, rid = _role_emoji_config_entry(entry)
                if rid is not None:
                    role_objects[label] = interaction.guild.get_role(rid)
                else:
                    role_objects[label] = discord.utils.get(interaction.guild.roles, name=label)
            selected_roles = self.values
            added_roles = []
            removed_roles = []
            for role_name, role in role_objects.items():
                if selected_roles[0] == "Remove Roles":
                    removed_roles.append(role_name)
                    await user.remove_roles(role)
                elif role_name not in selected_roles and role in user.roles:
                    removed_roles.append(role_name)
                    await user.remove_roles(role)
            for role_name in selected_roles:
                if role_name != "Remove Roles":
                    role = role_objects.get(role_name)
                    if role:
                        if role not in user.roles:
                            added_roles.append(role_name)
                            await user.add_roles(role)
            added_roles = "\n".join(added_roles)
            removed_roles = "\n".join(removed_roles)
            roles_embed = discord.Embed(title="Roles Updated",
                                        color=discord.Color.from_str(ConfigManager.get("EMBED_COLOR")),
                                        description="Successfully updated your roles!")
            roles_embed.add_field(name="Roles Added", value=added_roles if added_roles else "None")
            roles_embed.add_field(name="Roles Removed", value=removed_roles if removed_roles else "None")
            logo_url = interaction.client.app.embeds.get_logo_url(ConfigManager.get("LOGO"))
            roles_embed.set_footer(text=ConfigManager.get("FOOTER"), icon_url=logo_url)
            await self.interaction.edit_original_response(embed=roles_embed, content=None)
            log_tasks.info(f"{interaction.user} ({interaction.user.id}) submitted the {self.placeholder} select menu")
        
        except Exception as e:
            await self.interaction.edit_original_response(content = f"{self.placeholder} select menu error {e}", embeds = None)
            log_tasks.error(f"{interaction.user} ({interaction.user.id}) failed to click the {self.placeholder} select menu {e}")
