from datetime import datetime, timezone
import random
from discord import Embed, Color, File
from zalgo_text.zalgo import zalgo
from models.guesser import Guesser

hidden_color = Color.from_str("#2f3136")
revealed_color = Color.from_str("#2f3136")
hint_color = Color.from_str("#2f3136")
error_color = Color.from_str("#F73154")

# The format is for the winner's name
winner_text: list[str] = [
    "{} got it right.",
    "{} won this round.",
    "{} made a good guess.",
    "{} knows that Pokemon.",
    "Let's go {}!",
    "I choose {}.",
]
failed_text: list[str] = [
    "No one found it, better luck next time!",
    "Give it another try?",
    "Let's do it again!",
    "Let's play again!",
    "Was it that hard?",
]
close_answer_text: list[str] = [
    "You're pretty close.",
    "That's almost it!",
    "So close!",
    "You're almost there!",
    "You're on the right track!",
    "You're getting closer!",
    "That's almost correct",
]


class GenericErrorEmbed(Embed):
    def __init__(self):
        super().__init__()
        self.color = error_color
        self.title = "An error happened, I Couldn't start the game"


class ProcessingActiveEmbed(Embed):
    def __init__(self):
        super().__init__()
        self.color = error_color
        self.title = "Wait a minute! Someone else is posting a custom image"


class ProcessingFailedEmbed(Embed):
    def __init__(self):
        super().__init__()
        self.color = error_color
        self.title = "I could not process this image, try another one."


class InvalidMediaTypeEmbed(Embed):
    def __init__(self):
        super().__init__()
        self.color = error_color
        self.title = "Invalid image type, try to use a PNG with transparency."


class MissingPermissionsEmbed(Embed):
    def __init__(self):
        super().__init__()
        self.color = error_color
        self.title = "I do not have permissions to read or write messages here. Try in another channel."


class InvalidTimeoutEmbed(Embed):
    def __init__(self):
        super().__init__()
        self.color = error_color
        self.title = "Use A timeout between 15 and 300 seconds"


class AlreadyActiveEmbed(Embed):
    def __init__(self):
        super().__init__()
        self.color = error_color
        self.title = "A guessing game is already active."


class CloseAnswerEmbed(Embed):
    def __init__(self):
        super().__init__()
        self.color = hint_color
        self.title = random.choice(close_answer_text)


class HintEmbed(Embed):
    def __init__(self, guesser: Guesser):
        super().__init__()
        self.color = hint_color

        if guesser.hints_given >= 3:
            self.title = "I can't give more hints!"
            return

        self.title = "Here is a hint"

        self.description = "The name is: "

        for i, letter in enumerate(guesser.pokemon.name):
            if i <= guesser.hints_given:
                self.description += " " + letter
            else:
                self.description += " \_"


class HiddenEmbed(Embed):
    def __init__(self, guesser: Guesser, image_file: File):
        super().__init__()

        self.color = hidden_color
        self.title = "Who's That Pokemon?"

        self.description = "Ends " + datetime_to_discord_timestamp(guesser.end_time)

        if guesser.custom:
            self.set_footer(text=f"Custom image from {guesser.author.display_name}")

        self.set_image(url=f"attachment://{image_file.filename}")

        # For Debuging
        # self.set_footer(text=guesser.pokemon.name)


class RevealedEmbed(Embed):
    def __init__(self, guesser: Guesser, image_file: File):
        super().__init__()

        self.color = revealed_color
        self.title = f"It's {guesser.pokemon.name}!"

        number = "Custom" if guesser.custom else f"#{guesser.pokemon.id}"
        self.add_field(name="Number", value=number)
        self.add_field(name="Total Guesses", value=guesser.total_guesses)

        self.set_image(url=f"attachment://{image_file.filename}")

        if guesser.winner is not None:
            winner = guesser.winner

            self.description = random.choice(winner_text).format(winner.mention)

            self.set_thumbnail(url=winner.display_avatar.url)

        else:
            self.description = random.choice(failed_text)

        # missingno easteregg
        if guesser.pokemon.id == 0:
            corrupt_embed(self)


def datetime_to_discord_timestamp(dt: datetime) -> str:
    # return int((d - datetime(1970, 1, 1)).total_seconds())
    return f"<t:{int(dt.replace(tzinfo=timezone.utc).timestamp())}:R>"


text_corruptor = zalgo()
text_corruptor.numAccentsUp = (1, 5)
text_corruptor.numAccentsDown = (1, 30)
text_corruptor.numAccentsMiddle = (1, 5)
text_corruptor.maxAccentsPerLetter = 10


def corrupt_embed(embed: Embed):
    embed.title = text_corruptor.zalgofy(embed.title)
    embed.description = text_corruptor.zalgofy(embed.description)
    if embed.footer is not None and embed.footer.text is not None:
        embed.footer.text = text_corruptor.zalgofy(embed.footer.text)
    if embed.author is not None and embed.author.name is not None:
        embed.author.name = text_corruptor.zalgofy(embed.author.name)

    # Need to clear and readd the fields, cannot change them otherwise
    fields = embed.fields.copy()
    embed.clear_fields()
    for field in fields:
        embed.add_field(
            name=text_corruptor.zalgofy(field.name),
            value=text_corruptor.zalgofy(field.value),
            inline=field.inline,
        )
