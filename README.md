# nyah-bot
A Discord bot built for waifus. Created from [discord-bot-template](https://github.com/notchum/discord-bot-template).

## Features
- Waifus

---

## Environment Setup
Rename `.env.example` to just `.env` and open it up. Follow the directions in the comments of that file to obtain and fill out the API Keys needed.

> **Note**: The only two environment variables that must be filled are `DISCORD_BOT_TOKEN` and `RETHINKDB_SERVER_HOST`. The [Deployment](#deployment) section below will cover how to set up a RethinkDB instance in Docker.

---

## Discord Application Setup
The directions in the comment for filling out `DISCORD_BOT_TOKEN` in the `.env` file only tell you how to create a Discord bot, but permissions must be explicitly set in Discord's portal before inviting your bot to your server.

### Privileged Gateway Intents
In the Discord Developer Application Portal, under "Settings" > "Bot", scroll down to "Privileged Gateway Intents" and turn on Server Members and Message Content.

### Scopes
In the Discord Developer Application Portal, under "Settings" > "OAuth2" > "URL Generator", there is a "Scopes" selection. Check both `bot` and `applications.commands`.

### Bot Permissions
In the same "URL Generator" settings page, a new selection box should have appeared - "Bot Permissions". Check the boxes listed below:
- Manage Roles
- Read Messages/View Channels
- Manage Events
- Create Events
- Send Messages
- Create Public Threads
- Send Messages in Threads
- Manage Threads
- Embed Links
- Attach Files
- Read Message History
- Use External Emojis

---

## Deployment
There are a lot of ways to deploy a Discord bot but I prefer [Docker](https://www.docker.com/) so that is what I'll be covering here. Here are some example snippets to help you get started creating a container.

> **NOTE**: `<timezone>` is in the format shown [here](https://en.wikipedia.org/wiki/List_of_tz_database_time_zones#List) under "TZ database name".

### docker-compose (recommended)
```yaml
    version: "2.1"
    services:
      nyah-bot:
        image: notchum/nyah-bot:latest
        container_name: nyah-bot
        env_file: .env
        environment:
          - TZ=<timezone>
        restart: unless-stopped
```

### docker cli
```sh
$ docker run \
    --name nyah-bot \
    --restart unless-stopped \
    --env-file .env \
    -e TZ=<timezone> \
    -d notchum/nyah-bot:latest
```

### RethinkDB Setup
[RethinkDB](https://rethinkdb.com/) is the database software that the bot relies on. You can [install](https://rethinkdb.com/docs/install/) it on the same server you use for deployment using one of the packages or, if you went the Docker route above, I would recommend just installing their [Docker image](https://registry.hub.docker.com/_/rethinkdb/).

> **Note**: In your `.env` file, you must provide the address/hostname of the server hosting your RethinkDB instance under `RETHINKDB_SERVER_HOST`. If using Docker, you __cannot__ use `localhost`/`127.0.0.1` but instead you must use the address/hostname of the server itself.

---

## Development
Clone this repo or your fork of it. `cd` to the directory you just cloned.

### Dependencies
Every Python package can be installed using:
```sh
$ pip install -r requirements.txt
```
- [disnake](https://docs.disnake.dev/en/latest/api.html)
- [motor](https://github.com/mongodb/motor)
- [beanie](https://github.com/BeanieODM/beanie)
- [aiofiles](https://pypi.org/project/aiofiles/)
- [aiohttp-client-cache](https://github.com/requests-cache/aiohttp-client-cache)
- [python-dotenv](https://pypi.org/project/python-dotenv/)
- [loguru](https://github.com/Delgan/loguru)
- [ruff](https://github.com/astral-sh/ruff)
- [Google-Images-Search](https://github.com/arrrlo/Google-Images-Search)
- [Pillow](https://python-pillow.org/)

### Running nyah-bot
Then run the bot using: 
```sh
$ python launcher.py
```

### Building Docker Image
Once in the `nyah-bot` directory, build the image:
```sh
$ docker build -t nyah-bot .
```
Optionally, if you have a need for multiple image versions, tag the image with a version number by filling out `<version>`:
```sh
$ docker build -t nyah-bot:<version> .
```
Refer to [Deployment](#deployment) for a guide on running the Docker image(s) you just built.
