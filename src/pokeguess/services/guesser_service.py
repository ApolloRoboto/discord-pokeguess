import logging
from collections.abc import Awaitable
from datetime import UTC, datetime
from typing import Protocol

import prometheus_client
from discord import (
    DMChannel,
    GroupChannel,
    Interaction,
    StageChannel,
    TextChannel,
    Thread,
    VoiceChannel,
)
from discord.ext import tasks

from pokeguess.models.guesser import Guesser

log = logging.getLogger(__name__.removesuffix("_service"))

POKEGUESS_RESULT_COUNTER = prometheus_client.Counter(
    "pokeguess_guess_result",
    "The outcome of a pokeguess, did the users got the right answer?",
    ["outcome"],
)


class GuesserServiceException(Exception):
    pass


class GuesserAlreadyActiveException(GuesserServiceException):
    pass


class GuesserNotFoundException(GuesserServiceException):
    pass


class GuesserEndEvent(Protocol):
    def __call__(
        self,
        guesser: Guesser,
        interaction: Interaction | None,
        was_stopped: bool,
    ) -> Awaitable[None]: ...


class GuesserService:
    def __init__(self) -> None:

        # Guesser by channel_id
        self.active_guess: dict[int, Guesser] = {}

        self.on_guesser_end_event: list[GuesserEndEvent] = []

        # pylint: disable=no-member
        self.end_guesses_loop.start()
        # pylint: enable=no-member

    def add_guesser(self, guesser: Guesser) -> None:
        if guesser.channel.id in self.active_guess:
            raise GuesserAlreadyActiveException()

        log.info(
            f"Creating a guesser for pokemon #{guesser.pokemon.id} in channel {guesser.channel.id}"
        )

        self.active_guess[guesser.channel.id] = guesser

    async def end_guesser(
        self,
        channel: VoiceChannel
        | StageChannel
        | TextChannel
        | Thread
        | DMChannel
        | GroupChannel,
        *,
        interaction: Interaction | None = None,
        was_stopped: bool = False,
    ):
        if channel.id not in self.active_guess:
            raise GuesserNotFoundException()

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
                await event(guesser, interaction, was_stopped)
            except Exception:
                log.exception("Unhandled exception while calling on_guesser_end_event")

    def get_guesser(
        self,
        channel: VoiceChannel
        | StageChannel
        | TextChannel
        | Thread
        | DMChannel
        | GroupChannel
        | int,
    ) -> Guesser | None:
        if isinstance(channel, int):
            return self.active_guess.get(channel, None)

        return self.active_guess.get(channel.id, None)

    @tasks.loop(seconds=1)
    async def end_guesses_loop(self):
        try:
            channels_ids = list(self.active_guess.keys())

            for channel_id in channels_ids:
                guesser = self.get_guesser(channel_id)

                if guesser is None:
                    log.warning(
                        f"Expected to find a guesser for channel id {channel_id} but got None"
                    )
                    continue

                if guesser.end_time < datetime.now(UTC):
                    await self.end_guesser(guesser.channel)
        except Exception:
            log.exception("Error during end_guesses_loop")
