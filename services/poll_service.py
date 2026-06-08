import datetime

import discord

from core.config import ConfigManager
from repositories.poll_repository import PollRepository
from services.statistics_service import StatisticsService


class PollService:
    def __init__(self, repository: PollRepository | None = None):
        self._repo = repository or PollRepository()
        self._settings = ConfigManager.all()

    def return_polls(self) -> list:
        return self._repo.fetch_all_polls()

    def get_poll_info(self, title: str) -> dict:
        return self._repo.fetch_poll_by_title(title)

    async def create_embed_field(
        self, interaction: discord.Interaction, poll_information, option: int, names: bool
    ):
        votes = poll_information[f"option{option}_votes"].split("___")
        value = f"`{len(votes) - 1} Votes`"
        if names:
            for vote in votes:
                if vote.isdigit():
                    member = discord.utils.get(interaction.guild.members, id=int(vote))
                    if member:
                        value += f"\n {member.mention} ({member.name})"
        return {"name": poll_information[f"option{option}_text"], "value": value}

    async def update_original(self, interaction: discord.Interaction, title: str):
        poll_information = self.get_poll_info(title)
        new_embed = discord.Embed(
            title="Poll Manager",
            description=f"Loading poll information on `{title}`...",
            color=discord.Color.from_str(ConfigManager.get("EMBED_COLOR")),
            timestamp=datetime.datetime.utcnow(),
        )
        logo_url = interaction.client.app.embeds.get_logo_url(ConfigManager.get("LOGO"))
        new_embed.set_footer(text=ConfigManager.get("FOOTER"), icon_url=logo_url)
        for value in list(poll_information.keys()):
            if ("text" in value) and (poll_information[value] != ""):
                new_embed.add_field(
                    **await self.create_embed_field(
                        interaction,
                        poll_information,
                        "".join(num for num in value if num.isdigit()),
                        True,
                    )
                )
        return new_embed


_default_poll_service = PollService()
return_polls = _default_poll_service.return_polls
get_poll_info = _default_poll_service.get_poll_info
create_embed_field = _default_poll_service.create_embed_field
update_original = _default_poll_service.update_original

_statistics_for_polls = StatisticsService()
is_found = _statistics_for_polls.get_statistic
