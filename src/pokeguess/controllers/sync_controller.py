import logging
from discord.ext import commands
from discord.ext.commands import Context

log = logging.getLogger(__name__.removesuffix("_controller"))


class SyncController(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        try:
            log.debug("Syncing commands")
            synced = await self.bot.tree.sync()
            log.info(f"Synced {len(synced)} commands ")
        except:
            log.exception("error syncing")
