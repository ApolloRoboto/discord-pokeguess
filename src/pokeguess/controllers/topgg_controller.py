import logging

from discord.ext import commands, tasks
from discord.ext.commands import AutoShardedBot

from pokeguess.services.topgg_service import TopggService

log = logging.getLogger(__name__.removesuffix("_controller"))


class TopggControllerException(Exception):
    pass


class TopggControllerMissingTokenException(TopggControllerException):
    pass


class TopggControllerMissingProjectIdException(TopggControllerException):
    pass


class TopggController(commands.Cog):
    def __init__(self, bot: AutoShardedBot, topgg_service: TopggService):
        self.bot = bot
        self.topgg_client = topgg_service

        self.has_posted_commands = False

    @commands.Cog.listener()
    async def on_ready(self):
        if self.has_posted_commands:
            return

        if not self.metric_update.is_running():
            log.debug("Starting the metric update loop")
            self.metric_update.start()

        try:
            await self.topgg_client.post_commands(self.bot)
            self.has_posted_commands = True
        except Exception:
            log.exception("failed to post commands")

    @tasks.loop(minutes=30)
    async def metric_update(self):
        try:
            await self.topgg_client.post_metrics(self.bot)
        except Exception:
            log.exception("failed to post metrics")
