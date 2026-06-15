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
    """Restore sync buttons on the public verify embed (clear any leaked text)."""
    from ui.views.sync_buttons_view import SyncButtons

    message = interaction.message
    if message is None or message.author.id != interaction.client.user.id:
        return
    if message.flags.ephemeral:
        return
    try:
        edit_kwargs: dict = {"view": SyncButtons(), "content": None}
        if message.embeds:
            edit_kwargs["embed"] = message.embeds[0]
        await message.edit(**edit_kwargs)
    except discord.HTTPException as exc:
        log_tasks.debug(
            "Could not refresh verify panel on message %s: %s",
            message.id,
            exc,
        )


async def reply_ephemeral(
    interaction: discord.Interaction,
    *,
    content: str | None = None,
    embed: discord.Embed | None = None,
    view: discord.ui.View | None = None,
) -> bool:
    """Reply or follow up ephemerally; returns False if the interaction token expired."""
    kwargs: dict = {"ephemeral": True}
    if content is not None:
        kwargs["content"] = content
    if embed is not None:
        kwargs["embed"] = embed
    if view is not None:
        kwargs["view"] = view
    try:
        if interaction.response.is_done():
            await interaction.followup.send(**kwargs)
        else:
            await interaction.response.send_message(**kwargs)
        return True
    except (discord.NotFound, discord.InteractionResponded, discord.HTTPException):
        if interaction.response.is_done():
            try:
                await interaction.followup.send(**kwargs)
                return True
            except (discord.NotFound, discord.HTTPException):
                return False
        return False
