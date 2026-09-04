import logging
from dataclasses import dataclass
from importlib.metadata import version

import aiohttp
from discord import Client
from discord.ext.commands.bot import BotBase

log = logging.getLogger(__name__.removesuffix("_service"))


@dataclass
class TopggServiceErrorResponse:
    type: str
    title: str
    status: int
    detail: str


class TopggService:
    def __init__(self, token: str):
        self.token = token
        self.base_url = "https://top.gg/api/v1"
        self.user_agent = f"pokeguess/{version('pokeguess')} (+https://github.com/ApolloRoboto/discord-pokeguess)"

        headers = {
            "User-Agent": self.user_agent,
            "Authorization": "Bearer " + self.token,
            "Content-Type": "application/json",
        }

        self.session = aiohttp.ClientSession(
            headers=headers,
        )

    async def close(self):
        await self.session.close()

    async def post_commands(self, bot: BotBase):
        """https://docs.top.gg/api/v1/projects#put-/projects/project_id/commands"""
        url = f"{self.base_url}/projects/@me/commands"

        commands = await bot.tree.fetch_commands()
        data = [c.to_dict() for c in commands]

        async with self.session.put(url, json=data) as response:
            if response.status != 204:
                res_data = await response.text()
                log.error(
                    f"Failed to post commands on Top.gg ({response.status}) {res_data}"
                )

    async def post_metrics(self, bot: Client):
        """https://docs.top.gg/api/v1/projects#patch-/projects/project_id/metrics"""
        url = f"{self.base_url}/projects/@me/metrics"

        data = {
            "server_count": len(bot.guilds),
            "shard_count": bot.shard_count,
        }

        async with self.session.patch(url, json=data) as response:
            if response.status != 204:
                res_data = await response.text()
                log.error(
                    f"Failed to post metrics on Top.gg ({response.status}) {res_data}"
                )
