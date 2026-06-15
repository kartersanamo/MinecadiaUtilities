"""Guild-scoped slash command sync for Minecadia bots."""
from __future__ import annotations

import asyncio
import logging
import os
from typing import TYPE_CHECKING

import discord

if TYPE_CHECKING:
    from discord.ext import commands

_logger = logging.getLogger(__name__)

MAX_SYNC_ATTEMPTS = 5
RETRY_BASE_DELAY_SECONDS = 2.0
RETRYABLE_HTTP_STATUSES = {429, 500, 502, 503, 504}


def resolve_guild_id(config_guild_id: int | str | None = None) -> int | None:
    raw = os.getenv("DISCORD_GUILD_ID", "").strip()
    if not raw.isdigit() and config_guild_id is not None:
        raw = str(config_guild_id).strip()
    if raw.isdigit():
        return int(raw)
    return None


def format_command_names(commands_list: list[discord.app_commands.AppCommand]) -> str:
    parts: list[str] = []
    for command in commands_list:
        subs = getattr(command, "options", None) or []
        if subs:
            sub_names = ", ".join(getattr(o, "name", str(o)) for o in subs[:8])
            parts.append(f"{command.name}({sub_names})")
        else:
            parts.append(command.name)
    return ", ".join(parts)


def _is_retryable_sync_error(exc: discord.HTTPException) -> bool:
    status = getattr(exc, "status", None)
    return status in RETRYABLE_HTTP_STATUSES


async def _sync_tree(
    bot: "commands.Bot",
    warn,
    *,
    guild: discord.Object | None = None,
) -> list[discord.app_commands.AppCommand]:
    label = f"guild {guild.id}" if guild is not None else "global"
    last_exc: discord.HTTPException | None = None

    for attempt in range(1, MAX_SYNC_ATTEMPTS + 1):
        try:
            if guild is None:
                return await bot.tree.sync()
            return await bot.tree.sync(guild=guild)
        except discord.HTTPException as exc:
            last_exc = exc
            if guild is None and exc.code == 50240:
                warn(
                    "Global command sync incomplete — Discord Activities Entry Point "
                    "must stay registered (50240)."
                )
                return []
            if _is_retryable_sync_error(exc) and attempt < MAX_SYNC_ATTEMPTS:
                delay = RETRY_BASE_DELAY_SECONDS * attempt
                warn(
                    "%s command sync failed (%s) — retrying in %ss (%s/%s)",
                    label.title(),
                    getattr(exc, "status", exc.code),
                    delay,
                    attempt,
                    MAX_SYNC_ATTEMPTS,
                )
                await asyncio.sleep(delay)
                continue
            raise

    if last_exc is not None:
        raise last_exc
    return []


async def _sync_global(bot: "commands.Bot", warn) -> list[discord.app_commands.AppCommand]:
    return await _sync_tree(bot, warn)


async def sync_guild_commands(
    bot: "commands.Bot",
    *,
    config_guild_id: int | str | None = None,
    log=None,
    also_sync_global: bool = True,
    clear_global_after_guild: bool = False,
) -> list[discord.app_commands.AppCommand]:
    """Sync commands to the configured guild; optionally mirror or clear globals."""
    info = log.info if log else _logger.info
    warn = log.warning if log else _logger.warning

    guild_id = resolve_guild_id(config_guild_id)
    if guild_id is None:
        warn("DISCORD_GUILD_ID / GUILD_ID not set — falling back to global sync only")
        try:
            synced = await _sync_global(bot, warn)
        except discord.HTTPException as exc:
            warn(
                "Global command sync failed after retries (%s) — bot will continue with "
                "existing commands. Run /utilities-sync when Discord API is stable.",
                getattr(exc, "status", exc.code),
            )
            return []
        info("Globally synced %s commands: %s", len(synced), format_command_names(synced))
        return synced

    if not bot.application_id:
        warn("application_id not ready — skipping command sync")
        return []

    guild = discord.Object(id=guild_id)
    bot.tree.clear_commands(guild=guild)
    bot.tree.copy_global_to(guild=guild)
    try:
        guild_cmds = await _sync_tree(bot, warn, guild=guild)
    except discord.HTTPException as exc:
        warn(
            "Guild command sync failed after retries (%s) — bot will continue with "
            "existing commands. Run /utilities-sync when Discord API is stable.",
            getattr(exc, "status", exc.code),
        )
        return []
    info(
        "Guild-synced %s commands to guild %s: %s",
        len(guild_cmds),
        guild_id,
        format_command_names(guild_cmds),
    )

    if clear_global_after_guild:
        try:
            bot.tree.clear_commands(guild=None)
            await bot.tree.sync()
            info("Cleared global slash commands")
        except discord.HTTPException as exc:
            if exc.code == 50240:
                warn(
                    "Skipped global command wipe — Discord Activities Entry Point "
                    "cannot be removed via bulk sync (50240)."
                )
            else:
                raise
        return guild_cmds

    if also_sync_global:
        try:
            synced = await _sync_global(bot, warn)
        except discord.HTTPException as exc:
            warn(
                "Global command sync failed after retries (%s) — bot will continue; "
                "guild commands are synced. Run /utilities-sync when Discord API is stable.",
                getattr(exc, "status", exc.code),
            )
            return guild_cmds
        info("Globally synced %s commands: %s", len(synced), format_command_names(synced))
        return synced

    return guild_cmds
