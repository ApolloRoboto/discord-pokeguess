import os
import shutil
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass
import json
import logging
import requests

log = logging.getLogger(__name__)

OUT_DIR = Path("./pokemons/originals/")
POKEDEX = Path("./pokemons/pokedex.json")


@dataclass
class Pokemon:
    abilities: list[str]
    detailPageURL: str
    weight: str
    weakness: list[str]
    number: str
    height: int
    collectibles_slug: str
    featured: bool
    slug: str
    name: str
    ThumbnailAltText: str
    ThumbnailImage: str
    id: int
    type: list[str]

    @property
    def file_name(self) -> str:
        return str(self.id) + "_" + self.name.replace(":", "") + ".png"


class PokedexService:
    def __init__(self) -> None:
        # create directory if it does not exists
        if not OUT_DIR.exists():
            log.info(f"Creating directory {OUT_DIR}")
            os.makedirs(OUT_DIR)

        # validate the variable to be a directory
        if not OUT_DIR.is_dir():
            raise Exception(f"{OUT_DIR} has to be a directory")

    def get_all_pokemons(self) -> list[Pokemon]:
        data = {}

        # if the json pokedex exist, use it
        if POKEDEX.exists():
            log.info("Opening the pokedex")
            with open(POKEDEX, "r", encoding="utf-8") as f:
                data = json.load(f)

        # else, download the pokedex
        else:
            log.info("Getting the Pokedex")
            url = "https://www.pokemon.com/us/api/pokedex"

            log.info("Request to " + url)
            response = requests.get(url)

            response.raise_for_status()

            data = response.json()

            log.info("Saving the Pokedex")
            with open(POKEDEX, "w", encoding="utf-8") as f:
                json.dump(data, f)

        return [Pokemon(**entry) for entry in data]

    def get_downloaded_ids(self) -> list[int]:
        """Look into the out directory for files that was already downloaded"""

        ids: list[int] = []
        for file in os.listdir(OUT_DIR):
            ids.append(int(file.split("_")[0]))

        return ids

    def download_image(self, pokemon: Pokemon):
        start_time = datetime.now()
        log.info(f"Starting download of pokemon #{pokemon.id} {pokemon.name}")

        response = requests.get(pokemon.ThumbnailImage, stream=True)

        response.raise_for_status()

        file_path = Path(OUT_DIR, pokemon.file_name)

        with open(file_path, "wb") as f:
            shutil.copyfileobj(response.raw, f)

        log.info(f"Download successful [{datetime.now() - start_time}]")

    def download_all_pokemon(self):
        # get already downloaded images (in case the script failed at any point)
        already_downloaded_ids: list[int] = self.get_downloaded_ids()
        pokemons = self.get_all_pokemons()
        log.info(f"There are {len(already_downloaded_ids)} images already downloaded")

        # some pokemons are listed twice, but always following, this last id is to skip duplicates
        last_id = 0

        for pokemon in pokemons:
            if pokemon.id == last_id:
                log.info("duplicated id, skipping...")
                continue

            # if this image is already downloaded, skip
            if pokemon.id in already_downloaded_ids:
                continue

            self.download_image(pokemon)
            last_id = pokemon.id
