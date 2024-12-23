import re
import random
import typing
import asyncio
import datetime
from collections import deque

import disnake
from disnake.ext import commands, tasks
from loguru import logger

import utils
from bot import NyahBot
from models import Claim, Event
from helpers import ErrorEmbed, WaifuCoreEmbed, WaifuClaimEmbed, WaifuHaremEmbed, WaifuBaseEmbed
from utils.constants import Emojis, WaifuState, Cooldowns, Experience, Prices, Tiers, Fusions, TIER_EMOJI_MAP, TIER_TITLE_MAP, TIER_COST_MAP,FUSION_TIER_MAP
from utils.bracket import Bracket
from utils.items import ItemFactory
from views import *

class Waifus(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot: NyahBot = bot
        self.last_date = datetime.date.today()
        self.waifu_housekeeping.start()
        # self.waifu_war_creation.start()
        self.waifu_war_tasks = {}

    ##*************************************************##
    ##********           ABSTRACTIONS           *******##
    ##*************************************************##

    async def get_waifu_war_role(self, guild: disnake.Guild) -> None | disnake.Role:
        """ Gets the Waifu War role for the guild. 
        
            Parameters
            ----------
            guild: `disnake.Guild`
                The guild that has the role.

            Returns
            -------
            `disnake.Role`
                The Waifu War role of the guild. `None` if it doesn't exist.
        """
        roles = await guild.fetch_roles()
        return disnake.utils.get(roles, name="WAIFU WARRIORS")

    async def get_waifu_war_event(self, guild: disnake.Guild) -> None | disnake.GuildScheduledEvent:
        """ Gets the Waifu War event for the guild.

            Parameters
            ----------
            guild: `disnake.Guild`
                The guild that has the event.
            
            Returns
            -------
            `disnake.GuildScheduledEvent`
                The Waifu War event of the guild. `None` if it doesn't exist.
        """
        # TODO, guild.scheduled_events seem to be cached or something, only fetch can get the latest users
        # events = await guild.fetch_scheduled_events(with_user_count=True)
        for event in guild.scheduled_events:
            if event.name == "Waifu War": #TODO add better check - events in database?
                return event
        return None

    async def schedule_waifu_war_event(
        self,
        guild: disnake.Guild,
        start_time: datetime.datetime
    ) -> None:
        """ Schedules an event for Waifu Wars.

            Parameters
            ----------
            guild: `disnake.Guild`
                The guild to create the event in.
            start_time: `datetime.datetime`
                The time to schedule the event for.
        """
        # get an inspirational quote
        try:
            async with self.bot.session.get(url="https://animechan.xyz/api/random") as response:
                if response.status != 200:
                    logger.error(f"Animechan API returned status '{response.status}'")
                    quote = ""
                else:
                    body = await response.json()
                    quote = f"_{body['quote']}_\n\\- {body['character']}, \"{body['anime']}\""
        except:
            quote = ""
        
        # gather waifu war related info for guild
        nyah_guild = await self.bot.mongo.fetch_nyah_guild(guild)
        waifu_war_channel = await guild.fetch_channel(nyah_guild.waifu_war_channel_id)
        ww_role = await self.get_waifu_war_role(guild)
        
        # create the actual event
        waifu_war_event = await guild.create_scheduled_event(
            name="Waifu War",
            entity_type=disnake.GuildScheduledEventEntityType.external,
            entity_metadata=disnake.GuildScheduledEventMetadata(location=waifu_war_channel.name),
            privacy_level=disnake.GuildScheduledEventPrivacyLevel.guild_only,
            scheduled_start_time=start_time,
            scheduled_end_time=start_time + datetime.timedelta(hours=6),
        )

        # send a message to alert users
        embed = disnake.Embed(
            title="⚔️ THE WAIFU WAR IS SCHEDULED ⚔️",
            description=f"- {ww_role.mention} __**mark yourself as interested**__ to this event to enter this war!\n"
                        f"- Starts: {disnake.utils.format_dt(start_time, "D")}\n\n"
                        f"{quote}",
            color=disnake.Color.random(),
        )
        await waifu_war_channel.send(
            content=f"{ww_role.mention}\n"
                    f"https://discord.com/events/{guild.id}/{waifu_war_event.id}",
            embed=embed,
        )
        logger.info(f"{guild.name}[{guild.id}] | "
                             f"{waifu_war_event.name}[{waifu_war_event.id}] | "
                             f"Created scheduled Waifu War event for {waifu_war_event.scheduled_start_time}")

    async def start_waifu_war_event(self, event: disnake.GuildScheduledEvent) -> None:
        """ Start a Waifu War Discord event.
        
            Parameters
            ----------
            event: `disnake.GuildScheduledEvent`
                The guild event to start. Must be a Waifu War.
        """
        nyah_guild = await self.bot.mongo.fetch_nyah_guild(event.guild)
        waifu_war_channel = await event.guild.fetch_channel(nyah_guild.waifu_war_channel_id)

        # If there aren't at least two people entered, then don't start it
        event_user_ids = await self.get_waifu_war_event_users(event)
        if len(event_user_ids) < 2:
            embed = disnake.Embed(
                title="⚔️ THE WAIFU WAR IS CANCELLED ⚔️",
                description="The minimum amount of users for a Waifu War was not met :(",
                color=disnake.Color.random(),
                timestamp=disnake.utils.utcnow()
            ).set_image(url="https://media.discordapp.net/attachments/741072426984538122/748586578074664980/DzEZ4UsXgAAcFjN.png")
            await waifu_war_channel.send(embed=embed)
            await event.edit(status=disnake.GuildScheduledEventStatus.completed)
            return logger.warning(f"{event.guild.name}[{event.guild.id}] | "
                                           f"{event.name}[{event.id}] | "
                                           f"Waifu War event cancelled due to not enough users")

        if event.guild.id not in self.waifu_war_tasks:
            loop = tasks.Loop(self.waifu_wars, minutes=3.0)
            loop.start(event)
            self.waifu_war_tasks[event.guild.id] = loop
            logger.info(f"{event.guild.name}[{event.guild.id}] | "
                                 f"{event.name}[{event.id}] | "
                                 f"Waifu War started!")
        else:
            return logger.error(f"{event.guild.name}[{event.guild.id}] | "
                                         f"{event.name}[{event.id}] | "
                                         f"Guild already has Waifu War task running!")
        
        embed = disnake.Embed(
            title="⚔️ THE WAIFU WAR HAS STARTED ⚔️",
            color=disnake.Color.random(),
            timestamp=disnake.utils.utcnow()
        ).set_image(url="https://pm1.narvii.com/6201/470b2aef57812d8627c71a16a0736598d01ddea1_hq.jpg")
        await waifu_war_channel.send(embed=embed)

    async def end_waifu_war_event(self, event: disnake.GuildScheduledEvent) -> None:
        """ End a Waifu War Discord event.
        
            Parameters
            ----------
            event: `disnake.GuildScheduledEvent`
                The guild event to end. Must be a Waifu War.
        """
        nyah_guild = await self.bot.mongo.fetch_nyah_guild(event.guild)
        waifu_war_channel = await event.guild.fetch_channel(nyah_guild.waifu_war_channel_id)

        if event.guild.id in self.waifu_war_tasks:
            loop: tasks.Loop = self.waifu_war_tasks[event.guild.id]
            loop.stop()
            await event.edit(status=disnake.GuildScheduledEventStatus.completed)
            logger.info(f"{event.guild.name}[{event.guild.id}] | "
                                 f"{event.name}[{event.id}] | "
                                 f"Waifu War ended!")
        else:
            return logger.error(f"{event.guild.name}[{event.guild.id}] | "
                                         f"{event.name}[{event.id}] | "
                                         f"Guild doesn't have a Waifu War task running!")
        
        embed = disnake.Embed(
            title="⚔️ THE WAIFU WAR IS OVER ⚔️",
            color=disnake.Color.random(),
            timestamp=disnake.utils.utcnow()
        )
        # TODO create an embed with the war results
        await waifu_war_channel.send(embed=embed)

    async def get_waifu_war_event_users(self, event: disnake.GuildScheduledEvent) -> typing.List[int]:
        """ Get users that have met these criteria:
                - Subscribed to the Waifu War event.
                - Have active waifus in their harem.
                - Have the Waifu War user role.
        
            Parameters
            ----------
            event: `disnake.GuildScheduledEvent`
                The guild event to get the users of. Must be a Waifu War.

            Returns
            -------
            List[`int`]
                A list of the user IDs that met the criteria above.
        """
        event_user_ids = []
        ww_role = await self.get_waifu_war_role(event.guild)
        async for user in event.fetch_users():
            member = await event.guild.fetch_member(user.id)
            if ww_role not in member.roles:
                continue
            
            user_active = await self.bot.mongo.fetch_harem_count(member) > 0
            if not user_active:
                continue
            
            if user.id not in event_user_ids:
                event_user_ids.append(user.id)
        
        return event_user_ids

    async def end_waifu_war_season(self, guild: disnake.Guild) -> None:
        """ Resets all user's waifus, scores, and coins in a given guild
            if the guild's reset interval is met.

            Parameters
            ----------
            guild: `disnake.Guild`
                The guild to end the season in.
        """
        nyah_config = await self.bot.mongo.fetch_nyah_config()
        
        season_end_datetime = nyah_config.timestamp_last_season_end + datetime.timedelta(days=nyah_config.interval_season_days)
        if disnake.utils.utcnow() < season_end_datetime:
            return
        
        return logger.debug(f"{guild.name}'s WAIFU WAR SEASON SHOULD END")
        
        nyah_guild = await self.bot.mongo.fetch_nyah_guild(guild)
        waifu_war_channel = await guild.fetch_channel(nyah_config.waifu_war_channel_id)
        ww_role = await self.get_waifu_war_role(guild)
        msg_embed = disnake.Embed(
            title="⚔️ WAIFU WARS SEASON END ⚔️",
            color=disnake.Color.random(),
            description=f"{guild.name}'s Waifu War season is over!\n"
                        f"__All scores will be reset to 0!__"
                        f"__All harems will be fully reset!__",
        )
        
        await waifu_war_channel.send(
            content=ww_role.mention,
            embed=msg_embed,
        )

        r.db("nyah") \
            .table("players") \
            .get_all(str(guild.id), index="guild_id") \
            .update({
                "score": 0
            }) \
            .run(conn)
        r.db("nyah") \
            .table("guilds") \
            .get(str(guild.id)) \
            .update({
                "timestamp_last_season_end": datetime.datetime.now(datetime.timezone.utc)
            }) \
            .run(conn)
        r.db("waifus") \
            .table("claims") \
            .get_all(str(guild.id), index="guild_id") \
            .update({
                "state": None,
                "index": None,
            }) \
            .run(conn)
        # TODO update season results in db

        logger.info(f"{guild.name}[{guild.id}] | "
                             f"Waifu War season has been reset!")

    async def delete_waifu_war_threads(self, guild: disnake.Guild) -> None:
        """ Deletes any threads for waifu wars that are 24 hours old.

            Parameters
            ----------
            guild: `disnake.Guild`
                The guild to delete threads in.
        """
        nyah_guild = await self.bot.mongo.fetch_nyah_guild(guild)
        waifu_war_channel = await guild.fetch_channel(nyah_guild.waifu_war_channel_id)
        for t in waifu_war_channel.threads:
            if t.owner_id == self.bot.user.id and (disnake.utils.utcnow() - t.created_at).total_seconds() >= 3600 * 20: # 20 hrs
                await t.delete()
                logger.info(f"{guild.name}[{guild.id}] | "
                                     f"{waifu_war_channel.name}[{waifu_war_channel.id}] | "
                                     f"Deleted waifu war thread '{t.name}'[{t.id}]")

    async def send_waifu_war_reminder(self, guild: disnake.Guild) -> None:
        """ Send a reminder that the waifu war is starting soon.

            Parameters
            ----------
            guild: `disnake.Guild`
                The guild to send the message in.
        """
        # get the event if it exists
        waifu_war_event = await self.get_waifu_war_event(guild)
        if not waifu_war_event:
            return
        
        # check if it's about 10 minutes prior to event
        minutes_diff = (waifu_war_event.scheduled_start_time - disnake.utils.utcnow()).total_seconds() / 60.0
        if 10.0 < minutes_diff < 11.0:
            # gather waifu war related info for guild
            nyah_guild = await self.bot.mongo.fetch_nyah_guild(guild)
            waifu_war_channel = await guild.fetch_channel(nyah_guild.waifu_war_channel_id)
            ww_role = await self.get_waifu_war_role(guild)
            
            # send a message to alert users
            embed = disnake.Embed(
                title="⚔️ WAIFU WAR REMINDER ⚔️",
                description=f"- {ww_role.mention} __**mark yourself as interested**__ to this event to enter this war!\n"
                            f"- The Waifu War is starting {disnake.utils.format_dt(waifu_war_event.scheduled_start_time, "R")}!",
                color=disnake.Colour.random(),
            )
            await waifu_war_channel.send(
                content=f"{ww_role.mention}\n"
                        f"https://discord.com/events/{guild.id}/{waifu_war_event.id}",
                embed=embed,
            )
            logger.info(f"{guild.name}[{guild.id}] | "
                                 f"{waifu_war_event.name}[{waifu_war_event.id}] | "
                                 f"Sent 10-minute reminder for Waifu War event")

    async def manage_waifu_war_role(self, guild: disnake.Guild) -> None:
        """ Adds/Removes the guild's Waifu War role from it's members.

            Parameters
            ----------
            guild: `disnake.Guild`
                The guild to make the event in.
        """
        ww_role = await self.get_waifu_war_role(guild)
        if not ww_role:
            ww_role = await guild.create_role(
                name="WAIFU WARRIORS",
                mentionable=True,
                color=disnake.Color.from_rgb(235, 69, 158)
            )
        
        for member in guild.members:
            if member.bot:
                continue
            
            harem_size = await self.bot.mongo.fetch_harem_count(member)
            if harem_size > 0 and not member.get_role(ww_role.id):
                # Add user to role if not
                await member.add_roles(ww_role)
            elif harem_size == 0 and member.get_role(ww_role.id):
                # Remove user from role if
                await member.remove_roles(ww_role)

    ##*************************************************##
    ##********              EVENTS              *******##
    ##*************************************************##

    @commands.Cog.listener("on_guild_scheduled_event_update")
    async def on_waifu_war_event_update(
        self,
        before: disnake.GuildScheduledEvent,
        after: disnake.GuildScheduledEvent
    ):
        """ Checks if a Waifu War event started, and starts the task for it. """
        waifu_war_event = await self.get_waifu_war_event(before.guild)
        if waifu_war_event and before.id == waifu_war_event.id:
            if before.status != disnake.GuildScheduledEventStatus.active and after.status == disnake.GuildScheduledEventStatus.active:
                await self.start_waifu_war_event(waifu_war_event)

    ##*************************************************##
    ##********              TASKS               *******##
    ##*************************************************##

    @tasks.loop(time=datetime.time(hour=6, minute=0))
    async def waifu_war_creation(self):
        """ Creates a Waifu War scheduled event in a guild each day. """
        for guild in self.bot.guilds:
            waifu_war_event = await self.get_waifu_war_event(guild)
            if waifu_war_event:
                return
            nyah_config = await self.bot.mongo.fetch_nyah_config()
            start_time = datetime.datetime.combine(
                date=disnake.utils.utcnow().date(),
                time=datetime.time(nyah_config.waifu_war_hour, 0), #??? should this be hour in UTC? it is MDT now...
            )
            await self.schedule_waifu_war_event(guild, start_time)

    @waifu_war_creation.before_loop
    async def init_waifu_war_creation(self):
        await self.bot.wait_until_ready()

    @tasks.loop(minutes=1.0)
    async def waifu_housekeeping(self):
        """ Background task to check for waifu war maintenance. """
        logger.debug(f"Executing waifu housekeeping... [loop #{self.waifu_housekeeping.current_loop}]")

        for guild in self.bot.guilds:
            # add/remove waifu war role from users
            await self.manage_waifu_war_role(guild)

            # send a reminder that the waifu war is starting soon
            await self.send_waifu_war_reminder(guild)
            
            # delete old waifu war threads
            await self.delete_waifu_war_threads(guild)
            
            # end the season if it's time
            await self.end_waifu_war_season(guild)

    @waifu_housekeeping.before_loop
    async def init_waifu_housekeeping(self):
        await self.bot.wait_until_ready()

    # no decorator, but still a task started via scheduled Discord event
    async def waifu_wars(self, waifu_war_event: disnake.GuildScheduledEvent):
        """ Main loop for Waifu Wars.
        
            Parameters
            ----------
            waifu_war_event: `disnake.GuildScheduledEvent`
                The Waifu War event.
        """
        guild = waifu_war_event.guild
        loop: tasks.Loop = self.waifu_war_tasks[guild.id]
        logger.debug(f"Executing Waifu War manager... [loop #{loop.current_loop}]")
        
        # If the waifu war event is not active, then don't continue
        if waifu_war_event and waifu_war_event.status != disnake.GuildScheduledEventStatus.active:
            return logger.error(f"{guild.name}[{guild.id}] started Waifu War manager but the event is inactive")

        # Only create the bracket on the first pass
        if loop.current_loop == 0:
            war = Event(
                event_id=waifu_war_event.id,
                guild_id=guild.id,
                state=disnake.GuildScheduledEventStatus.active,
                timestamp_start=disnake.utils.utcnow(),
                timestamp_end=None
            )
            await war.insert()

            # Create the initial bracket
            bracket = Bracket(war)
            nyah_players = await self.bot.mongo.fetch_active_nyah_players()
            event_user_ids = await self.get_waifu_war_event_users(waifu_war_event)
            
            # Add users to the bracket if they are part of the event
            rank = 1
            for player in nyah_players:
                # If they aren't in the event, then go next
                if player.user_id not in event_user_ids:
                    continue
                user = self.bot.get_user(int(player.user_id))
                # If they don't have any married waifus, then go next
                if await self.bot.mongo.fetch_harem_married_count(user) == 0:
                    continue
                
                # Add to bracket
                bracket.add_team(
                    name=user.name,
                    user_id=player.user_id,
                    ranking=rank
                )
                rank += 1
            bracket.create_bracket()
        
        # Get the waifu war channel
        nyah_guild = await self.bot.mongo.fetch_nyah_guild(guild)
        waifu_war_channel = await guild.fetch_channel(nyah_guild.waifu_war_channel_id)

        # Get the war
        war = await self.bot.mongo.fetch_active_war(guild)

        # Create a bracket object to help us
        bracket = Bracket(war)

        #TODO Print the bracket
        # logger.debug(f"guildname[guildid] Waifu War bracket:")
        # for line in bracket.__str__().split("\n"):
        #     logger.debug(line)

        # Get current round
        current_round = bracket.get_current_round()

        # Check if the round message has already been sent
        round_message_id = bracket.get_round_message_id(current_round)
        if not round_message_id:
            # Get a gif 
            async with self.bot.session.get(url="https://nekos.best/api/v2/thumbsup") as response:
                if response.status != 200:
                    logger.error(f"nekos.best API returned status code `{response.status}`")
                    gif_url="https://img1.ak.crunchyroll.com/i/spire2/180a8752234002128be1dd4459e3e8bd1308352623_full.jpg"
                else:
                    body = await response.json()
                    gif_url = body["results"][0]["url"]
            round_embed = disnake.Embed(
                title=f"Waifu War Round {current_round.number}"
            ).set_thumbnail(url=gif_url)
            round_message = await waifu_war_channel.send(embed=round_embed)
            bracket.set_round_message_id(current_round, str(round_message.id))
            bracket.start_round_matches(current_round)
        else:
            # Try to get the message from cache
            round_message = self.bot.get_message(int(round_message_id))
            # If that didn't work, then get the message from history
            if not round_message:
                async for message in waifu_war_channel.history(limit=100):
                    if message.id == int(round_message_id):
                        round_message = message
        round_embed = round_message.embeds[0]

        # Find how long this round will take
        num_ongoing_matches = bracket.get_num_ongoing_matches(current_round)
        if num_ongoing_matches >= 3:
            voting_time_min = 3
        elif num_ongoing_matches == 2:
            voting_time_min = 2
        elif num_ongoing_matches <= 1:
            voting_time_min = 1
        loop.change_interval(minutes=voting_time_min)
        
        # Get a waifu for both users in every match
        for current_match in bracket.get_round_matches(current_round):
            match_title = f"Match {current_match.number}"

            # Check if there is already a winner for this match
            if bracket.get_match_winner(current_match):
                continue
            else:
                # Add fields to represent this match if it doesn't exist
                if not round_embed.fields or match_title not in [field.name for field in round_embed.fields]:
                    team_1_str = f"<@{current_match.user_red_id}>"
                    team_2_str = "BYE" if current_match.user_blue_id == "BYE" else f"<@{current_match.user_blue_id}>"
                    round_embed.add_field(
                        name=match_title,
                        value=f"🟥 {team_1_str} 🟥 vs. 🟦 {team_2_str} 🟦",
                        inline=False
                    )
                    await round_message.edit(embed=round_embed)

            # If there is a BYE in the match, then set the red team as winner
            if bracket.match_has_bye(current_match):
                bracket.set_match_winner(current_match, current_match.user_red_id)
                continue
            
            # Create the random waifu battle from both users in the match
            random_waifu_red = None
            random_waifu_blue = None
            for user_color, user_id in [("red", current_match.user_red_id), ("blue", current_match.user_blue_id)]:
                opponent_user_id = current_match.user_blue_id if user_color == "red" else current_match.user_red_id
                
                # Check if the user has any waifus left
                user = await self.bot.fetch_user(int(user_id))
                if await self.bot.mongo.fetch_harem_married_count(user) == 0:
                    # If the user is out of waifus, then they lose the match
                    bracket.set_match_winner(current_match, opponent_user_id)
                else:
                    # If the user still has active waifus then get a random one
                    harem_waifu = await self.bot.mongo.fetch_random_harem_married(user)
                    if user_color == "red":
                        random_waifu_red = Claim(**harem_waifu)
                    elif user_color == "blue":
                        random_waifu_blue = Claim(**harem_waifu)
            
            # If there aren't waifus then there's no battle, so go next
            if not random_waifu_red or not random_waifu_blue:
                continue

            # Create the battle
            current_battle = bracket.create_battle(current_match, random_waifu_red, random_waifu_blue)

            # Create vs image
            vs_img_url = await self.bot.create_waifu_vs_img(random_waifu_red, random_waifu_blue)
            
            # Create the battle embed
            ends_at = disnake.utils.utcnow() + datetime.timedelta(minutes=voting_time_min)
            red_waifu = await self.bot.mongo.fetch_waifu(random_waifu_red.slug)
            blue_waifu = await self.bot.mongo.fetch_waifu(random_waifu_blue.slug)
            battle_embed = disnake.Embed(
                title=f"{match_title}  •  Battle {current_battle.number}",
                description=f"**__{red_waifu.name}__** vs. **__{blue_waifu.name}__**\n"
                            f"Voting ends: {disnake.utils.format_dt(ends_at, "R")}",
                color=disnake.Color.random()
            ).set_image(url=vs_img_url)

            # Send the vs image to the thread
            if not round_message.thread:
                await round_message.create_thread(
                    name=round_embed.title,
                    auto_archive_duration=10080
                )
                ww_role = await self.get_waifu_war_role(guild)
                await round_message.thread.send(content=ww_role.mention)
            battle_message = await round_message.thread.send(
                content=str([field.value for field in round_embed.fields if field.name == match_title][0]),
                embed=battle_embed,
                view=WarVoteView(current_battle)
            )
            bracket.set_battle_message_id(current_battle, str(battle_message.id))

        # Wait for the votes to come in
        await asyncio.sleep(voting_time_min * 60)

        # Update the battles in the bracket
        for current_match in bracket.get_round_matches(current_round):
            current_battle = bracket.get_current_battle(current_match)
            if not current_battle or bracket.get_match_winner(current_match):
                continue

            # Remove the voting view from the message
            battle_message_id = bracket.get_battle_message_id(current_battle)
            # Try to get the message from cache
            battle_message = self.bot.get_message(int(battle_message_id))
            # If that didn't work, then get the message from history
            if not battle_message:
                async for message in waifu_war_channel.history(limit=100):
                    if message.id == int(battle_message_id):
                        battle_message = message
            await battle_message.edit(view=None)

            # Count the votes
            vote_info = bracket.count_battle_votes(current_battle)
            
            # Update the user's harem that has the losing waifu
            losing_claim = await self.bot.mongo.fetch_claim(vote_info["loser"]["id"])
            losing_claim.index = None
            losing_claim.state = WaifuState.NULL
            await self.bot.mongo.update_claim(losing_claim)
            losing_user = self.bot.get_user(int(losing_claim.user_id))
            
            # Reindex the losing user's waifus
            losing_harem = await self.bot.mongo.fetch_harem(losing_user)
            await losing_harem.reindex()
            
            # Get the user's waifu that won
            winning_claim = await self.bot.mongo.fetch_claim(vote_info["winner"]["id"])
            winning_user = self.bot.get_user(int(winning_claim.user_id))
            waifu = await self.bot.mongo.fetch_waifu(winning_claim.slug)

            # Edit the message to indicate winner
            embed = disnake.Embed(
                color=disnake.Color.random()
            ).set_thumbnail(url=winning_claim.image_url)
            match vote_info["result"]:
                case "tie":
                    embed.title = "Tied Round!"
                    embed.description = f"{winning_user.mention}'s **__{waifu.name}__** won with {vote_info['winner']['count']} votes!\n" \
                                        f"{losing_user.mention} lost the round with {vote_info['loser']['count']} votes!"
                case "nil":
                    embed.title = "No Votes!"
                    embed.description = f"{winning_user.mention}'s **__{waifu.name}__** was selected as the winner!"
                case "red":
                    embed.title = f"{winning_user.name} Won!"
                    embed.description = f"{winning_user.mention}'s **__{waifu.name}__** won with {vote_info['winner']['count']} votes!\n" \
                                        f"{losing_user.mention} lost the round with {vote_info['loser']['count']} votes!"
                case "blue":
                    embed.title = f"{winning_user.name} Won!"
                    embed.description = f"{winning_user.mention}'s **__{waifu.name}__** won with {vote_info['winner']['count']} votes!\n" \
                                        f"{losing_user.mention} lost the round with {vote_info['loser']['count']} votes!"
                case _:
                    logger.error(f"No result returned for battle '{current_battle.id}'")
            await battle_message.reply(embed=embed)

            # If the loser doesn't have any waifus left, then set the winner of the match
            if await self.bot.mongo.fetch_harem_married_count(losing_user) == 0:
                # If the user is out of waifus, then they lose the match
                bracket.set_match_winner(current_match, str(winning_user.id))
                embed = disnake.Embed(
                    description=f"{winning_user.mention} won the match!",
                    color=disnake.Color.random()
                ).set_author(name=f"{winning_user.name} beat {losing_user.name}!", icon_url=winning_user.display_avatar.url)
                await battle_message.reply(embed=embed)
        
        # Change the embed's fields to mark the match winner if there is one
        for current_match in bracket.get_round_matches(current_round):
            match_title = f"Match {current_match.number}"
            winner_id = bracket.get_match_winner(current_match)
            if winner_id:
                for i, field in enumerate(round_embed.fields):
                    if field.name == match_title:
                        # Replace the box emojis with ❌
                        modified_string = re.sub(
                            pattern=r"🟥 <@(\d+)> 🟥",
                            repl=lambda match: "❌ <@{}> ❌".format(match.group(1)),
                            string=field.value
                        )
                        modified_string = re.sub(
                            r"🟦 <@(\d+)> 🟦",
                            lambda match: "❌ <@{}> ❌".format(match.group(1)),
                            modified_string
                        )

                        # Replace the winner's ID emojis with ✅
                        round_embed.set_field_at(
                            index=i,
                            name=field.name,
                            value=modified_string.replace(
                                "❌ <@{}> ❌".format(winner_id),
                                "✅ <@{}> ✅".format(winner_id)
                            ),
                            inline=field.inline
                        )

                        # Edit the message
                        await round_message.edit(embed=round_embed)
                        break
        
        # Mark the end of the round if it's matches are finished
        if bracket.round_finished(current_round):
            bracket.set_round_timestamp_end(current_round)

            # Give the user's XP at the end of the round
            for user_id in bracket.get_round_participant_ids(current_round):
                user = await guild.fetch_member(int(user_id))
                nyah_player = await self.bot.mongo.fetch_nyah_player(user)
                await nyah_player.add_user_xp(Experience.WAR_ROUND.value)

            # War is over if this round was the last
            if bracket.last_round(current_round):
                await self.end_waifu_war_event(waifu_war_event)

                # TODO Put winner's waifus on cooldown 
                # set state to COOLDOWN and timestamp_cooldown to now
                
                # Give the winner and runner-up awards
                ending_embed = disnake.Embed(
                    color=disnake.Color.random()
                )
                for user_id in bracket.get_round_participant_ids(current_round):
                    user = await guild.fetch_member(int(user_id))
                    nyah_player = await self.bot.mongo.fetch_nyah_player(user)
                    if user_id == winner_id:
                        await nyah_player.add_user_money(Prices.PAYOUT_WAR_FIRST.value)
                        await nyah_player.add_user_xp(Experience.WAR_FIRST.value)
                        ending_embed.title = f"Congratulations to {user.name} for winning the Waifu War!"
                        ending_embed.description += f"- {user.mention} won `{Prices.PAYOUT_WAR_FIRST.value:,}` {Emojis.COINS} and `{Experience.WAR_FIRST.value}` XP!"
                        ending_embed.set_thumbnail(url=user.display_avatar.url)
                    else:
                        await nyah_player.add_user_money(Prices.PAYOUT_WAR_SECOND.value)
                        await nyah_player.add_user_xp(Experience.WAR_SECOND.value)
                        ending_embed.description += f"- {user.mention} won `{Prices.PAYOUT_WAR_SECOND.value:,}` {Emojis.COINS} and `{Experience.WAR_SECOND.value}` XP!"
                # TODO test this
                await waifu_war_channel.send(embed=ending_embed)

                # Reindex all participant's waifus
                for participant in bracket.participants:
                    if participant.user_id == "BYE":
                        continue
                    user = await guild.fetch_member(int(participant.user_id))
                    harem = await self.bot.mongo.fetch_harem(user)
                    await harem.reindex()

    ##*************************************************##
    ##********             COMMANDS             *******##
    ##*************************************************##

    @commands.slash_command()
    async def profile(self, inter: disnake.ApplicationCommandInteraction):
        """ View your level, XP, balance and cooldowns. """
        await inter.response.defer()
        now = disnake.utils.utcnow()

        # Gather user's db info
        nyah_player = await self.bot.mongo.fetch_nyah_player(inter.author)
        
        # Claim cooldowns
        if await nyah_player.user_is_on_cooldown(Cooldowns.CLAIM):
            next_claim_at = await nyah_player.user_cooldown_expiration_time(Cooldowns.CLAIM)
            if now < next_claim_at:
                fmt_claim_times = f"❄️ {disnake.utils.format_dt(next_claim_at, "R")} ({disnake.utils.format_dt(next_claim_at, "t")})"
            else:
                fmt_claim_times = "🟢 **Ready**"
        else:
            fmt_claim_times = "🟢 **Ready**"
        
        # Duel cooldowns
        if await nyah_player.user_is_on_cooldown(Cooldowns.DUEL):
            next_duel_at = await nyah_player.user_cooldown_expiration_time(Cooldowns.DUEL)
            if now < next_duel_at:
                fmt_duel_times = f"❄️ {disnake.utils.format_dt(next_duel_at, "R")} ({disnake.utils.format_dt(next_duel_at, "t")})"
            else:
                fmt_duel_times = "🟢 **Ready**"
        else:
            fmt_duel_times = "🟢 **Ready**"
        
        # Minigame cooldowns
        if await nyah_player.user_is_on_cooldown(Cooldowns.MINIGAME):
            next_minigame_at = await nyah_player.user_cooldown_expiration_time(Cooldowns.MINIGAME)
            if now < next_minigame_at:
                fmt_minigame_times = f"❄️ {disnake.utils.format_dt(next_minigame_at, "R")} ({disnake.utils.format_dt(next_minigame_at, "t")})"
            else:
                fmt_minigame_times = "🟢 **Ready**"
        else:
            fmt_minigame_times = "🟢 **Ready**"
        
        # Player inventory
        player_inventory = []
        for inv_item in nyah_player.inventory:
            if inv_item.amount == 0:
                continue
            item = ItemFactory.create_item(inv_item.type, nyah_player, inv_item.amount)
            player_inventory.append(item)
        if len(player_inventory) == 0:
            fmt_inventory = "-"
        else:
            fmt_inventory = " ".join([i.inv_str for i in player_inventory])

        embed = disnake.Embed(
            color=disnake.Color.random(),
        ) \
        .set_author(name=f"{inter.author.name}'s Profile", icon_url=inter.author.display_avatar.url) \
        .add_field(name="Level", value=f"{nyah_player.level}") \
        .add_field(name="XP", value=f"{nyah_player.xp}/{utils.calculate_accumulated_xp(nyah_player.level + 1)}") \
        .add_field(name=f"Balance", value=f"`{nyah_player.money:,}` {Emojis.COINS}") \
        .add_field(name="Inventory", value=fmt_inventory) \
        .add_field(name="Cooldowns:", value="", inline=False) \
        .add_field(name=f"{Emojis.CLAIM} Drop", value=fmt_claim_times, inline=False) \
        .add_field(name=f"{Emojis.MINIGAME} Minigame", value=fmt_minigame_times, inline=False) \
        .add_field(name=f"{Emojis.DUEL} Duel", value=fmt_duel_times, inline=False)
        
        return await inter.edit_original_response(embed=embed)

    @commands.slash_command()
    async def minigame(
        self,
        inter: disnake.ApplicationCommandInteraction,
        bet: commands.Range[int, 0, 50] = 0
    ):
        """ Play a random waifu minigame for money!
        
            Parameters
            ----------
            bet: `int`
                The amount of money to bet.
        """
        # Gather user's db info
        nyah_player = await self.bot.mongo.fetch_nyah_player(inter.author)
        
        # Check if user's duel on cooldown
        if await nyah_player.user_is_on_cooldown(Cooldowns.MINIGAME):
            next_minigame_at = await nyah_player.user_cooldown_expiration_time(Cooldowns.MINIGAME)
            return await inter.response.send_message(
                content=f"{inter.author.mention} you are on a minigame cooldown now.\n"
                        f"Try again {disnake.utils.format_dt(next_minigame_at, "R")} ({disnake.utils.format_dt(next_minigame_at, "t")})",
                ephemeral=True
            )
        
        # Check if user has enough money
        if nyah_player.money < bet:
            return await inter.response.send_message(
                content=f"{inter.author.mention} you don't have enough money to bet that much.",
                ephemeral=True
            )

        await inter.response.defer()
        
        # Select the type of minigame this will be
        minigame = random.choice(["guess_name", "guess_bust", "guess_age", "smash_or_pass"])

        # Get very popular characters for the minigame
        mutual_aggregation = {"$match": {"popularity_rank": {"$lt": 600}}}

        match minigame:
            case "guess_name":
                waifu = await self.bot.mongo.fetch_random_waifu([mutual_aggregation])
                answer = waifu.name

                embed = disnake.Embed(
                    title="WHO'S THAT WAIFU",
                    description=f"{inter.author.mention} who is this character?",
                    color=disnake.Color.teal()
                ).set_image(waifu.image_url)
                minigame_view = await WaifuNameGuessView.create(inter.author, answer)

                correct_description = f"- Yes! This is **__{answer}__**, good job\n"
                wrong_description = f"- No, this is **__{answer}__** :(\n"
        
            case "guess_bust":
                waifu = await self.bot.mongo.fetch_random_waifu([{"$match": {"bust": {"$ne": None}}}, mutual_aggregation])
                answer = waifu.bust

                embed = disnake.Embed(
                    title="GUESS HER BUST SIZE",
                    description=f"{inter.author.mention} what is **__{waifu.name}'s__** bust measurement?",
                    color=disnake.Color.teal()
                ).set_image(waifu.image_url)
                minigame_view = await WaifuBustGuessView.create(inter.author, answer)

                correct_description = f"- **__{waifu.name}'s__** bust is {answer}, good job\n"
                wrong_description = f"- Sorry, **__{waifu.name}'s__** tits are {answer} :(\n"
        
            case "guess_age":
                waifu = await self.bot.mongo.fetch_random_waifu([{"$match": {"age": {"$ne": None}}}, mutual_aggregation])
                answer = waifu.age

                embed = disnake.Embed(
                    title="AGE GUESS GAME",
                    description=f"{inter.author.mention} how old is **__{waifu.name}__**?",
                    color=disnake.Color.teal()
                ).set_image(waifu.image_url)
                minigame_view = await WaifuAgeGuessView.create(inter.author, answer)

                correct_description = f"- **__{waifu.name}__** is {answer} years old, good job\n"
                wrong_description = f"- Sorry, **__{waifu.name}__** is {answer} :(\n"

            case "smash_or_pass":
                waifu = await self.bot.mongo.fetch_random_waifu([{"$match": {"age": {"$gte": 18}}}, mutual_aggregation])
                
                femboy = False
                if "femboy" in waifu.description.lower():
                    answer = "SMASH"
                    femboy = True
                else:
                    answer = random.choice(["SMASH", "PASS"])

                embed = disnake.Embed(
                    title="SMASH OR PASS?",
                    description=f"{inter.author.mention} would you smash or pass **__{waifu.name}__**?",
                    color=disnake.Color.teal()
                ).set_image(waifu.image_url)
                minigame_view = WaifuSmashOrPassView(inter.author, answer)

                if femboy:
                    correct_description = f"- **__{waifu.name}__** is a femboy... so he is a SMASH, good job\n"
                    wrong_description = f"- **__{waifu.name}__** is a femboy... femboys are always a SMASH... c'mon bro\n"
                else:
                    correct_description = f"- **__{waifu.name}__** is a {answer}, good job\n"
                    wrong_description = f"- **__{waifu.name}__** is a {answer}... c'mon bro\n"
        
        # Send the message
        embed.set_footer(text="You have 10 seconds to answer")
        message = await inter.edit_original_response(embed=embed, view=minigame_view)
        minigame_view.message = message

        # Set timestamp in db
        nyah_player = await self.bot.mongo.fetch_nyah_player(inter.author)
        nyah_player.timestamp_last_minigame = disnake.utils.utcnow()
        await self.bot.mongo.update_nyah_player(nyah_player)

        # Wait for the user to answer
        await minigame_view.wait()
        
        # Calculate the amount of money the user won/lost
        if bet > 0:
            win_amount = bet
            lose_amount = bet * -1
        else:
            win_amount = Prices.PAYOUT_MINIGAME_WIN.value
            lose_amount = 0

        # Create the embed with the result of the user's answer
        if minigame_view.author_won:
            logger.debug(f"{inter.author.name} beat minigame '{minigame}'")
            result_embed = disnake.Embed(
                title="Correct!",
                description=correct_description + 
                            f"- You won `{win_amount:,}` {Emojis.COINS} "
                            f"and `{Experience.MINIGAME_WIN.value}` XP",
                color=disnake.Color.green(),
            )
            await nyah_player.add_user_money(win_amount)
            await nyah_player.add_user_xp(Experience.MINIGAME_WIN.value, inter.author, inter.channel)
        else:
            logger.debug(f"{inter.author.name} lost minigame '{minigame}'")
            result_embed = disnake.Embed(
                title="Wrong!",
                description=wrong_description +
                            f"- You lost `{lose_amount:,}` {Emojis.COINS}",
                color=disnake.Color.red(),
            )
            await nyah_player.add_user_money(lose_amount)

        return await inter.edit_original_response(embeds=[embed, result_embed], view=None)

    @commands.slash_command()
    async def waifudex(
        self,
        inter: disnake.ApplicationCommandInteraction,
        name: str = None,
        series: str = None,
        tag: str = None,
        birthday: bool = False
    ):
        """ View any waifu from the database!

            Parameters
            ----------
            name: `str`
                Get a single waifu entry.
            series: `str`
                Get all waifus from a given series.
            tag: `str`
                Get all waifus that contain this tag.
            birthday: `bool`
                Get all waifus that were born today.
        """
        await inter.response.defer()
        result = None

        # Return the total number of waifus that the user has claimed
        if not name and not series and not tag and not birthday:
            n_total_claims = await self.bot.mongo.fetch_claim_count(inter.author)
            embed = disnake.Embed(
                description=f"You've gotten {n_total_claims} waifus!",
                color=disnake.Color.teal()
            ).set_author(name=f"{inter.author.name}'s waifudex", icon_url=inter.author.display_avatar.url)

            return await inter.edit_original_response(embed=embed)

        # Return all characters from that series
        elif not name and series and not tag and not birthday:
            result = await self.bot.mongo.fetch_waifus_by_series(series)
        
        # Return all characters that have this tag
        elif not name and not series and tag and not birthday:
            result = await self.bot.mongo.fetch_waifus_by_tag(tag)
        
        # Return characters that were born today
        elif not name and not series and not tag and birthday:
            result = await self.bot.mongo.fetch_waifus_birthday_today()

        # Return characters with the same name
        elif name and not series and not tag and not birthday:
            if re.search(r"\[.*\]", name):
                match = re.match(r"^(.*?)\s*\[(.*?)\]$", name)
                name = match.group(1).strip()
                series = match.group(2).strip()
                result = await self.bot.mongo.fetch_waifus_by_name_and_series(name, series)
            else:
                series = ""
                result = await self.bot.mongo.fetch_waifus_by_name(name)

        if not result:
            return await inter.edit_original_response(
                embed=ErrorEmbed(f"Couldn't find any waifus that match:\nname={name}\nseries={series}\ntag={tag}\nbirthday={birthday}")
            )
        
        embeds = []
        for waifu in result:
            embed = WaifuCoreEmbed(waifu)
            embeds.append(embed)
        
        dex_view = await WaifuDexView.create_instance(embeds, inter.author)
        await dex_view.initialize_footers()
        message = await inter.edit_original_response(embed=embeds[0], view=dex_view)
        dex_view.message = message
        return

    @commands.slash_command()
    async def getmywaifu(self, inter: disnake.ApplicationCommandInteraction):
        """ Get a random waifu! """       
        # Gather user's db info
        nyah_player = await self.bot.mongo.fetch_nyah_player(inter.author)
        
        # Check if user's waifu is available to claim
        if await nyah_player.user_is_on_cooldown(Cooldowns.CLAIM):
            next_claim_at = await nyah_player.user_cooldown_expiration_time(Cooldowns.CLAIM)
            return await inter.response.send_message(
                content=f"Whoa now! That's too many waifus right now - this isn't a hanime, big guy.\n"
                        f"Next waifu available at {disnake.utils.format_dt(next_claim_at, "R")} ({disnake.utils.format_dt(next_claim_at, "t")})\n"
                        f"{'🟩' * int(divmod((next_claim_at - disnake.utils.utcnow()).total_seconds(), 3600)[0]):⬜<6}", #TODO fix this shit
                ephemeral=True
            )
        
        # Make sure the waifu war isn't active
        waifu_war_event = await self.get_waifu_war_event(inter.guild)
        if waifu_war_event and waifu_war_event.status == disnake.GuildScheduledEventStatus.active:
            return await inter.response.send_message(
                content=f"Sorry, you cannot get a waifu while a Waifu War is ongoing!",
                ephemeral=True
            )
        
        await inter.response.defer()
        
        # Get a random waifu from the db
        new_waifu = await self.bot.mongo.fetch_random_waifu()
        
        # Create the claim
        claim = await nyah_player.generate_claim(new_waifu)
        
        # Send the waifu
        waifu_embed = WaifuClaimEmbed(new_waifu, claim)
        claim_view = WaifuClaimView(claim, inter.author)
        message = await inter.edit_original_response(
            content=f"**A {'husbando' if new_waifu.husbando else 'waifu'} for {inter.author.mention} :3**",
            embed=waifu_embed,
            view=claim_view
        )
        claim_view.message = message

        # Insert claim in db
        claim.guild_id=message.guild.id
        claim.channel_id=message.channel.id
        claim.message_id=message.id
        claim.jump_url=message.jump_url
        claim.timestamp=message.created_at
        await self.bot.mongo.insert_claim(claim)

        # Update harem in db
        harem = await self.bot.mongo.fetch_harem(inter.author)
        await harem.reindex()

        # Update user info in db
        nyah_player.timestamp_last_claim = disnake.utils.utcnow()
        await self.bot.mongo.update_nyah_player(nyah_player)
        await nyah_player.add_user_xp(Experience.CLAIM.value, inter.author, inter.channel)

        logger.info(f"{inter.guild.name}[{inter.guild.id}] | "
                             f"{inter.channel.name}[{inter.channel.id}] | "
                             f"{inter.author}[{inter.author.id}] | "
                             f"Claimed {new_waifu.slug}[{claim.id}]")
        return

    @commands.slash_command()
    async def buymywaifu(self, inter: disnake.ApplicationCommandInteraction, name: str):
        """Buy a waifu!
        
            Parameters
            ----------
            name: `str`
                The waifu to buy.
        """
        await inter.response.defer()

        if re.search(r"\[.*\]", name):
            match = re.match(r"^(.*?)\s*\[(.*?)\]$", name)
            name = match.group(1).strip()
            series = match.group(2).strip()

            result = await self.bot.mongo.fetch_waifus_by_name_and_series(name, series)
        else:
            result = await self.bot.mongo.fetch_waifus_by_name(name)
        waifu = result[0]

        if not result:
            return await inter.edit_original_response(
                embed=ErrorEmbed(f"Couldn't find `{name}` in the waifu database!")
            )
        
        total_character = await self.bot.mongo.fetch_waifu_count()
        tier = utils.tier_from_rank(total_character, waifu.popularity_rank)
        cost = TIER_COST_MAP[tier].value
        
        embed = WaifuBaseEmbed(waifu)
        embed.description = f"Buy __**{waifu.name}**__ for `{cost:,}` {Emojis.COINS}?"
        
        purchase_view = WaifuPurchaseView(
            embed=embed,
            waifu=waifu,
            author=inter.author,
            cost=cost
        )
        message = await inter.edit_original_response(embed=embed, view=purchase_view)
        purchase_view.message = message

    @commands.slash_command()
    async def listmywaifus(self, inter: disnake.ApplicationCommandInteraction):
        """ List your harem! """
        await inter.response.defer()

        harem = await self.bot.mongo.fetch_harem(inter.author)
        
        if not harem:
            return await inter.edit_original_response(
                embed=ErrorEmbed(f"{inter.author.mention} your harem is empty!\n\nUse `/getmywaifu` to get started")
            )
        
        embed = disnake.Embed(
            description="",
            color=disnake.Color.dark_red()
        )
        embeds = []
        for claim in harem:
            if claim.index == 1:
                embed.set_thumbnail(url=claim.image_url)
            
            embed.description += f"`{claim.index}` {TIER_EMOJI_MAP[claim.tier]} {claim.name} ({claim.skill_str_short}) "

            if claim.state == WaifuState.ACTIVE:
                embed.description += Emojis.STATE_MARRIED
            elif claim.state == WaifuState.COOLDOWN:
                embed.description += Emojis.STATE_COOLDOWN

            #TODO show trait in list
            # if claim.trait_common:
            #     embed.description += Emojis.TRAIT_COMMON
            # if claim.trait_uncommon:
            #     embed.description += Emojis.TRAIT_UNCOMMON
            # if claim.trait_rare:
            #     embed.description += Emojis.TRAIT_RARE
            # if claim.trait_legendary:
            #     embed.description += Emojis.TRAIT_LEGENDARY
            
            embed.description += "\n"

            if claim.index % 10 == 0:
                embed.set_author(name=f"{inter.author.name}'s Harem", icon_url=inter.author.display_avatar.url)
                embeds.append(embed)
                embed = disnake.Embed(
                    description="",
                    color=disnake.Color.dark_red()
                )
        
        embed.set_author(name=f"{inter.author.name}'s Harem", icon_url=inter.author.display_avatar.url)
        embeds.append(embed)
        
        if len(embeds) > 1:
            waifu_page_view = WaifuPaginator(embeds, inter.author)
            message = await inter.edit_original_response(embed=embeds[0], view=waifu_page_view)
            waifu_page_view.message = message
            return
        return await inter.edit_original_response(embed=embeds[0])

    @commands.slash_command()
    async def managemywaifus(
        self,
        inter: disnake.ApplicationCommandInteraction,
        waifu: str = None
    ):
        """ View/edit your harem!
        
            Parameters
            ----------
            waifu: `str`
                Select only one of your waifus to manage.
        """
        await inter.response.defer()

        harem = await self.bot.mongo.fetch_harem(inter.author)

        if waifu:
            try:
                index = int(waifu.split(".")[0])
            except:
                return await inter.edit_original_response(
                    embed=ErrorEmbed(f"`{waifu}` is not a valid waifu!")
                )

            if index > len(harem) or index <= 0:
                return await inter.edit_original_response(
                    embed=ErrorEmbed(f"`{waifu}` does not have a valid index!")
                )
            harem = [harem.pop(index - 1)]
                
        if not harem:
            return await inter.edit_original_response(
                embed=ErrorEmbed(f"{inter.author.mention} your harem is empty!\n\nUse `/getmywaifu` to get started")
            )
        
        embeds: typing.List[disnake.Embed] = list()
        for claim in harem:
            w = await self.bot.mongo.fetch_waifu(claim.slug)
            embed = WaifuHaremEmbed(w, claim)
            embed.set_footer(text=claim.id)
            embeds.append(embed)

        waifu_war_event = await self.get_waifu_war_event(inter.guild)
        if waifu_war_event and waifu_war_event.status == disnake.GuildScheduledEventStatus.active:
            return await inter.edit_original_response(embed=embeds[0], view=None)
        
        view = WaifuMenuView(embeds, inter.author, harem)
        await view.initialize()
        message = await inter.edit_original_response(embed=embeds[0], view=view)
        view.message = message
        return

    @commands.slash_command()
    async def fusemywaifus(self, inter: disnake.ApplicationCommandInteraction):
        """Fuse lower-tier waifus to create a higher tier one!"""
        await inter.response.defer()
        
        harem = await self.bot.mongo.fetch_harem(inter.author)
        tier_dict = {tier:[] for tier in Tiers}
        for claim in harem:
            tier_dict[claim.tier].append(claim)
        
        fusion_count_dict = {}
        fusion_count_str = ""
        for fusion in Fusions:
            required_tier = Tiers(fusion.value)
            num_fusions = len(tier_dict[required_tier]) // 3
            fusion_count_dict[fusion] = num_fusions
            fusion_count_str += f"- {TIER_EMOJI_MAP[FUSION_TIER_MAP[fusion]]} `x{num_fusions}`\n"

        embed = disnake.Embed(
            title="Fusion Menu",
            description=f"Combine three (`3`) characters of the same tier to create a stronger one.\n"
                        f"The resulting character will be one tier higher than the characters you fused.\n\n"
                        f"__Available fusions:__\n{fusion_count_str}",
            color=disnake.Color.fuchsia()
        )
        view = FusionStageOneView(inter.author, fusion_count_dict)
        message = await inter.edit_original_response(
            embed=embed,
            view=view
        )
        view.message = message

        await view.wait()

        if not view.selected_fusion_type:
            return await inter.edit_original_response(view=None)

        required_tier = Tiers(view.selected_fusion_type.value)
        fusion_candidates = tier_dict[required_tier]

        if len(fusion_candidates) < 3:
            return await inter.edit_original_response(
                embed=ErrorEmbed(f"You don't have `3` {TIER_TITLE_MAP[required_tier]} characters available to fuse!"),
                view=None
            )

        embed = disnake.Embed(
            title=f"{TIER_TITLE_MAP[FUSION_TIER_MAP[view.selected_fusion_type]]} Fusion",
            description=f"Combine three (`3`) characters of the same tier to create a stronger one.\n",
            color=disnake.Color.fuchsia()
        )
        view = FusionStageTwoView(inter.author, fusion_candidates, view.selected_fusion_type)
        message = await inter.edit_original_response(
            embed=embed,
            view=view
        )
        view.message = message
        return

    ##*************************************************##
    ##********          AUTOCOMPLETES           *******##
    ##*************************************************##

    @managemywaifus.autocomplete("waifu")
    async def harem_autocomplete(
        self,
        inter: disnake.ApplicationCommandInteraction,
        user_input: str
    ) -> list:
        harem_size = await self.bot.mongo.fetch_harem_count(inter.author)
        if harem_size == 0:
            return [f"Your harem is empty!"]
        
        if user_input.isdigit() and int(user_input) <= harem_size:
            index = int(user_input)
            claim = await self.bot.mongo.fetch_claim_by_index(inter.author, index)
            waifu = await self.bot.mongo.fetch_waifu(claim.slug)
            formatted_name = f"{claim.index}. {waifu.name}"
            waifu_names = [formatted_name]
        else:
            harem = await self.bot.mongo.fetch_harem(inter.author)
            
            waifu_names = []
            for claim in harem:
                waifu = await self.bot.mongo.fetch_waifu(claim.slug)
                formatted_name = f"{claim.index}. {waifu.name} ({claim.skill_str_short})"
                waifu_names.append(formatted_name)
        
        return deque(waifu_names, maxlen=25)

    @buymywaifu.autocomplete("name")
    @waifudex.autocomplete("name")
    async def waifu_name_autocomplete(
        self,
        inter: disnake.ApplicationCommandInteraction,
        user_input: str
    ) -> list:
        if not user_input:
            user_input = "a"
        waifus = await self.bot.mongo.fetch_waifus_by_name(user_input)
        return deque([f"{waifu.name} [{waifu.series[0]}]" for waifu in waifus if len(waifu.series)], maxlen=25)

    @waifudex.autocomplete("series")
    async def waifu_series_autocomplete(
        self,
        inter: disnake.ApplicationCommandInteraction,
        user_input: str
    ) -> list:
        result = await self.bot.mongo.fetch_waifu_series()
        comp = re.compile(f"(?i)^{user_input}")
        return deque(filter(comp.match, result), maxlen=25)

    @waifudex.autocomplete("tag")
    async def waifu_tag_autocomplete(
        self,
        inter: disnake.ApplicationCommandInteraction,
        user_input: str
    ) -> list:
        result = await self.bot.mongo.fetch_waifu_tags()
        comp = re.compile(f"(?i)^{user_input}")
        return deque(filter(comp.match, result), maxlen=25)


def setup(bot: commands.Bot):
    bot.add_cog(Waifus(bot))
