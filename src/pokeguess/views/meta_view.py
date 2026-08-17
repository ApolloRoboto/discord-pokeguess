import discord
from discord import ButtonStyle, ClientUser, Member, User

INVITE_URL = "https://discord.com/api/oauth2/authorize?client_id=1052405591680757961&permissions=2147518464&scope=bot"


class InviteView(discord.ui.View):
    def __init__(self, bot: Member | User | ClientUser):
        super().__init__()

        self.add_item(
            discord.ui.Button(
                label="👀 Click here to invite me to your server!",
                style=ButtonStyle.url,
                url=INVITE_URL,
            )
        )
