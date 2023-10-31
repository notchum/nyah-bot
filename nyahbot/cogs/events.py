import re
import random
import datetime

import disnake
from disnake.ext import commands

from bot import NyahBot
from models import NyahGuild, NyahPlayer
from nyahbot.util import (
    utilities,
)

class Events(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot: NyahBot = bot

    @commands.Cog.listener()
    async def on_slash_command(self, inter: disnake.ApplicationCommandInteraction):
        """ Client event when a command is used. """
        return
        #TODO figure out what to do with setup_finished - is it needed?   
        if inter.data.name == "setup": return

        guild_exists_in_db = r.db("nyah") \
                                .table("guilds") \
                                .get_all(str(inter.guild.id), index="guild_id") \
                                .count() \
                                .eq(1) \
                                .run(conn)
        if not guild_exists_in_db:
            return await inter.guild.system_channel.send(
                embed=utilities.get_error_embed(f"A database entry doesn't exist for this guild! Please contact {self.bot.owner.mention}")
            )
        setup_finished = r.db("nyah") \
                            .table("guilds") \
                            .get(str(inter.guild.id)) \
                            .get_field("setup_finished") \
                            .run(conn) 
        if not setup_finished:         
            return await inter.guild.system_channel.send(
                embed=utilities.get_error_embed("Use `/setup` to ensure all bot functions are available!")
            )

    @commands.Cog.listener()
    async def on_slash_command_error(self, inter: disnake.ApplicationCommandInteraction, error: commands.CommandError):
        """ Client event when a slash command catches an error. """
        return
        #TODO fix this bullshit
        original_response = await inter.original_response()
        if original_response.flags.loading:
            if isinstance(error, commands.CommandOnCooldown):
                await inter.edit_original_response(
                    content=f"This command is on cooldown... try again in {error.retry_after:.2f} seconds."
                )
            await inter.edit_original_response(create_trace(error))
        else:
            if isinstance(error, commands.CommandOnCooldown):
                await inter.response.send_message(
                    content=f"This command is on cooldown... try again in {error.retry_after:.2f} seconds.",
                    ephemeral=True
                )
            await inter.response.send_message(create_trace(error), ephemeral=True)
        self.bot.logger.error(f"{inter.guild.name}[{inter.guild.id}] | "
                     f"{inter.channel.name}[{inter.channel.id}] | "
                     f"{inter.author}[{inter.author.id}] | "
                     f"Reason [{error}]")

    @commands.Cog.listener()
    async def on_slash_command_completion(self, inter: disnake.ApplicationCommandInteraction):
        """ Client event when a slash command has been successfully executed. """
        self.bot.logger.info(f"{inter.guild.name}[{inter.guild.id}] | "
                             f"{inter.channel.name}[{inter.channel.id}] | "
                             f"{inter.author}[{inter.author.id}] | "
                             f"Used {inter.application_command.cog_name}::{inter.application_command.name}")

    @commands.Cog.listener()
    async def on_connect(self):
        """ Client event when it connects. """
        self.bot.logger.success("CONNECTED TO DISCORD")

    @commands.Cog.listener()
    async def on_reconnect(self):
        """ Client event when it is reconnecting. """
        self.bot.logger.info("RECONNECTING TO DISCORD")

    @commands.Cog.listener()
    async def on_disconnect(self):
        """ Client event when it disconnects. """
        self.bot.logger.warning("DISCONNECTED FROM DISCORD")

    @commands.Cog.listener()
    async def on_guild_join(self, guild: disnake.Guild):
        """ Client event when it creates or joins a guild. """
        if await self.bot.mongo.check_nyah_guild_exists(guild):
            return
        
        nyah_guild = NyahGuild(
            guild_id=guild.id,
            name=guild.name,
            waifu_war_channel_id=guild.system_channel.id,
            waifu_war_hour=18,
            waifu_max_marriages=3,
            interval_claim_mins=60,
            interval_duel_mins=180,
            interval_minigame_mins=60,
            interval_season_days=28,
            timestamp_last_season_end=None,
        )
        await self.bot.mongo.insert_nyah_guild(nyah_guild)
        self.bot.logger.success(f"Created database entry for guild '{guild.name}'[{guild.id}]")

        for member in guild.members:
            if await self.bot.mongo.check_nyah_player_exists(member):
                continue
            if member.bot:
                continue
            
            nyah_player = NyahPlayer(
                user_id=member.id,
                name=member.name,
                score=0,
                money=0,
                xp=0,
                level=0,
                wishlist=[],
                timestamp_last_duel=None,
                timestamp_last_claim=None,
                timestamp_last_minigame=None
            )
            await self.bot.mongo.insert_nyah_player(nyah_player)
            self.bot.logger.info(f"{guild.name}[{guild.id}] | "
                                 f"Created database entry for member '{member.name}'[{member.id}]")

    @commands.Cog.listener()
    async def on_guild_remove(self, guild: disnake.Guild):
        """ Client event when it leaves a guild. """
        pass # TODO add in_server bool to NyahGuild

    @commands.Cog.listener()
    async def on_guild_update(self, before: disnake.Guild, after: disnake.Guild):
        """ Client event when a guild is updated. """
        if before.name != after.name:
            self.bot.logger.info(f"{before.name}[{before.id}] | "
                                 f"Changed guild name to {after.name}")
            nyah_guild = await self.bot.mongo.fetch_nyah_guild(after)
            nyah_guild.name = after.name
            await self.bot.mongo.update_nyah_guild(nyah_guild)

    @commands.Cog.listener()
    async def on_member_join(self, member: disnake.Member):
        """ Guild event when someone joins. """
        if await self.bot.mongo.check_nyah_player_exists(member):
            return
        if member.bot:
            return

        nyah_player = NyahPlayer(
            user_id=member.id,
            name=member.name,
            score=0,
            money=0,
            xp=0,
            level=0,
            wishlist=[],
            timestamp_last_duel=None,
            timestamp_last_claim=None,
            timestamp_last_minigame=None
        )
        await self.bot.mongo.insert_nyah_player(nyah_player)
        self.bot.logger.info(f"{member.guild.name}[{member.guild.id}] | "
                             f"Created database entry for member '{member.name}'[{member.id}]")

    @commands.Cog.listener()
    async def on_user_update(self, before: disnake.User, after: disnake.User):
        """ Discord event when someone updates their user profile. """
        if before.bot:
            return
        if before.name != after.name:
            self.bot.logger.info(f"{before.name}[{before.id}] | "
                                 f"Changed username to {after.name}")
            nyah_player = await self.bot.mongo.fetch_nyah_player(after)
            nyah_player.name = after.name
            await self.bot.mongo.update_nyah_player(nyah_player)

    @commands.Cog.listener()
    async def on_guild_scheduled_event_create(self, event: disnake.GuildScheduledEvent):
        """ Called when a guild scheduled event is created. """
        self.bot.logger.info(f"{event.guild.name}[{event.guild.id}] | "
                             f"{event.name}[{event.id}] | "
                             f"Event created")

    @commands.Cog.listener()
    async def on_guild_scheduled_event_delete(self, event: disnake.GuildScheduledEvent):
        """ Called when a guild scheduled event is deleted. """
        self.bot.logger.info(f"{event.guild.name}[{event.guild.id}] | "
                             f"{event.name}[{event.id}] | "
                             f"Event deleted")

    @commands.Cog.listener()
    async def on_guild_scheduled_event_update(self, before: disnake.GuildScheduledEvent, after: disnake.GuildScheduledEvent):
        """ Called when a guild scheduled event is updated. """
        self.bot.logger.info(f"{before.guild.name}[{before.guild.id}] | "
                             f"{before.name}[{before.id}] | "
                             f"Event updated")

def setup(bot: commands.Bot):
    bot.add_cog(Events(bot))