import logging

from discord import File, Interaction, app_commands
from discord.ext import commands

from pokeguess.views import meta_view

log = logging.getLogger(__name__.removesuffix("_controller"))


class MetaController(commands.Cog):
    """Handles meta requests, this is more about giving information and resources to the user"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(
        name="invite",
        description="Invite this bot to your server!",
    )
    async def invite_command(self, interaction: Interaction) -> None:
        log.info("Interaction: invite")

        view = meta_view.InviteView(self.bot.user)
        file = File("./resources/littlePokemonBanner.png")
        await interaction.response.send_message(view=view, file=file)
