import json
import logging
import shutil
from datetime import UTC, datetime
from pathlib import Path

import aiofiles
import aiohttp

from pokeguess.models.pokemon import PokemonData

log = logging.getLogger(__name__.removesuffix("_service"))


class PokedexServiceException(Exception):
    pass


class PokedexMissingException(PokedexServiceException):
    pass


class PokedexService:
    def __init__(
        self,
        http_client: aiohttp.ClientSession,
        pokedex_file: Path,
        original_dir: Path,
    ) -> None:
        self.http_client = http_client
        self.pokedex_file = pokedex_file
        self.original_dir = original_dir

        if not self.pokedex_file.exists():
            raise PokedexMissingException()

        log.debug(f"Pokemon images will be saved at {original_dir.absolute()}")

        # create directory if it does not exists
        if not original_dir.exists():
            log.info(f"Creating directory {original_dir}")
            original_dir.mkdir(exist_ok=True)

        # validate the variable to be a directory
        if not original_dir.is_dir():
            raise ValueError(f"{original_dir} has to be a directory")
        self.pokedex: list[PokemonData] = []

        self.load_pokedex()

    def load_pokedex(self):
        with open(self.pokedex_file, "r") as f:
            data: list[dict] = json.load(f)

        self.pokedex = [PokemonData.from_dict(d) for d in data]

    def get_pokemon_by_id(self, pokemon_id) -> PokemonData | None:
        for p in self.pokedex:
            if p.id == pokemon_id:
                return p
        return None

    def get_all_pokemons(self) -> list[PokemonData]:

        log.debug("Reading the pokedex")
        with open(self.pokedex_file, "r", encoding="utf-8") as f:
            data: list[dict] = json.load(f)

        return [PokemonData.from_dict(entry) for entry in data]

    def get_downloaded_image_ids(self) -> list[int]:
        """Look into the out directory for images that was already downloaded"""

        ids: list[int] = []

        for file in self.original_dir.iterdir():
            ids.append(int(file.name.split(".")[0]))

        return ids

    async def download_image(self, pokemon: PokemonData):
        if pokemon.image_url is None:
            return

        start_time = datetime.now(UTC)
        log.debug(f"Starting image download of pokemon #{pokemon.id} {pokemon.slug}")

        file_path = self.original_dir / f"{pokemon.id}.png"

        async with self.http_client.get(pokemon.image_url) as response:
            response.raise_for_status()
            async with aiofiles.open(file_path, "wb") as f:
                async for chunk in response.content.iter_chunked(65536):
                    await f.write(chunk)

        end_time = datetime.now(UTC) - start_time

        log.info(
            f"Successfully downloaded image for #{pokemon.id} {pokemon.slug} [{end_time}]"
        )

    def copy_image(self, pokemon: PokemonData):
        if pokemon.image_path is None:
            return

        log.debug(f"Copying image of pokemon #{pokemon.id} {pokemon.slug}")

        file_path = self.original_dir / f"{pokemon.id}.png"

        shutil.copyfile(pokemon.image_path, file_path)

        log.info(f"Successfully copied image for pokemon #{pokemon.id} {pokemon.slug}")

    async def download_all_images(self):
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
                await self.download_image(pokemon)

        end_time = datetime.now(UTC)

        log.info(f"Finished downloading all images [{end_time - start_time}]")
