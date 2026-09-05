import logging
import os
import random
import tempfile
import uuid
from datetime import UTC, datetime, timedelta
from pathlib import Path

import discord
import Levenshtein
from discord import (
    CategoryChannel,
    File,
    ForumChannel,
    Interaction,
    Message,
    app_commands,
)
from discord.app_commands import Choice, Range
from discord.ext import commands
from discord.ext.commands import AutoShardedBot
from prometheus_client import Counter
from slugify import slugify

from pokeguess.models.guesser import Guesser
from pokeguess.models.pokemon import CustomPokemonData, PokemonData
from pokeguess.services.guesser_service import (
    GuesserAlreadyActiveException,
    GuesserNotFoundException,
    GuesserService,
)
from pokeguess.services.image_service import ImageService
from pokeguess.services.pokedex_service import PokedexService
from pokeguess.views import guess_view

log = logging.getLogger(__name__.removesuffix("_controller"))

POKEMON_TMP_DIR = Path(tempfile.gettempdir(), "custompokemon")
ORIGINAL_IMG_DIR_TMP = POKEMON_TMP_DIR / "originals"
REVEALED_IMG_DIR_TMP = POKEMON_TMP_DIR / "revealed"
HIDDEN_IMG_DIR_TMP = POKEMON_TMP_DIR / "hidden"

POKEMON_DIR = Path("./pokemons")
ORIGINAL_IMG_DIR = POKEMON_DIR / "originals"
HIDDEN_IMG_DIR = POKEMON_DIR / "hidden"
REVEALED_IMG_DIR = POKEMON_DIR / "revealed"


POKEGUESS_ATTEMPS_COUNTER = Counter(
    "pokeguess_guess_attemps", "How many attemps were made by users"
)
POKEGUESS_HINTS_COUNTER = Counter("pokeguess_guess_hints", "How many hints were given")

ALLOWED_CONTENT_TYPE = ["image/png"]
HINT_REQUEST_TEXT = {
    "hint",
    "help",
    "help me",
    "give me hint",
    "give me a hint",
    "give me an hint",
    "give me help",
    "give hint",
    "give help",
    "get hint",
    "get help",
    "i need a hint",
    "i need an hint",
    "i need hint",
    "i need help",
    "i want hint",
    "i want a hint",
    "i want an hint",
    "i want help",
    "can i get hint",
    "can i get a hint",
    "can i get an hint",
    "can i get help",
    "another hint",
    "another help",
    "hint please",
    "help please",
}


class GuessController(commands.Cog):
    """Handles request related to the pokeguess command."""

    def __init__(
        self,
        bot: AutoShardedBot,
        pokedex_service: PokedexService,
        image_service: ImageService,
        guesser_service: GuesserService,
    ):
        self.bot = bot
        self.pokedex_service = pokedex_service

        self.guesser_service = guesser_service
        self.image_service = image_service

        # register the on_guess_end method to be called
        self.guesser_service.on_guesser_end_event.append(self.on_guess_end)

        # keep track of wich channel is processing an image, prevents duplicated requests
        self.image_being_processed: set[int] = set()

    @app_commands.command(
        name="pokeguesscustom", description="Start a Pokemon guess with a custom image"
    )
    @app_commands.describe(
        name="Name of your custom pokemon",
        image="Image of your custom pokemon. Please use an image with transparency",
        timeout="Guessing timeout in seconds",
    )
    async def pokeguesscustom_command(
        self,
        interaction: Interaction,
        name: str,
        image: discord.Attachment,
        timeout: Range[int, 15, 300] = 60,
    ):
        log.debug(f"Interaction: pokeguesscustom, timeout: {timeout}")

        # do I have permission to read and send messages here?
        permissions = interaction.app_permissions
        if (
            permissions.read_messages is False
            or permissions.send_messages is False
            or permissions.attach_files is False
        ):
            log.warning("Missing permissions")
            embed = guess_view.MissingPermissionsEmbed()
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        if interaction.channel is None or isinstance(
            interaction.channel, (ForumChannel, CategoryChannel)
        ):
            log.warning(f"Invalid interaction channel, got {type(interaction.channel)}")
            return

        # is there a running guesser here?
        if self.guesser_service.get_guesser(interaction.channel) is not None:
            log.warning("There is already an active guesser")
            embed = guess_view.AlreadyActiveEmbed()
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        # is there an image being processed here?
        if interaction.channel.id in self.image_being_processed:
            log.warning("There is already an image being processed here")
            embed = guess_view.ProcessingActiveEmbed()
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        if len(name) > 50:
            log.warning(f"Name is too long, was {len(name)}")
            embed = guess_view.InvalidNameEmbed()
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        # max 5 minutes
        if timeout > 300:
            log.warning(f"Timeout is too long, was {timeout}")
            embed = guess_view.InvalidTimeoutEmbed()
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        log.debug(
            f"Custom image: {image.filename} {image.width}x{image.height} {image.content_type} {image.size} bytes"
        )

        # Only taking Images
        if image.content_type not in ALLOWED_CONTENT_TYPE:
            log.warning(f"Invalid content_type, was {image.content_type}")
            embed = guess_view.InvalidMediaTypeEmbed()
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        # Create the file path
        pokemon_id = str(uuid.uuid4())
        original_file_extension = image.filename.split(".")[-1]
        original_path = ORIGINAL_IMG_DIR_TMP / f"{pokemon_id}.{original_file_extension}"
        hidden_path = HIDDEN_IMG_DIR_TMP / f"{pokemon_id}.png"
        revealed_path = REVEALED_IMG_DIR_TMP / f"{pokemon_id}.png"

        # Saving this file
        log.debug(f"Saving {original_path}")
        os.makedirs(ORIGINAL_IMG_DIR_TMP, exist_ok=True)
        await image.save(original_path)

        # Starting the image process
        self.image_being_processed.add(interaction.channel.id)
        async with interaction.channel.typing():
            try:
                self.image_service.process_image(
                    original_path, hidden_path, revealed_path
                )

            except Exception:
                log.exception("Image processing failed")
                embed = guess_view.ProcessingFailedEmbed()
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
            finally:
                if interaction.channel.id in self.image_being_processed:
                    self.image_being_processed.remove(interaction.channel.id)

        # Create the pokemon
        pokemon = CustomPokemonData(
            generation=None,
            name=name,
            slug=slugify(name),
            id=pokemon_id,
            original_img_path=original_path,
            hidden_img_path=hidden_path,
            revealed_img_path=revealed_path,
        )

        # Create the guesser
        now = datetime.now(UTC) + timedelta(milliseconds=100)  #  now + response delay

        guesser = Guesser(
            channel=interaction.channel,
            pokemon=pokemon,
            start_time=now,
            end_time=now + timedelta(seconds=timeout),
            author=interaction.user,
        )

        try:
            self.guesser_service.add_guesser(guesser)
        except GuesserAlreadyActiveException:
            log.warning(
                "Could not send custom pokemon, there is already an active guesser"
            )
            embed = guess_view.AlreadyActiveEmbed()
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        # Send response
        file = File(pokemon.hidden_img_path, filename="hidden.png")
        embed = guess_view.HiddenEmbed(guesser, file)
        await interaction.response.send_message(embed=embed, file=file)

    @app_commands.command(
        name="pokeguess",
        description="Start a Pokemon guess",
    )
    @app_commands.describe(
        generation="The Pokemon generation to play from",
        timeout="Guessing timeout in seconds",
    )
    @app_commands.choices(
        generation=[
            Choice(name="All", value=0),
            Choice(name="Kanto (1)", value=1),
            Choice(name="Johto (2)", value=2),
            Choice(name="Hoenn (3)", value=3),
            Choice(name="Sinnoh (4)", value=4),
            Choice(name="Unova (5)", value=5),
            Choice(name="Kalos (6)", value=6),
            Choice(name="Alola (7)", value=7),
            Choice(name="Galar (8)", value=8),
            Choice(name="Paldea (9)", value=9),
            # Choice(name="XXXXX (10)", value=10), # pokemon list unknown at this time
        ]
    )
    async def pokeguess_command(
        self,
        interaction: Interaction,
        generation: Choice[int] | None = None,
        timeout: Range[int, 15, 300] = 60,
    ) -> None:
        log.debug(
            f"Interaction: pokeguess, generation: {generation}, timeout: {timeout}"
        )

        # do I have permission to read and send messages here
        permissions = interaction.app_permissions
        if permissions.read_messages is False or permissions.send_messages is False:
            log.warning("Missing permissions on this channel")
            embed = guess_view.MissingPermissionsEmbed()
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        if interaction.channel is None or isinstance(
            interaction.channel, (ForumChannel, CategoryChannel)
        ):
            log.warning(f"Invalid interaction channel, got {type(interaction.channel)}")
            embed = guess_view.ErrorEmbed()
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        # is there a running guesser here?
        if self.guesser_service.get_guesser(interaction.channel) is not None:
            log.warning("There is already an active guesser")
            embed = guess_view.AlreadyActiveEmbed()
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        # is there an image being processed here?
        if interaction.channel.id in self.image_being_processed:
            log.warning("There is already an image being processed here")
            embed = guess_view.ProcessingActiveEmbed()
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        # max 5 minutes
        if timeout > 300:
            log.warning(f"Invalid timeout, was {timeout}")
            embed = guess_view.InvalidTimeoutEmbed()
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        id_range = (0, 905)

        if generation is None:
            generation = Choice(name="All", value=0)

        if generation.value == 0:  # all
            id_range = (0, 1025)
        elif generation.value == 1:
            id_range = (0, 151)
        elif generation.value == 2:
            id_range = (152, 251)
        elif generation.value == 3:
            id_range = (252, 386)
        elif generation.value == 4:
            id_range = (387, 493)
        elif generation.value == 5:
            id_range = (494, 649)
        elif generation.value == 6:
            id_range = (650, 721)
        elif generation.value == 7:
            id_range = (722, 809)
        elif generation.value == 8:
            id_range = (810, 905)
        elif generation.value == 9:
            id_range = (906, 1025)
        # elif generation.value == 10:
        #     id_range = (1026, 0)

        choice = random.randint(*id_range)

        log.debug(f"Searching for pokemon #{choice}")

        pokemon = self.pokedex_service.get_pokemon_by_id(choice)
        if pokemon is None:
            log.error(f"Pokemon #{choice} was not found")
            embed = guess_view.ErrorEmbed()
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        # Create Guesser
        now = datetime.now(UTC) + timedelta(milliseconds=100)  #  now + response delay

        guesser = Guesser(
            channel=interaction.channel,
            pokemon=pokemon,
            start_time=now,
            end_time=now + timedelta(seconds=timeout),
            author=interaction.user,
        )

        self.guesser_service.add_guesser(guesser)

        # Send response
        file = File(self.get_pokemon_hidden_img_path(pokemon), filename="hidden.png")
        embed = guess_view.HiddenEmbed(guesser, file)
        await interaction.response.send_message(embed=embed, file=file)

    @app_commands.command(name="stop", description="Stop an active guessing game")
    async def stop_command(
        self,
        interaction: Interaction,
    ):
        log.debug("Interaction: stop")

        if interaction.channel is None or isinstance(
            interaction.channel, (ForumChannel, CategoryChannel)
        ):
            log.warning(f"Invalid interaction channel, got {type(interaction.channel)}")
            return

        # is there an image being processed here?
        if interaction.channel.id in self.image_being_processed:
            log.warning("Attempt to stop the game while image is being processed")
            embed = guess_view.ProcessingActiveEmbed()
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        try:
            await self.guesser_service.end_guesser(
                interaction.channel,
                interaction=interaction,
                was_stopped=True,
            )
        except GuesserNotFoundException:
            embed = guess_view.NothingToStopEmbed()
            await interaction.response.send_message(embed=embed, ephemeral=True)

    @commands.Cog.listener()
    async def on_message(self, message: Message):
        # bot filter
        if message.author.bot is True:
            return

        guesser = self.guesser_service.get_guesser(message.channel)

        # if none, than there is no active guesser for this channel
        if guesser is None:
            return

        guesser.total_guesses += 1
        POKEGUESS_ATTEMPS_COUNTER.inc()

        msg_content = message.content.strip().lower()

        if guesser.guess(msg_content):
            guesser.winner = message.author
            guesser.winning_message = message
            await self.guesser_service.end_guesser(message.channel)
            return

        # Send a hint if the user is requesting it
        if msg_content in HINT_REQUEST_TEXT:
            POKEGUESS_HINTS_COUNTER.inc()
            log.info(
                f"User {message.author.id} requested a hint, hints given: {guesser.hints_given + 1}"
            )
            embed = guess_view.HintEmbed(guesser)
            await message.channel.send(embed=embed)
            guesser.hints_given += 1
            return

        # The user is very close to the answer
        if Levenshtein.distance(msg_content, guesser.pokemon.name.lower()) == 1:
            log.info(f"User {message.author.id} almost got it")
            embed = guess_view.CloseAnswerEmbed()
            await message.reply(embed=embed)
            return

    async def on_guess_end(
        self, guesser: Guesser, interaction: Interaction | None, was_stopped: bool
    ):

        try:
            file = File(self.get_pokemon_revealed_img_path(guesser.pokemon))

            if was_stopped and interaction is not None:
                embed = guess_view.StoppedEmbed(guesser)
                await interaction.response.send_message(embed=embed)
            else:
                async with guesser.channel.typing():
                    embed = guess_view.RevealedEmbed(guesser, file)
                    if guesser.winning_message is None:
                        await guesser.channel.send(embed=embed, file=file)
                    else:
                        await guesser.winning_message.reply(embed=embed, file=file)

        except discord.errors.NotFound:
            log.warning(f"The channel {guesser.channel.id} could not be found")

        # Clean up custom pokemon
        if guesser.is_custom:
            log.debug("Removing custom Pokemon file")
            files_to_remove = [
                self.get_pokemon_original_img_path(guesser.pokemon),
                self.get_pokemon_hidden_img_path(guesser.pokemon),
                self.get_pokemon_revealed_img_path(guesser.pokemon),
            ]
            for file in files_to_remove:
                try:
                    if file is not None:
                        log.debug(f"Removing {file}")
                        os.remove(file)
                except OSError:
                    log.exception(f"Could not remove custom pokemon file {file}")
            log.info("Removed custom Pokemon files")

    def get_pokemon_original_img_path(self, pokemon: PokemonData) -> Path:
        if isinstance(pokemon, CustomPokemonData):
            return pokemon.original_img_path
        return ORIGINAL_IMG_DIR / f"{pokemon.id}.png"

    def get_pokemon_hidden_img_path(self, pokemon: PokemonData) -> Path:
        if isinstance(pokemon, CustomPokemonData):
            return pokemon.hidden_img_path
        return HIDDEN_IMG_DIR / f"{pokemon.id}.png"

    def get_pokemon_revealed_img_path(self, pokemon: PokemonData) -> Path:
        if isinstance(pokemon, CustomPokemonData):
            return pokemon.revealed_img_path
        return REVEALED_IMG_DIR / f"{pokemon.id}.png"
