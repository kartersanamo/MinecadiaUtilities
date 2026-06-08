from discord.ext import commands

from core.config import ConfigManager
from core.database import DatabasePool
from repositories.statistics_repository import StatisticsRepository
from repositories.poll_repository import PollRepository
from services.embed_service import EmbedService
from services.permission_service import PermissionService
from services.poll_service import PollService
from services.statistics_service import StatisticsService
from services.time_format_service import TimeFormatService


class BotApp:
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.settings = ConfigManager.all()
        self.db = DatabasePool.get()
        self.statistics_repo = StatisticsRepository(self.db)
        self.statistics = StatisticsService(self.statistics_repo)
        self.polls_repo = PollRepository()
        self.polls = PollService(self.polls_repo)
        self.permissions = PermissionService()
        self.embeds = EmbedService()
        self.time_format = TimeFormatService()

    @classmethod
    def from_bot(cls, bot: commands.Bot) -> "BotApp":
        return cls(bot)
