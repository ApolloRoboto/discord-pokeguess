import logging
import os

from discord.ext import commands, tasks

from pokeguess.services.topgg_service import TopggService

log = logging.getLogger(__name__.removesuffix("_controller"))


class TopggControllerException(Exception):
    pass


class TopggControllerMissingTokenException(TopggControllerException):
    pass


class TopggControllerMissingProjectIdException(TopggControllerException):
    pass


class TopggController(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

        self.has_posted_commands = False

        token = os.getenv("TOPGG_TOKEN")
        if token is None or token == "":
            raise TopggControllerMissingTokenException()

        self.topgg_client = TopggService(token)

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
