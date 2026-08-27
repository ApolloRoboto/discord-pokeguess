from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any


@dataclass(kw_only=True)
class PokemonData:
    generation: int | None
    id: int | str
    name: str
    slug: str
    aliases: list[str] = field(default_factory=list)
    types: list[PokemonType] = field(default_factory=list)
    image_path: Path | None = None
    image_url: str | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> PokemonData:
        return PokemonData(
            generation=data.get("generation"),
            id=data["id"],
            name=data["name"],
            slug=data["slug"],
            aliases=data.get("aliases", []),
            image_path=None
            if data.get("image_path") is None
            else Path(data["image_path"]),
            image_url=data.get("image_url"),
            types=[PokemonType[v] for v in data.get("type", [])],
        )


@dataclass
class CustomPokemonData(PokemonData):
    original_img_path: Path
    hidden_img_path: Path
    revealed_img_path: Path


class PokemonType(Enum):
    """https://pokemon.fandom.com/wiki/Type#List_of_types"""

    normal = 0  # a8a878
    fire = 1  # f08030
    water = 2  # 6890f0
    electric = 3  # f8d030
    grass = 4  # 78c850
    ice = 5  # 98d8d8
    fighting = 6  # c03028
    poison = 7  # a040a0
    ground = 8  # e0c068
    flying = 9  # a890f0
    psychic = 10  # f85888
    bug = 11  # a8b820
    rock = 12  # b8a038
    ghost = 13  # 705898
    dragon = 14  # 7038f8
    dark = 15  # 705848
    steel = 16  # b8b8d0
    fairy = 17  # f0b6bc

    @property
    def color(self):
        return _pokemon_type_color[self]


_pokemon_type_color = {
    PokemonType.normal: "#a8a878",
    PokemonType.fire: "#f08030",
    PokemonType.water: "#6890f0",
    PokemonType.electric: "#f8d030",
    PokemonType.grass: "#78c850",
    PokemonType.ice: "#98d8d8",
    PokemonType.fighting: "#c03028",
    PokemonType.poison: "#a040a0",
    PokemonType.ground: "#e0c068",
    PokemonType.flying: "#a890f0",
    PokemonType.psychic: "#f85888",
    PokemonType.bug: "#a8b820",
    PokemonType.rock: "#b8a038",
    PokemonType.ghost: "#705898",
    PokemonType.dragon: "#7038f8",
    PokemonType.dark: "#705848",
    PokemonType.steel: "#b8b8d0",
    PokemonType.fairy: "#f0b6bc",
}
