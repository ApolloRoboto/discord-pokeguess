from datetime import datetime
from dataclasses import dataclass
from discord import TextChannel, Member
from models.pokemon import Pokemon


@dataclass
class Guesser:
    channel: TextChannel
    pokemon: Pokemon
    start_time: datetime
    end_time: datetime
    custom: bool
    author: Member
    total_guesses: int = 0
    winner: Member = None
    hints_given = 0
