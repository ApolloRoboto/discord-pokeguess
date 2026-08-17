# PokeGuess

Who’s That Pokemon!

Recreate the most nostalgic guessing game into your server. You can also create your own!

[Invite link](https://discord.com/api/oauth2/authorize?client_id=1052405591680757961&permissions=2147518464&scope=bot)

Find it on:
- [discord.bots.gg](https://discord.bots.gg/bots/1052405591680757961)
- [top.gg](https://top.gg/bot/1052405591680757961)
- [discordbotlist.com](https://discordbotlist.com/bots/pokeguess)
- [discords.com](https://discords.com/bots/bot/1052405591680757961)
- [discord.me](https://discord.me/pokeguess)

# Running the bot

Create a `.env` file with the following content.

```env
# Discord
DISCORD_BOT_TOKEN=
DISCORD_APPLICATION_ID=
```

Install dependencies
```bash
python -m pip install .
```

Run the bot.
```bash
python ./src/main.py
```

One manual action needs to be done to update the slash commands. As the owner, send a private message with `!sync` to the bot.

## With Docker

```bash
docker-compose build
docker-compose --env-file ./.env up
```
