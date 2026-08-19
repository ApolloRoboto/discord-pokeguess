import asyncio
import logging
import os
import sys
from pathlib import Path

from discord import Intents
from discord.ext import commands
from discord.ext.prometheus import PrometheusCog
from dotenv import load_dotenv

import pokeguess.controllers
from pokeguess.logger import prepare_logger
from pokeguess.services.image_service import ImageService
from pokeguess.services.pokedex_service import PokedexService

POKEMON_DIR = Path("./pokemons")
ORIGINAL_DIR = POKEMON_DIR / "originals"
REVEALED_DIR = POKEMON_DIR / "revealed"
HIDDEN_DIR = POKEMON_DIR / "hidden"


log = logging.getLogger(__name__.replace("__main__", "main"))


def download_pokemon_images():
    log.debug("Downloading pokemon images")
    PokedexService().download_all_pokemon()


def process_pokemon_images():
    log.debug("Processing pokemon images")
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


def has_file_permissions():
    if os.access(POKEMON_DIR, os.W_OK):
        return True
    log.error(f"Missing write permissions for folder '{POKEMON_DIR.absolute()}'")
    return False


def log_bot_commands(bot):
    app_commands = [c.name for c in list(bot.tree.walk_commands())]
    log.info(f"App Commands ({len(app_commands)}): {', '.join(app_commands)}")

    commands = [c.name for c in list(bot.walk_commands())]
    log.info(f"Commands ({len(commands)}): {', '.join(commands)}")


async def main():
    load_dotenv()
    prepare_logger()

    log.info("Heya!")

    if not has_file_permissions():
        sys.exit(1)

    log.debug(f"Pokemon images will be saved at {POKEMON_DIR.absolute()}")

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

    await pokeguess.controllers.add_cogs(bot)

    log_bot_commands(bot)

    # Prepare the data before running the bot
    download_pokemon_images()
    process_pokemon_images()

    await bot.start(os.environ["DISCORD_BOT_TOKEN"])


def run():
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        log.info("Bye Bye!")


if __name__ == "__main__":
    run()
