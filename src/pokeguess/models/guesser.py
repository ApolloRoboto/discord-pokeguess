from dataclasses import dataclass
from datetime import datetime

from discord import Member, TextChannel
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
