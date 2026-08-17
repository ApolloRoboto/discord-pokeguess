import logging
import asyncio
import os
import sys
from pathlib import Path
from discord.ext import commands
from discord import Intents, Interaction, InteractionType
from discord.ext.prometheus import PrometheusCog, PrometheusLoggingHandler
from dotenv import load_dotenv
import controllers
from services.pokedex_service import PokedexService
from services.image_service import ImageService

logging.basicConfig(
    stream=sys.stdout,
    level=logging.INFO,
    datefmt="%Y-%m-%d %H:%M:%S",
    format="%(asctime)s %(levelname)-7s %(name)-25s %(message)s",
)
logging.getLogger().addHandler(PrometheusLoggingHandler())
log = logging.getLogger(__name__)

ORIGINAL_DIR = Path("./pokemons", "originals")
REVEALED_DIR = Path("./pokemons", "revealed")
HIDDEN_DIR = Path("./pokemons", "hidden")


def download_pokemon_images():
    log.info("Downloading pokemon images")
    PokedexService().download_all_pokemon()


def process_pokemon_images():
    log.info("Processing pokemon images")
    image_service = ImageService()
    for file in os.listdir(ORIGINAL_DIR):
        original_path = Path(ORIGINAL_DIR, file)
        hidden_path = Path(HIDDEN_DIR, file)
        revealed_path = Path(REVEALED_DIR, file)

        # Already processed, skipping
        if hidden_path.exists() and revealed_path.exists():
            continue

        image_service.process_image(
            original_path=original_path,
            hidden_path=hidden_path,
            revealed_path=revealed_path,
        )


async def main():
    load_dotenv()

    intents = Intents()
    intents.members = True
    intents.guilds = True
    intents.guild_messages = True
    intents.message_content = True

    bot = commands.AutoShardedBot(
        command_prefix="!",
        intents=intents,
        help_command=None,
    )

    await bot.add_cog(PrometheusCog(bot))

    await controllers.add_cogs(bot)

    log.info("App Commands:")
    for command in bot.tree.walk_commands():
        log.info(f"\t{command.name}")
    log.info("Commands:")
    for command in bot.walk_commands():
        log.info(f"\t{command.name}")

    # Prepare the data before running the bot
    download_pokemon_images()
    process_pokemon_images()

    await bot.start(os.environ["DISCORD_BOT_TOKEN"])


if __name__ == "__main__":
    asyncio.run(main())
