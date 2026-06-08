import discord

from core.config import ConfigManager
from core.loggers import log_tasks


def get_verified_role(guild: discord.Guild) -> discord.Role | None:
    role_id = ConfigManager.get("VERIFIED_ROLE_ID")
    if role_id:
        role = guild.get_role(int(role_id))
        if role is not None:
            return role
    return discord.utils.get(guild.roles, name="Verified")


async def refresh_verify_panel(interaction: discord.Interaction) -> None:
    """Re-attach sync buttons on the public verify embed after a modal submit."""
    from ui.views.sync_buttons_view import SyncButtons

    message = interaction.message
    if message is None or message.author.id != interaction.client.user.id:
        return
    try:
        await message.edit(view=SyncButtons())
    except discord.HTTPException as exc:
        log_tasks.debug(
            "Could not refresh verify panel on message %s: %s",
            message.id,
            exc,
        )
