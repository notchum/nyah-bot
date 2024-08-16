import traceback

import disnake
from disnake.ext import commands
from loguru import logger

import models
from bot import NyahBot
from helpers import ErrorEmbed


class Events(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot: NyahBot = bot

    @commands.Cog.listener()
    async def on_slash_command(self, inter: disnake.ApplicationCommandInteraction):
        """Client event when a command is used."""
        if inter.guild.id in [776929597567795247, 1169450511133589604]:
            if not self.bot.config.TEST_MODE:
                return await inter.response.send_message(
                    embed=ErrorEmbed("The bot is not configured for test mode.")
                )
            else:
                pass
        elif self.bot.config.TEST_MODE:
            return await inter.response.send_message(
                embed=ErrorEmbed("The bot is configured for test mode.")
            )
        else:
            pass

    @commands.Cog.listener()
    async def on_slash_command_error(
        self, inter: disnake.ApplicationCommandInteraction, error: commands.CommandError
    ):
        """Client event when a slash command catches an error."""
        trace = traceback.format_exception(type(error), error, error.__traceback__)
        traceback_str = "".join(trace)
        logger.exception(traceback_str)
        logger.exception(
            f"{inter.guild.name}[{inter.guild.id}] | "
            f"{inter.channel.name}[{inter.channel.id}] | "
            f"{inter.author}[{inter.author.id}] | "
            f"{inter.application_command.cog_name}::{inter.application_command.name} | "
            f"Reason: [{error}]"
        )

    @commands.Cog.listener()
    async def on_slash_command_completion(
        self, inter: disnake.ApplicationCommandInteraction
    ):
        """Client event when a slash command has been successfully executed."""
        logger.info(
            f"{inter.guild.name}[{inter.guild.id}] | "
            f"{inter.channel.name}[{inter.channel.id}] | "
            f"{inter.author}[{inter.author.id}] | "
            f"Used {inter.application_command.cog_name}::{inter.application_command.name}"
        )

    @commands.Cog.listener()
    async def on_connect(self):
        """Client event when it connects."""
        logger.info("CONNECTED TO DISCORD")

    @commands.Cog.listener()
    async def on_reconnect(self):
        """Client event when it is reconnecting."""
        logger.info("RECONNECTING TO DISCORD")

    @commands.Cog.listener()
    async def on_disconnect(self):
        """Client event when it disconnects."""
        logger.warning("DISCONNECTED FROM DISCORD")

    @commands.Cog.listener()
    async def on_guild_join(self, guild: disnake.Guild):
        """Client event when it creates or joins a guild."""
        if await self.bot.mongo.check_nyah_guild_exists(guild):
            return

        nyah_guild = models.NyahGuild(
            guild_id=guild.id,
            name=guild.name,
            waifu_war_channel_id=guild.system_channel.id,
        )
        await self.bot.mongo.insert_nyah_guild(nyah_guild)
        logger.info(f"Created database entry for guild '{guild.name}'[{guild.id}]")

        for member in guild.members:
            if await self.bot.mongo.check_nyah_player_exists(member):
                continue
            if member.bot:
                continue

            nyah_player = models.NyahPlayer(
                user_id=member.id,
                name=member.name,
                score=0,
                money=0,
                xp=0,
                level=0,
                wishlist=[],
                timestamp_last_duel=None,
                timestamp_last_claim=None,
                timestamp_last_minigame=None,
            )
            await self.bot.mongo.insert_nyah_player(nyah_player)
            logger.info(
                f"{guild.name}[{guild.id}] | "
                f"Created database entry for member '{member.name}'[{member.id}]"
            )

    @commands.Cog.listener()
    async def on_guild_remove(self, guild: disnake.Guild):
        """Client event when it leaves a guild."""
        pass  # TODO add in_server bool to NyahGuild

    @commands.Cog.listener()
    async def on_guild_update(self, before: disnake.Guild, after: disnake.Guild):
        """Client event when a guild is updated."""
        if before.name != after.name:
            logger.info(
                f"{before.name}[{before.id}] | " f"Changed guild name to {after.name}"
            )
            nyah_guild = await self.bot.mongo.fetch_nyah_guild(after)
            nyah_guild.name = after.name
            await self.bot.mongo.update_nyah_guild(nyah_guild)

    @commands.Cog.listener()
    async def on_member_join(self, member: disnake.Member):
        """Guild event when someone joins."""
        if await self.bot.mongo.check_nyah_player_exists(member):
            return
        if member.bot:
            return

        nyah_player = models.NyahPlayer(
            user_id=member.id,
            name=member.name,
            score=0,
            money=0,
            xp=0,
            level=0,
            wishlist=[],
            timestamp_last_duel=None,
            timestamp_last_claim=None,
            timestamp_last_minigame=None,
        )
        await self.bot.mongo.insert_nyah_player(nyah_player)
        logger.info(
            f"{member.guild.name}[{member.guild.id}] | "
            f"Created database entry for member '{member.name}'[{member.id}]"
        )

    @commands.Cog.listener()
    async def on_user_update(self, before: disnake.User, after: disnake.User):
        """Discord event when someone updates their user profile."""
        if before.bot:
            return
        if before.name != after.name:
            logger.info(
                f"{before.name}[{before.id}] | " f"Changed username to {after.name}"
            )
            nyah_player = await self.bot.mongo.fetch_nyah_player(after)
            nyah_player.name = after.name
            await self.bot.mongo.update_nyah_player(nyah_player)

    @commands.Cog.listener()
    async def on_guild_scheduled_event_create(self, event: disnake.GuildScheduledEvent):
        """Called when a guild scheduled event is created."""
        logger.info(
            f"{event.guild.name}[{event.guild.id}] | "
            f"{event.name}[{event.id}] | "
            f"Event created"
        )

    @commands.Cog.listener()
    async def on_guild_scheduled_event_delete(self, event: disnake.GuildScheduledEvent):
        """Called when a guild scheduled event is deleted."""
        logger.info(
            f"{event.guild.name}[{event.guild.id}] | "
            f"{event.name}[{event.id}] | "
            f"Event deleted"
        )

    @commands.Cog.listener()
    async def on_guild_scheduled_event_update(
        self, before: disnake.GuildScheduledEvent, after: disnake.GuildScheduledEvent
    ):
        """Called when a guild scheduled event is updated."""
        logger.info(
            f"{before.guild.name}[{before.guild.id}] | "
            f"{before.name}[{before.id}] | "
            f"Event updated"
        )


def setup(bot: commands.Bot):
    bot.add_cog(Events(bot))
