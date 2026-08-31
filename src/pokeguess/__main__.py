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
ORIGINAL_IMG_DIR = POKEMON_DIR / "originals"
REVEALED_IMG_DIR = POKEMON_DIR / "revealed"
HIDDEN_IMG_DIR = POKEMON_DIR / "hidden"


log = logging.getLogger(__name__.replace("__main__", "main"))


def process_pokemon_images():
    log.debug("Processing pokemon images")
    image_service = ImageService()
    for file in os.listdir(ORIGINAL_IMG_DIR):
        original_path = ORIGINAL_IMG_DIR / file
        hidden_path = HIDDEN_IMG_DIR / file
        revealed_path = REVEALED_IMG_DIR / file

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


async def main() -> int:
    load_dotenv()
    prepare_logger()

    log.info("Heya!")

    if not has_file_permissions():
        return 1

    bot_token = os.environ.get("DISCORD_BOT_TOKEN")
    if bot_token is None:
        log.error("environment variable BOT_TOKEN missing")
        return 1

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
    pokedex_service = PokedexService()
    pokedex_service.download_all_images()
    process_pokemon_images()

    async with bot:  # this will close the client session and remove the "Unclosed client session" error
        await bot.start(bot_token)

    return 0


def run():
    try:
        sys.exit(asyncio.run(main()))
    except KeyboardInterrupt:
        log.info("Bye Bye!")
        sys.exit(0)


if __name__ == "__main__":
    run()
