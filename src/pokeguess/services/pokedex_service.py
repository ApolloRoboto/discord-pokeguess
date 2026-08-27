import json
import logging
import os
import shutil
from datetime import UTC, datetime
from pathlib import Path

import requests

from pokeguess.models.pokemon import PokemonData

log = logging.getLogger(__name__.removesuffix("_service"))

# TODO: needs to be configurations
OUT_DIR = Path("./pokemons/originals/")
POKEDEX = Path("./resources/pokedex.json")


class PokedexServiceException(Exception):
    pass


class PokedexMissingException(PokedexServiceException):
    pass


class PokedexService:
    def __init__(self) -> None:
        # create directory if it does not exists
        if not OUT_DIR.exists():
            log.info(f"Creating directory {OUT_DIR}")
            os.makedirs(OUT_DIR)

        # validate the variable to be a directory
        if not OUT_DIR.is_dir():
            raise ValueError(f"{OUT_DIR} has to be a directory")
        self.pokedex: list[PokemonData] = []

        self.load_pokedex()

    def load_pokedex(self):
        with open(POKEDEX, "r") as f:
            data: list[dict] = json.load(f)

        self.pokedex = [PokemonData.from_dict(d) for d in data]

    def get_pokemon_by_id(self, pokemon_id) -> PokemonData | None:
        for p in self.pokedex:
            if p.id == pokemon_id:
                return p
        return None

    def get_all_pokemons(self) -> list[PokemonData]:

        if not POKEDEX.exists():
            raise PokedexMissingException()

        log.debug("Reading the pokedex")
        with open(POKEDEX, "r", encoding="utf-8") as f:
            data: list[dict] = json.load(f)

        return [PokemonData.from_dict(entry) for entry in data]

    def get_downloaded_image_ids(self) -> list[int]:
        """Look into the out directory for images that was already downloaded"""

        ids: list[int] = []

        for file in os.listdir(OUT_DIR):
            ids.append(int(file.split(".")[0]))

        return ids

    def download_image(self, pokemon: PokemonData):
        if pokemon.image_url is None:
            return

        start_time = datetime.now(UTC)
        log.debug(f"Starting image download of pokemon #{pokemon.id} {pokemon.slug}")

        response = requests.get(pokemon.image_url, stream=True)

        response.raise_for_status()

        file_path = OUT_DIR / f"{pokemon.id}.png"

        with open(file_path, "wb") as f:
            shutil.copyfileobj(response.raw, f)

        end_time = datetime.now(UTC) - start_time

        log.info(
            f"Successfully downloaded image for #{pokemon.id} {pokemon.slug} [{end_time}]"
        )

    def copy_image(self, pokemon: PokemonData):
        if pokemon.image_path is None:
            return

        log.debug(f"Copying image of pokemon #{pokemon.id} {pokemon.slug}")

        file_path = OUT_DIR / f"{pokemon.id}.png"

        shutil.copyfile(pokemon.image_path, file_path)

        log.info(f"Successfully copied image for pokemon #{pokemon.id} {pokemon.slug}")

    def download_all_images(self):
        # avoid re downloading images
        start_time = datetime.now(UTC)

        already_downloaded_ids: list[int] = self.get_downloaded_image_ids()
        pokemons = self.get_all_pokemons()
        pokemons = list(filter(lambda x: x.id not in already_downloaded_ids, pokemons))

        log.debug(f"Downloading images, there are {len(pokemons)} images to download")

        for pokemon in pokemons:
            # if this image is already downloaded, skip
            if pokemon.id in already_downloaded_ids:
                continue

            if pokemon.image_path is not None:
                self.copy_image(pokemon)
            if pokemon.image_url is not None:
                self.download_image(pokemon)

        end_time = datetime.now(UTC)

        log.info(f"Finished downloading all images [{end_time - start_time}]")
