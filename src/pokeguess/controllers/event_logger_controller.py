import logging
from discord import Guild
from discord.ext import commands
from discord.ext.commands import CommandNotFound


log = logging.getLogger("event")


class EventLoggerController(commands.Cog):
    """Log some common interactions with the bot."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

        @bot.event
        async def on_command_error(ctx, error):
            if isinstance(error, CommandNotFound):
                return
            raise error

    @commands.Cog.listener()
    async def on_ready(self):
        log.info(
            f"Bot is logged in and ready as {self.bot.user.name}#{self.bot.user.discriminator}"
        )

    @commands.Cog.listener()
    async def on_guild_join(self, guild: Guild):
        log.info(f"Joined a guild! ({guild.id})")

    @commands.Cog.listener()
    async def on_guild_remove(self, guild: Guild):
        log.info(f"Left a guild... ({guild.id})")
