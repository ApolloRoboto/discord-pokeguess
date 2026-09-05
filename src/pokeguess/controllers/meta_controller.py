import logging

from discord import AutoShardedClient, Interaction, app_commands
from discord.ext import commands

from pokeguess.views import meta_view

log = logging.getLogger(__name__.removesuffix("_controller"))


class MetaController(commands.Cog):
    """Handles meta requests, this is more about giving information and resources to the user"""

    def __init__(self, bot: AutoShardedClient):
        self.bot = bot

    @app_commands.command(
        name="invite",
        description="Invite this bot to other server",
    )
    async def invite_command(self, interaction: Interaction) -> None:
        log.info("Interaction: invite")

        assert self.bot.user is not None

        view = meta_view.InviteView(self.bot.user)
        # file = File("./resources/littlePokemonBanner.png")
        await interaction.response.send_message(
            view=view,
            # file=file,
            content="*Consider supporting me on [Ko-Fi](https://ko-fi.com/apolloroboto) <3*",
            suppress_embeds=True,
        )
