import logging
import os
from collections.abc import Awaitable, Callable
from datetime import datetime, timezone
from pathlib import Path

from discord import TextChannel
from discord.ext import tasks
from prometheus_client import Counter

from pokeguess.models.guesser import Guesser
from pokeguess.models.pokemon import Pokemon

log = logging.getLogger(__name__)

HIDDEN_IMG_DIR = Path("./pokemons/hidden/")
REVEALED_IMG_DIR = Path("./pokemons/revealed/")

POKEGUESS_RESULT_COUNTER = Counter(
    "pokeguess_guess_result",
    "The outcome of a pokeguess, did the users got the right answer?",
    ["outcome"],
)


class GuesserServiceException(Exception):
    pass


class GuesserAlreadyActiveException(GuesserServiceException):
    pass


class GuesserService:
    def __init__(self) -> None:
        # Guesser by channel_id
        self.active_guess: dict[int, Guesser] = {}

        self.on_guesser_end_event: list[Callable[[Guesser], Awaitable[None]]] = []

        # pylint: disable=no-member
        self.end_guesses_loop.start()
        # pylint: enable=no-member

    def get_pokemon_by_id(self, pokemon_id):
        log.info(f"Searching for pokemon #{pokemon_id} in the file system")

        for file in os.listdir(HIDDEN_IMG_DIR):
            first_underscore = file.index("_")
            last_dot = len(file) - file[::-1].index(".") - 1

            pokemon_name = file[first_underscore + 1 : last_dot]

            if pokemon_id == int(file[0:first_underscore]):
                return Pokemon(
                    id=pokemon_id,
                    name=pokemon_name,
                    hidden_img_path=Path(HIDDEN_IMG_DIR, file),
                    revealed_img_path=Path(REVEALED_IMG_DIR, file),
                    original_img_path=None,  # Hiding it
                )

        log.error(f"Pokemon #{pokemon_id} not found")

        return None

    def add_guesser(self, guesser: Guesser) -> None:
        if guesser.channel.id in self.active_guess:
            raise GuesserAlreadyActiveException()

        log.info(
            f"Creating a guesser for pokemon #{guesser.pokemon.id} in channel {guesser.channel.id}"
        )

        self.active_guess[guesser.channel.id] = guesser

    async def end_guesser(self, channel: TextChannel):
        if channel.id not in self.active_guess:
            raise GuesserServiceException()

        guesser = self.active_guess.pop(channel.id)

        log.info(
            f"Ending guesser for pokemon #{guesser.pokemon.id} in channel {channel.id}"
        )

        if guesser.winner is None:
            POKEGUESS_RESULT_COUNTER.labels("lose").inc()
            log.info("Users lost")
        else:
            log.info(f"User {guesser.winner.id} won")
            POKEGUESS_RESULT_COUNTER.labels("win").inc()

        for event in self.on_guesser_end_event:
            try:
                await event(guesser)
            except Exception:
                log.exception("Unhandled exception while calling on_guesser_end_event")

    def get_guesser(self, channel: TextChannel | int) -> Guesser:
        if isinstance(channel, int):
            return self.active_guess.get(channel, None)

        return self.active_guess.get(channel.id, None)

    @tasks.loop(seconds=1)
    async def end_guesses_loop(self):
        try:
            channels_ids = list(self.active_guess.keys())

            for channel_id in channels_ids:
                guesser = self.get_guesser(channel_id)

                if guesser.end_time < datetime.now(timezone.utc):
                    await self.end_guesser(guesser.channel)
        except Exception:
            log.exception("Error during end_guesses_loop")
