import discord

from core.config import ConfigManager


class PermissionService:
    @staticmethod
    async def is_staff(
        user: discord.abc.User,
        guild: discord.Guild | None = None,
    ) -> bool:
        member = user if isinstance(user, discord.Member) else None
        if member is None:
            if guild is None:
                return False
            member = guild.get_member(user.id)
            if member is None:
                try:
                    member = await guild.fetch_member(user.id)
                except (discord.NotFound, discord.HTTPException):
                    return False

        staff_roles = ConfigManager.get("STAFF_ROLES")
        return any(role.name in staff_roles for role in member.roles)


is_staff = PermissionService.is_staff
