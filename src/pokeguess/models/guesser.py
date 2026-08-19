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

from pokeguess.models.pokemon import Pokemon


@dataclass
class Guesser:
    channel: (
        VoiceChannel | StageChannel | TextChannel | Thread | DMChannel | GroupChannel
    )
    pokemon: Pokemon
    start_time: datetime
    end_time: datetime
    author: Member | User
    total_guesses: int = 0
    winning_message: Message | None = None
    winner: Member | None = None
    hints_given = 0
