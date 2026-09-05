import logging
from dataclasses import dataclass

import aiohttp
from discord.ext.commands import AutoShardedBot

log = logging.getLogger(__name__.removesuffix("_service"))


@dataclass
class TopggServiceErrorResponse:
    type: str
    title: str
    status: int
    detail: str


class TopggService:
    def __init__(self, token: str, http_client: aiohttp.ClientSession):
        self.token = token
        self.http_client = http_client

        self.base_url = "https://top.gg/api/v1"

    async def post_commands(self, bot: AutoShardedBot):
        """https://docs.top.gg/api/v1/projects#put-/projects/project_id/commands"""
        url = f"{self.base_url}/projects/@me/commands"

        commands = await bot.tree.fetch_commands()
        data = [c.to_dict() for c in commands]

        headers = {
            "Authorization": "Bearer " + self.token,
            "Content-Type": "application/json",
        }

        return

        async with self.http_client.put(url, json=data, headers=headers) as response:
            if response.status != 204:
                res_data = await response.text()
                log.error(
                    f"Failed to post commands on Top.gg ({response.status}) {res_data}"
                )

    async def post_metrics(self, bot: AutoShardedBot):
        """https://docs.top.gg/api/v1/projects#patch-/projects/project_id/metrics"""
        url = f"{self.base_url}/projects/@me/metrics"

        data = {
            "server_count": len(bot.guilds),
            "shard_count": bot.shard_count,
        }

        headers = {
            "Authorization": "Bearer " + self.token,
            "Content-Type": "application/json",
        }

        return

        async with self.http_client.patch(url, json=data, headers=headers) as response:
            if response.status != 204:
                res_data = await response.text()
                log.error(
                    f"Failed to post metrics on Top.gg ({response.status}) {res_data}"
                )
