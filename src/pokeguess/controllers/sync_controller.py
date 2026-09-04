import logging

from discord.ext import commands

log = logging.getLogger(__name__.removesuffix("_controller"))


class SyncController(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.has_synced = False  # prevent sync after reconnection

    @commands.Cog.listener()
    async def on_ready(self):
        if self.has_synced:
            return

        try:
            log.debug("Syncing commands")
            synced = await self.bot.tree.sync()
            self.has_synced = True
            log.info(f"Synced {len(synced)} commands")
        except Exception:
            log.exception("error syncing")
