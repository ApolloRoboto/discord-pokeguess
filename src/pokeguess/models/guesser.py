from dataclasses import dataclass
from datetime import datetime

from discord import (
    DMChannel,
    GroupChannel,
    Member,
    Message,
    StageChannel,
    TextChannel,
    Thread,
    User,
    VoiceChannel,
)

from pokeguess.models.pokemon import CustomPokemonData, PokemonData


@dataclass
class Guesser:
    channel: (
        VoiceChannel | StageChannel | TextChannel | Thread | DMChannel | GroupChannel
    )
    pokemon: PokemonData
    start_time: datetime
    end_time: datetime
    author: Member | User
    total_guesses: int = 0
    winning_message: Message | None = None
    winner: Member | None = None
    hints_given = 0

    @property
    def is_custom(self) -> bool:
        return isinstance(self.pokemon, CustomPokemonData)

    def guess(self, s: str) -> bool:
        return (
            s == self.pokemon.slug
            or s == self.pokemon.name.lower()
            or s in self.pokemon.aliases
        )
