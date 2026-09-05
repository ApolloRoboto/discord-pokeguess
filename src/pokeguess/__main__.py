import asyncio
import logging
import os
import sys
from importlib.metadata import version
from pathlib import Path

import aiohttp.client
from discord import Intents
from discord.ext.commands import AutoShardedBot
from discord.ext.prometheus import PrometheusCog
from dotenv import load_dotenv

from pokeguess import controllers, services
from pokeguess.logger import prepare_logger
from pokeguess.services.pokedex_service import PokedexService

RESOURCE_DIR = Path("./resources")
POKEMON_DIR = Path("./pokemons")
ORIGINAL_IMG_DIR = POKEMON_DIR / "originals"
HIDDEN_IMG_DIR = POKEMON_DIR / "hidden"
REVEALED_IMG_DIR = POKEMON_DIR / "revealed"


log = logging.getLogger(__name__.replace("__main__", "main"))


def get_required_env(key: str) -> str:
    val = os.getenv(key)
    if val is None or val.strip() == "":
        raise ValueError(f"Environment variable {key} missing")
    return val


def get_bool_env(key: str) -> bool:
    val = os.getenv(key)
    if val is None:
        return False
    val = val.strip().lower()

    return val == "true" or val == "0"


def create_http_client() -> aiohttp.ClientSession:
    user_agent = f"pokeguess/{version('pokeguess')} (+https://github.com/ApolloRoboto/discord-pokeguess)"
    headers = {
        "User-Agent": user_agent,
    }

    return aiohttp.ClientSession(
        headers=headers,
    )


def create_topgg_service(http_client: aiohttp.ClientSession) -> services.TopggService:
    token = get_required_env("TOPGG_TOKEN")

    return services.TopggService(token, http_client)


async def create_pokedex_service(
    http_client: aiohttp.ClientSession,
) -> services.PokedexService:

    s = PokedexService(
        http_client,
        pokedex_file=RESOURCE_DIR / "pokedex.json",
        original_dir=ORIGINAL_IMG_DIR,
    )
    await s.load_pokedex()
    return s


def create_image_service() -> services.ImageService:
    return services.ImageService(RESOURCE_DIR / "background.png")


def create_guesser_service() -> services.GuesserService:
    return services.GuesserService()


async def process_pokemon_images(image_service: services.ImageService):
    log.debug("Processing pokemon images")

    for file in os.listdir(ORIGINAL_IMG_DIR):
        original_path = ORIGINAL_IMG_DIR / file
        hidden_path = HIDDEN_IMG_DIR / file
        revealed_path = REVEALED_IMG_DIR / file

        # Already processed, skipping
        if hidden_path.exists() and revealed_path.exists():
            continue

        await image_service.process_image(
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


def create_bot() -> AutoShardedBot:

    intents = Intents()
    intents.members = True
    intents.guilds = True
    intents.guild_messages = True
    intents.message_content = True

    return AutoShardedBot(
        command_prefix="!",
        intents=intents,
        help_command=None,
    )


async def main() -> int:
    load_dotenv()
    prepare_logger()

    log.info("Heya!")

    if not has_file_permissions():
        return 1

    bot_token = get_required_env("DISCORD_BOT_TOKEN")

    bot = create_bot()
    http_client = create_http_client()
    pokedex_service = await create_pokedex_service(http_client)
    image_service = create_image_service()
    guesser_service = create_guesser_service()

    await bot.add_cog(PrometheusCog(bot))
    await bot.add_cog(controllers.EventLoggerController(bot))
    await bot.add_cog(controllers.MetaController(bot))
    await bot.add_cog(
        controllers.GuessController(
            bot, pokedex_service, image_service, guesser_service
        )
    )
    await bot.add_cog(controllers.SyncController(bot))

    if get_bool_env("TOPGG_ENABLED"):
        topgg_service = create_topgg_service(http_client)
        await bot.add_cog(controllers.TopggController(bot, topgg_service))

    log_bot_commands(bot)

    # Prepare the data before running the bot
    await pokedex_service.download_all_images()
    await process_pokemon_images(image_service)

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
