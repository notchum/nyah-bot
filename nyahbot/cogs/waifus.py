import os
import re
import random
import typing
import asyncio
import datetime
from collections import deque

import disnake
import aiofiles
from PIL import Image
from rethinkdb import r # TODO move all reql to helpers
from loguru import logger
from disnake.ext import commands, tasks

from nyahbot.util.globals import conn, session # TODO move all reql to helpers, move api to apihelpers
from nyahbot.util.bracket import Bracket
from nyahbot.util.dataclasses import (
    Claim,
    Waifu,
    War,
)
from nyahbot.util.constants import (
    Emojis,
    Cooldowns,
    WaifuState,
    Money,
    Experience,
    MMR,
)
from nyahbot.util import (
    helpers,
    reql_helpers,
    traits,
    utilities,
)

from nyahbot.views.war_vote import WarVoteView
from nyahbot.views.waifu_dex import WaifuDexView
from nyahbot.views.waifu_duel import WaifuDuelView
from nyahbot.views.waifu_claim import WaifuClaimView
from nyahbot.views.waifu_skill import WaifuSkillView
from nyahbot.views.waifu_menu import WaifuMenuView
from nyahbot.views.waifu_paginator import WaifuPaginator

from nyahbot.views.waifu_minigames import WaifuSmashOrPassView, WaifuNameGuessView, WaifuBustGuessView

class Waifus(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.last_date = datetime.date.today()
        self.waifu_housekeeping.start()
        self.waifu_war_tasks = {}
        #!!! REMOVE
        self.scraper_index = 10000
        self.last_check_unranked = False
        #!!! REMOVE

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
        # events = await guild.fetch_scheduled_events(with_user_count=True)
        for event in guild.scheduled_events:
            if event.creator_id != self.bot.user.id:
                continue
            if event.name == "Waifu War":
                return event
        return None

    async def get_war_leaderboard(self, guild: disnake.Guild) -> disnake.Embed:
        """ Creates an embed containing current waifu scores leaderboard.

            Parameters
            ----------
            guild: `disnake.Guild`
                The guild to get the leaderboard of.
            
            Returns
            -------
            `disnake.Embed`
                An embed with the guild leaderboard.
        """
        score_mapping = {}
        rank_one_member_id = 0
        top_score = 0
        result = r.db("nyah") \
                    .table("players") \
                    .get_all(str(guild.id), index="guild_id") \
                    .run(conn)
        for user in result.items:
            if user["score"] > 0:
                score_mapping[guild.get_member(int(user["user_id"])).mention] = user["score"]
                if user["score"] > top_score:
                    top_score = user["score"]
                    rank_one_member_id = int(user["user_id"])
        nyah_guild = await reql_helpers.get_nyah_guild(guild)
        season_end = nyah_guild.timestamp_last_season_end + datetime.timedelta(days=nyah_guild.interval_season_days)
        score_mapping = {key: val for key, val in sorted(score_mapping.items(), key = lambda ele: ele[1], reverse = True)}
        embed = disnake.Embed(
            description=f"Season ends {utilities.get_dyn_time_relative(season_end)}",
            color=disnake.Color.random()
        )
        if not score_mapping:
            embed.title = "Waifu War Leaderboard"
            embed.description = "No one is on the scoreboard yet! Use `/getmywaifu` to get started!"
            return embed
        embed.add_field(
            name="Ranking",
            value="\n".join([f"`{i}` **{score}**" for i, score in enumerate(sorted(score_mapping.values(), reverse=True), start=1)])
        )
        embed.add_field(
            name="Member",
            value='\n'.join(score_mapping.keys())
        )
        rank_one_member = guild.get_member(rank_one_member_id)
        embed.set_author(name="Waifu War Leaderboard", icon_url=rank_one_member.display_avatar.url)
        return embed

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
            async with session.get(url="https://animechan.xyz/api/random") as response:
                if response.status != 200:
                    logger.error(f"Animechan API returned status '{response.status}'")
                    quote = ""
                else:
                    body = await response.json()
                    quote = f"_{body['quote']}_\n\- {body['character']}, \"{body['anime']}\""
        except:
            quote = ""
        
        # gather waifu war related info for guild
        nyah_guild = await reql_helpers.get_nyah_guild(guild)
        waifu_war_channel = await guild.fetch_channel(int(nyah_guild.waifu_war_channel_id))
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
                        f"- Starts: {utilities.get_dyn_time_long(start_time)}\n\n"
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
        nyah_guild = await reql_helpers.get_nyah_guild(event.guild)
        waifu_war_channel = await event.guild.fetch_channel(int(nyah_guild.waifu_war_channel_id))

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
        nyah_guild = await reql_helpers.get_nyah_guild(event.guild)
        waifu_war_channel = await event.guild.fetch_channel(int(nyah_guild.waifu_war_channel_id))

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
        board_embed = await self.get_war_leaderboard(event.guild)
        await waifu_war_channel.send(embeds=[embed, board_embed])

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
            
            user_active = r.db("waifus") \
                            .table("claims") \
                            .get_all([str(event.guild.id), str(user.id)], index="guild_user") \
                            .has_fields(["state", "index"]) \
                            .filter(
                                r.row["state"].eq(WaifuState.ACTIVE.name)
                            ) \
                            .count() \
                            .gt(0) \
                            .run(conn)
            if not user_active:
                continue
            
            if user.id not in event_user_ids:
                event_user_ids.append(user.id)
        
        return event_user_ids

    async def create_waifu_vs_img(self, red_waifu: Claim, blue_waifu: Claim) -> str:
        """ Create a waifu war round versus thumbnail image.

            Get ready to see the worst code ever written.

            Parameters
            ----------
            red_waifu: `Claim`
                The waifu to place on the red side of the versus image.
            blue_waifu: `Claim`
                The waifu to place on the red side of the versus image.

            Returns
            -------
            `str`
                The URL of the versus image.
        """
        UPPER_LEFT_INX = 0
        LOWER_RIGHT_INX = 1
        X_COORD_INX = 0
        Y_COORD_INX = 1

        def scale_image(img: Image.Image, scale_percent: float) -> Image.Image:
            """ Scales an image to `scale_percent`. """
            dim = (int(img.width * scale_percent), int(img.height * scale_percent))
            return img.resize(dim, resample=Image.Resampling.BICUBIC)

        def get_bounding_box_coords(img: Image.Image) -> list:
            """ Returns the coordinates of two boxes.  """
            return [
                # (x0, y0), (x1, y1)
                [(int(img.width*0.10), int(img.height*0.10)), (int(img.width*0.40), int(img.height*0.90))], # left side
                # (x2, y2), (x3, y3)
                [(int(img.width*0.60), int(img.height*0.10)), (int(img.width*0.90), int(img.height*0.90))]  # right side
            ]

        def center_place(img: Image.Image, bb_coords: list) -> tuple:
            """ Calculate upper-left coordinate to place an image in center of bounding box. """
            bb_width = bb_coords[LOWER_RIGHT_INX][X_COORD_INX] - bb_coords[UPPER_LEFT_INX][X_COORD_INX]
            bb_height = bb_coords[LOWER_RIGHT_INX][Y_COORD_INX] - bb_coords[UPPER_LEFT_INX][Y_COORD_INX]
            center_x = bb_coords[UPPER_LEFT_INX][X_COORD_INX] + bb_width//2
            center_y = bb_coords[UPPER_LEFT_INX][Y_COORD_INX] + bb_height//2

            return (center_x - img.width//2, center_y - img.height//2)

        # download background image
        if not os.path.exists("assets/images/vs.jpg"):
            bg_url = "https://external-content.duckduckgo.com/iu/?u=https%3A%2F%2Fstatic.vecteezy.com%2Fsystem%2Fresources%2Fpreviews%2F000%2F544%2F945%2Foriginal%2Fcomic-fighting-cartoon-background-blue-vs-red-vector-illustration-design.jpg&f=1&nofb=1&ipt=d7b1d0d9bb512e200148263e80ad893ee95f011cf44cfc20417a2da90f94642a&ipo=images"
            try:
                async with session.get(bg_url) as response:
                    if response.status != 200:
                        logger.error(f"Downloading image {bg_url} returned status code `{response.status}`")
                    async with aiofiles.open("assets/images/vs.jpg", mode="wb") as f:
                        await f.write(await response.read())
            except Exception as err:
                logger.error(f"Download image returned invalid data! {err}")

        # load background
        bg_img = Image.open("assets/images/vs.jpg")
        if (bg_img.mode != "RGBA"):
            bg_img = bg_img.convert("RGBA")

        # get initial bounding box coords [upper-left, lower-right]
        bb = get_bounding_box_coords(bg_img)

        # load 2 foreground images
        waifus: typing.Dict[str, typing.Dict[str, Image.Image | Claim | int]] = {
            "red": {
                "object": red_waifu,
                "image": None,
                "long_inx": None
            },
            "blue": {
                "object": blue_waifu,
                "image": None,
                "long_inx": None
            },
        }
        for waifu_color, waifu_value in waifus.items():
            # get image url
            image_url = r.db("waifus") \
                            .table("claims") \
                            .get(waifu_value["object"].id) \
                            .get_field("image_url") \
                            .run(conn)

            # download image
            try:
                image_path = f"assets/images/{waifu_value['object'].id}"
                if not os.path.exists(image_path):
                    async with session.get(image_url) as response:
                        if response.status != 200:
                            logger.error(f"Downloading image {image_url} returned status code `{response.status}`")
                        async with aiofiles.open(image_path, mode="wb") as f:
                            await f.write(await response.read())
                        logger.info(f"Downloaded image {image_path}")
            except Exception as err:
                logger.error(f"Downloading image returned invalid data! {err}")

            # load fg image
            load_img = Image.open(image_path)
            if (load_img.mode != "RGBA"):
                load_img = load_img.convert("RGBA")
            
            # save the image
            waifus[waifu_color]["image"] = load_img

            # determine longer side of each fg image
            if waifus[waifu_color]["image"].height > waifus[waifu_color]["image"].width:
                waifus[waifu_color]["long_inx"] = 1 # 1=height in .size
            else:
                waifus[waifu_color]["long_inx"] = 0 # 0=width in .size
        
        # determine the smaller image of the two using total pixels
        if (waifus["red"]["image"].width * waifus["red"]["image"].height) < (waifus["blue"]["image"].width * waifus["blue"]["image"].height):
            small_img_key = "red"
            large_img_key = "blue"
        else:
            small_img_key = "blue"
            large_img_key = "red"
        
        # get length of bb side-of-interest
        bb_long = bb[0][LOWER_RIGHT_INX][waifus[small_img_key]["long_inx"]] - bb[0][UPPER_LEFT_INX][waifus[small_img_key]["long_inx"]]
        if waifus[small_img_key]["image"].size[waifus[small_img_key]["long_inx"]] < bb_long: # if the smaller fg is smaller than the bb
            # scale the bg image
            scale_percent = waifus[small_img_key]["image"].size[waifus[small_img_key]["long_inx"]] / bb_long
            bg_img = scale_image(bg_img, scale_percent)

            # scale the bb to the new bg size
            bb = get_bounding_box_coords(bg_img)

            # scale the larger fg to the new bb size
            bb_long = bb[0][LOWER_RIGHT_INX][waifus[large_img_key]["long_inx"]] - bb[0][UPPER_LEFT_INX][waifus[large_img_key]["long_inx"]]
            scale_percent = bb_long / waifus[large_img_key]["image"].size[waifus[large_img_key]["long_inx"]]
            waifus[large_img_key]["image"] = scale_image(waifus[large_img_key]["image"], scale_percent)
        else: # if the bb is smaller than the smaller fg
            # scale both fg images to the bb
            for key, waifu_value in waifus.items():
                fg_img = waifu_value["image"]
                long_inx = waifu_value["long_inx"]
                bb_long = bb[0][LOWER_RIGHT_INX][long_inx] - bb[0][UPPER_LEFT_INX][long_inx]
                scale_percent = bb_long / fg_img.size[long_inx]
                waifus[key]["image"] = scale_image(fg_img, scale_percent)

        # final scaling and overlaying
        for bb_inx, (_, waifu_value) in enumerate(waifus.items()):
            fg_img = waifu_value["image"]
            # in case a fg image's width is too wide for the bb, scale once more
            bb_width = bb[bb_inx][LOWER_RIGHT_INX][X_COORD_INX] - bb[bb_inx][UPPER_LEFT_INX][X_COORD_INX]
            if fg_img.width > bb_width:
                scale_percent = bb_width / fg_img.width
                fg_img = scale_image(fg_img, scale_percent)

            # overlay fg images onto bg
            bg_img.paste(fg_img, box=center_place(fg_img, bb[bb_inx]), mask=fg_img)

        # save the image
        output_path = f"assets/images/{red_waifu.id}.vs.{blue_waifu.id}.png"
        bg_img.save(output_path)
        logger.info(f"Created image {output_path}")

        # upload the image to discord (free image hosting)
        image_host_channel = await self.bot.fetch_channel(1164613880538992760)
        image_host_msg = await image_host_channel.send(file=disnake.File(output_path))
        logger.info(f"Uploaded image {image_host_msg.attachments[0].url}")

        # return the URL of the image
        return image_host_msg.attachments[0].url

    async def find_duel_opponent(self, guild: disnake.Guild, user: disnake.User | disnake.Member) -> disnake.User:
        # Select user directly above you in score, else select user below
        rankings = r.db("nyah") \
                    .table("players") \
                    .get_all(str(guild.id), index="guild_id") \
                    .order_by(r.desc("score")) \
                    .pluck("user_id", "score", "level") \
                    .run(conn)

        user_data = next((u for u in rankings if u["user_id"] == str(user.id)), None)
    
        if user_data is None:
            # User not found in rankings, return None
            return None

        neighbors = []
        user_score = user_data["score"]
        total_players = len(rankings)

        # Determine the number of neighbors above and below the user based on total players
        num_neighbors = min(total_players - 1, 4)  # Max 4 neighbors (2 above, 2 below)

        for i, opponent in enumerate(rankings):
            if opponent["score"] == 0:
                continue
            if opponent["user_id"] != user_data["user_id"]:
                score_diff = user_score - opponent["score"]
                if i < num_neighbors or (total_players - i) <= num_neighbors:
                    neighbors.append(opponent)

        if not neighbors:
            # No suitable neighbors found within the level and score differences
            return self.bot.user

        # Calculate similarity scores for each neighbor
        similarity_scores = []
        for neighbor in neighbors:
            score_diff = abs(user_score - neighbor["score"]) // 10
            level_diff = abs(user_data["level"] - neighbor["level"])
            similarity_score = 1 / (1 + score_diff + level_diff)
            similarity_scores.append(similarity_score)
        
        # Check if there's a similarity score greater than 20%
        if max(similarity_scores) < 0.20:
            return self.bot.user

        # Select the opponent with the highest similarity score
        best_opponent = neighbors[similarity_scores.index(max(similarity_scores))]
        opponent = await guild.fetch_member(int(best_opponent["user_id"]))
        return opponent
        # If the selected opponent doesn't have any married waifus, face the bot
        # if opps_claim == None or opps_claim.state != WaifuState.ACTIVE.name:
        #     return self.bot.user #TODO implement via a reql_helper

    async def end_waifu_war_season(self, guild: disnake.Guild) -> None:
        """ Resets all user's waifus, scores, and coins in a given guild
            if the guild's reset interval is met.

            Parameters
            ----------
            guild: `disnake.Guild`
                The guild to end the season in.
        """
        nyah_guild = await reql_helpers.get_nyah_guild(guild)
        
        season_end_datetime = nyah_guild.timestamp_last_season_end + datetime.timedelta(days=nyah_guild.interval_season_days)
        if datetime.datetime.now(datetime.timezone.utc) < season_end_datetime:
            return
        
        return logger.debug(f"{guild.name}'s WAIFU WAR SEASON SHOULD END")
        
        waifu_war_channel = await guild.fetch_channel(int(nyah_guild.waifu_war_channel_id))
        ww_role = await self.get_waifu_war_role(guild)
        leaderboard_embed = await self.get_war_leaderboard(guild)
        msg_embed = disnake.Embed(
            title="⚔️ WAIFU WARS SEASON END ⚔️",
            color=disnake.Color.random(),
            description=f"{guild.name}'s Waifu War season is over!\n"
                        f"__All scores will be reset to 0!__"
                        f"__All harems will be fully reset!__",
        )
        
        await waifu_war_channel.send(
            content=ww_role.mention,
            embeds=[msg_embed, leaderboard_embed],
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
        nyah_guild = await reql_helpers.get_nyah_guild(guild)
        waifu_war_channel = await guild.fetch_channel(int(nyah_guild.waifu_war_channel_id))
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
            nyah_guild = await reql_helpers.get_nyah_guild(guild)
            waifu_war_channel = await guild.fetch_channel(int(nyah_guild.waifu_war_channel_id))
            ww_role = await self.get_waifu_war_role(guild)
            
            # send a message to alert users
            embed = disnake.Embed(
                title="⚔️ WAIFU WAR REMINDER ⚔️",
                description=f"- {ww_role.mention} __**mark yourself as interested**__ to this event to enter this war!\n"
                            f"- The Waifu War is starting {utilities.get_dyn_time_relative(waifu_war_event.scheduled_start_time)}!",
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
        async for member in guild.fetch_members():
            member_active = r.db("waifus") \
                                .table("claims") \
                                .get_all([str(guild.id), str(member.id)], index="guild_user") \
                                .has_fields(["state", "index"]) \
                                .count() \
                                .gt(0) \
                                .run(conn)
            if member_active and not member.get_role(ww_role.id):
                # Add user to role if not
                await member.add_roles(ww_role)
            elif not member_active and member.get_role(ww_role.id):
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

    @tasks.loop(time=datetime.time(hour=6, minute=0)) #!!! i think this is broken
    async def waifu_war_creation(self):
        """ Creates a Waifu War scheduled event in a guild each day. """
        for guild in self.bot.guilds:
            waifu_war_event = await self.get_waifu_war_event(guild)
            if waifu_war_event:
                return
            nyah_guild = await reql_helpers.get_nyah_guild(guild)
            start_time = datetime.datetime.combine(
                date=disnake.utils.utcnow().date(),
                time=datetime.time(nyah_guild.waifu_war_hour, 0), #??? should this be hour in UTC? it is MDT now...
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
            war_uuid = r.uuid().run(conn)
            war = War(
                id=war_uuid,
                event_id=str(waifu_war_event.id),
                guild_id=str(guild.id),
                timestamp_start=datetime.datetime.now(datetime.timezone.utc),
                timestamp_end=None
            )
            r.db("wars").table("core").insert(war.__dict__).run(conn)

            # Create the initial bracket
            bracket = Bracket(war_uuid)
            rankings = await reql_helpers.get_nyah_player_guild(guild)
            event_user_ids = await self.get_waifu_war_event_users(waifu_war_event)
            
            # Add users to the bracket if they are part of the event
            rank = 1
            for user_info in rankings:
                user = self.bot.get_user(int(user_info.user_id))
                
                # If they aren't in the event, then go next
                if user.id not in event_user_ids:
                    continue
                # If they don't have any married waifus, then go next
                if await reql_helpers.get_harem_married_size(guild, user) == 0:
                    continue
                
                # Add to bracket
                bracket.add_team(
                    name=user.name,
                    user_id=user_info.user_id,
                    ranking=rank
                )
                rank += 1
            bracket.create_bracket()
        
        # Get the waifu war channel
        nyah_guild = await reql_helpers.get_nyah_guild(guild)
        waifu_war_channel = await guild.fetch_channel(int(nyah_guild.waifu_war_channel_id))

        # Get the war ID
        war_uuid = r.db("wars") \
                    .table("core") \
                    .filter(
                        r.and_(
                            r.row["guild_id"].eq(str(guild.id)),
                            r.row["timestamp_start"],
                            r.not_(r.row["timestamp_end"])
                        )
                    ) \
                    .nth(0) \
                    .get_field("id") \
                    .run(conn)

        # Create a bracket object to help us
        bracket = Bracket(war_uuid)

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
            async with session.get(url="https://nekos.best/api/v2/thumbsup") as response:
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
                has_waifu = r.db("waifus") \
                                .table("claims") \
                                .get_all([str(guild.id), user_id], index="guild_user") \
                                .has_fields(["state", "index"]) \
                                .filter(
                                    r.row["state"].eq(WaifuState.ACTIVE.name)
                                ) \
                                .count() \
                                .gt(0) \
                                .run(conn)
                
                if not has_waifu:
                    # If the user is out of waifus, then they lose the match
                    bracket.set_match_winner(current_match, opponent_user_id)
                else:
                    # If the user still has active waifus then get a random one
                    harem_waifu = r.db("waifus") \
                                    .table("claims") \
                                    .get_all([str(guild.id), user_id], index="guild_user") \
                                    .has_fields(["state", "index"]) \
                                    .filter(
                                        r.row["state"].eq(WaifuState.ACTIVE.name)
                                    ) \
                                    .sample(1) \
                                    .nth(0) \
                                    .run(conn)
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
            vs_img_url = await self.create_waifu_vs_img(random_waifu_red, random_waifu_blue)
            
            # Create the battle embed
            ends_at = disnake.utils.utcnow() + datetime.timedelta(minutes=voting_time_min)
            red_name = r.db("waifus").table("core").get(random_waifu_red.slug).get_field("name").run(conn)
            blue_name = r.db("waifus").table("core").get(random_waifu_blue.slug).get_field("name").run(conn)
            battle_embed = disnake.Embed(
                title=f"{match_title}  •  Battle {current_battle.number}",
                description=f"**__{red_name}__** vs. **__{blue_name}__**\n"
                            f"Voting ends: {utilities.get_dyn_time_relative(ends_at)}",
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
            result = r.db("waifus") \
                        .table("claims") \
                        .get(vote_info["loser"]["id"]) \
                        .run(conn)
            losing_claim = Claim(**result)
            losing_claim.index = None
            losing_claim.state = WaifuState.NULL.value
            losing_user = self.bot.get_user(int(losing_claim.user_id))
            r.db("waifus") \
                .table("claims") \
                .get(losing_claim.id) \
                .update(losing_claim.__dict__) \
                .run(conn)
            
            # Reindex the losing user's waifus
            r.db("waifus") \
                .table("claims") \
                .get_all([str(guild.id), losing_claim.user_id], index="guild_user") \
                .has_fields(["state", "index"]) \
                .filter(
                    r.or_(
                        r.row["state"].ne(WaifuState.NULL.name),
                        r.row["state"].ne(WaifuState.SOLD.name),
                    )
                ) \
                .update({
                    "index": r.row["index"] - 1
                }) \
                .run(conn)
            
            # Get the user's waifu that won
            result = r.db("waifus") \
                        .table("claims") \
                        .get(vote_info["winner"]["id"]) \
                        .run(conn)
            winning_claim = Claim(**result)
            winning_user = self.bot.get_user(int(winning_claim.user_id))
            result = r.db("waifus") \
                        .table("core") \
                        .get(winning_claim.slug) \
                        .run(conn)
            waifu = Waifu(**result)

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
            has_waifu = r.db("waifus") \
                            .table("claims") \
                            .get_all([str(guild.id), str(losing_user.id)], index="guild_user") \
                            .has_fields(["state", "index"]) \
                            .filter(
                                r.row["state"].eq(WaifuState.ACTIVE.name)
                            ) \
                            .count() \
                            .gt(0) \
                            .run(conn)
            
            if not has_waifu:
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
                await helpers.add_user_xp(user, Experience.WAR_ROUND.value)

            # War is over if this round was the last
            if bracket.last_round(current_round):
                await self.end_waifu_war_event(waifu_war_event)

                # Put winner's waifus on cooldown
                r.db("waifus") \
                    .table("claims") \
                    .get_all([str(guild.id), winner_id], index="guild_user") \
                    .has_fields(["state", "index"]) \
                    .filter(
                        r.row["state"].eq(WaifuState.ACTIVE.name)
                    ) \
                    .update({
                        "state": WaifuState.COOLDOWN.name,
                        "timestamp_cooldown": disnake.utils.utcnow(),
                    }) \
                    .run(conn)
                
                # Give the winner and runner-up awards
                for user_id in bracket.get_round_participant_ids(current_round):
                    user = await guild.fetch_member(int(user_id))
                    if user_id == winner_id:
                        await helpers.add_user_money(user, Money.WAR_FIRST.value)
                    else:
                        await helpers.add_user_money(user, Money.WAR_SECOND.value)
                
                # Reindex all participant's waifus
                for participant in bracket.participants:
                    if participant.user_id == "BYE":
                        continue
                    user = await guild.fetch_member(int(participant.user_id))
                    await helpers.reindex_guild_user_harem(guild, user)

    ##*************************************************##
    ##********             COMMANDS             *******##
    ##*************************************************##

    @commands.slash_command(default_member_permissions=disnake.Permissions(administrator=True))
    async def waifuadmin(self, inter: disnake.ApplicationCommandInteraction):
        """ Top-level command group for configuring waifus for guilds. """
        pass

    @waifuadmin.sub_command()
    async def setup(self, inter: disnake.ApplicationCommandInteraction):
        """ Configure settings for this server. """
        await inter.response.send_message("in progress")

    @waifuadmin.sub_command()
    async def create_waifu_war(
        self,
        inter: disnake.ApplicationCommandInteraction,
        time_delta_min: int
    ):
        """ Create a Waifu War event manually.
        
            Parameters
            ----------
            time_delta_min: `int`
                How many minutes in the future to schedule for.
        """
        await inter.response.defer(ephemeral=True)
        waifu_war_event = await self.get_waifu_war_event(inter.guild)
        if waifu_war_event:
            return await inter.edit_original_response(
                embed=utilities.get_error_embed("A waifu war event already exists in this server!")
            )
        start_time = disnake.utils.utcnow() + datetime.timedelta(minutes=time_delta_min)
        await self.schedule_waifu_war_event(inter.guild, start_time)
        return await inter.edit_original_response(
            embed=utilities.get_success_embed(f"Scheduled event for {utilities.get_dyn_time_long(start_time)}")
        )

    @waifuadmin.sub_command()
    async def set_user_attributes(
        self,
        inter: disnake.ApplicationCommandInteraction,
        user: disnake.User,
        level: int = None,
        xp: int = None,
        mmr: int = None,
        money: int = None
    ):
        if level == None and xp == None and mmr == None and money == None:
            return await inter.response.send_message(
                embed=utilities.get_error_embed("No attributes provided!"),
                ephemeral=True
            )
        
        nyah_player = await reql_helpers.get_nyah_player(user)
        if level != None: nyah_player.level = level
        if xp != None: nyah_player.xp = xp
        if mmr != None: nyah_player.score = mmr
        if money != None: nyah_player.money = money
        await reql_helpers.set_nyah_player(nyah_player)

        return await inter.response.send_message(
            embed=utilities.get_success_embed("Updated user attributes!"),
            ephemeral=True
        )

    @waifuadmin.sub_command()
    async def reset_user_cooldown(
        self,
        inter: disnake.ApplicationCommandInteraction,
        user: disnake.User = None,
        cooldown: str = commands.Param(choices=["timestamp_last_claim",
                                                "timestamp_last_duel",
                                                "timestamp_last_minigame"])
    ):
        """ Resets a chosen cooldown for a user or for all guild members.

            Parameters
            ----------
            user: `disnake.User`
                The user to reset waifu availability for. (Default: All guild members)
            cooldown: `str`
                The cooldown field name to reset.
        """
        if user:
            r.db("nyah") \
                .table("players") \
                .get_all([str(inter.guild.id), str(user.id)], index="guild_user") \
                .update({
                    cooldown: None
                }) \
                .run(conn)
            logger.success(f"{inter.guild.name}[{inter.guild.id}] | Reset `{cooldown}` for {user.name}#{user.discriminator}[{user.id}]!")
            return await inter.response.send_message(
                embed=utilities.get_success_embed(f"Reset `{cooldown}` for {user.name}#{user.discriminator}[{user.id}]!"),
                ephemeral=True
            )
        else:
            r.db("nyah") \
                .table("players") \
                .get_all(str(inter.guild.id), index="guild_id") \
                .update({
                    cooldown: None
                }) \
                .run(conn)
            logger.success(f"{inter.guild.name}[{inter.guild.id}] | Reset `{cooldown}` for all members!")
            return await inter.response.send_message(
                embed=utilities.get_success_embed(f"Reset `{cooldown}` for all members!"),
                ephemeral=True
            )


    @commands.slash_command()
    async def leaderboard(self, inter: disnake.ApplicationCommandInteraction):
        """ View the Waifu Wars leaderboard! """
        embed = await self.get_war_leaderboard(inter.guild)
        return await inter.response.send_message(embed=embed)

    @commands.slash_command()
    async def profile(self, inter: disnake.ApplicationCommandInteraction):
        """ View your level, XP, balance and cooldowns. """
        await inter.response.defer()
        now = disnake.utils.utcnow()

        nyah_player = await reql_helpers.get_nyah_player(inter.author)
        
        # Claim cooldowns
        if await helpers.user_is_on_cooldown(inter.author, Cooldowns.CLAIM):
            next_claim_at = await helpers.user_cooldown_expiration_time(inter.author, Cooldowns.CLAIM)
            if now < next_claim_at:
                fmt_claim_times = f"❄️ {utilities.get_dyn_time_relative(next_claim_at)} ({utilities.get_dyn_time_short(next_claim_at)})"
            else:
                fmt_claim_times = "🟢 **Ready**"
        else:
            fmt_claim_times = "🟢 **Ready**"
        
        # Duel cooldowns
        if await helpers.user_is_on_cooldown(inter.author, Cooldowns.DUEL):
            next_duel_at = await helpers.user_cooldown_expiration_time(inter.author, Cooldowns.DUEL)
            if now < next_claim_at:
                fmt_duel_times = f"❄️ {utilities.get_dyn_time_relative(next_duel_at)} ({utilities.get_dyn_time_short(next_duel_at)})"
            else:
                fmt_duel_times = "🟢 **Ready**"
        else:
            fmt_duel_times = "🟢 **Ready**"
        
        # Minigame cooldowns
        if await helpers.user_is_on_cooldown(inter.author, Cooldowns.MINIGAME):
            next_minigame_at = await helpers.user_cooldown_expiration_time(inter.author, Cooldowns.MINIGAME)
            if now < next_claim_at:
                fmt_minigame_times = f"❄️ {utilities.get_dyn_time_relative(next_minigame_at)} ({utilities.get_dyn_time_short(next_minigame_at)})"
            else:
                fmt_minigame_times = "🟢 **Ready**"
        else:
            fmt_minigame_times = "🟢 **Ready**"

        embed = disnake.Embed(
            color=disnake.Color.random(),
        ) \
        .set_author(name=f"{inter.author.name}'s Profile", icon_url=inter.author.display_avatar.url) \
        .add_field(name="Level", value=f"{nyah_player.level}") \
        .add_field(name="XP", value=f"{nyah_player.xp}/{helpers.calculate_accumulated_xp(nyah_player.level + 1)}") \
        .add_field(name=f"Balance", value=f"`{nyah_player.money:,}` {Emojis.COINS}") \
        .add_field(name="Cooldowns:", value="", inline=False) \
        .add_field(name=f"{Emojis.CLAIM} Drop", value=fmt_claim_times, inline=False) \
        .add_field(name="🎮 Minigame", value=fmt_minigame_times, inline=False) \
        .add_field(name="🎌 Duel", value=fmt_duel_times, inline=False)
        
        return await inter.edit_original_response(embed=embed)

    @commands.slash_command()
    async def minigame(self, inter: disnake.ApplicationCommandInteraction):
        """ Play a random waifu minigame for money! """
        # Check if user's duel on cooldown
        if await helpers.user_is_on_cooldown(inter.author, Cooldowns.MINIGAME):
            next_minigame_at = await helpers.user_cooldown_expiration_time(inter.author, Cooldowns.MINIGAME)
            return await inter.response.send_message(
                content=f"{inter.author.mention} you are on a minigame cooldown now.\n"
                        f"Try again {utilities.get_dyn_time_relative(next_minigame_at)} ({utilities.get_dyn_time_short(next_minigame_at)})",
                ephemeral=True
            )

        await inter.response.defer()
        
        # Select the type of minigame this will be
        minigame = random.choice(["guess_name", "guess_bust", "smash_or_pass"])

        # Get a random waifu
        result = r.db("waifus") \
                    .table("core") \
                    .has_fields("popularity_rank") \
                    .order_by("popularity_rank") \
                    .limit(500) \
                    .sample(1) \
                    .nth(0) \
                    .run(conn)
        waifu = Waifu(**result)

        if minigame == "guess_name":
            answer = waifu.name

            embed = disnake.Embed(
                title="WHO'S THAT WAIFU",
                description=f"{inter.author.mention} who is this character?",
                color=disnake.Color.teal()
            ).set_image(waifu.image_url)
            minigame_view = WaifuNameGuessView(inter.author, answer)

            correct_description = f"- Yes! This is **__{answer}__**, good job\n"
            wrong_description = f"- No, this is **__{answer}__** :(\n"
        
        elif minigame == "guess_bust":
            result = r.db("waifus") \
                        .table("core") \
                        .has_fields(["popularity_rank", "bust"]) \
                        .order_by("popularity_rank") \
                        .limit(500) \
                        .sample(1) \
                        .nth(0) \
                        .run(conn)
            waifu = Waifu(**result)
            answer = waifu.bust

            embed = disnake.Embed(
                title="GUESS HER BUST SIZE",
                description=f"{inter.author.mention} what is **__{waifu.name}'s__** bust measurement?",
                color=disnake.Color.teal()
            ).set_image(waifu.image_url)
            minigame_view = WaifuBustGuessView(inter.author, answer)

            correct_description = f"- **__{waifu.name}'s__** bust is {answer}, good job\n"
            wrong_description = f"- Sorry, **__{waifu.name}'s__** tits are {answer} :(\n"

        elif minigame == "smash_or_pass":
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
        await inter.edit_original_response(embed=embed, view=minigame_view)

        # Set timestamp in db
        nyah_player = await reql_helpers.get_nyah_player(inter.author)
        nyah_player.timestamp_last_minigame = disnake.utils.utcnow()
        await reql_helpers.set_nyah_player(nyah_player)

        # Wait for the user to answer
        await minigame_view.wait()

        # Create the embed with the result of the user's answer
        if minigame_view.author_won:
            result_embed = disnake.Embed(
                title="Correct!",
                description=correct_description + 
                            f"- You earned `{Money.MINIGAME_WIN.value}` {Emojis.COINS} "
                            f"and `{Experience.MINIGAME_WIN.value}` XP",
                color=disnake.Color.green(),
            )
            logger.debug(f"{inter.author.name} beat minigame '{minigame}'")
            await helpers.add_user_money(inter.author, Money.MINIGAME_WIN.value)
            await helpers.add_user_xp(inter.author, Experience.MINIGAME_WIN.value, inter.channel)
        else:
            result_embed = disnake.Embed(
                title="Wrong!",
                description=wrong_description +
                            f"- You earned `{Money.MINIGAME_LOSS.value}` {Emojis.COINS} "
                            f"and `{Experience.MINIGAME_LOSS.value}` XP",
                color=disnake.Color.red(),
            )
            logger.debug(f"{inter.author.name} lost minigame '{minigame}'")
            await helpers.add_user_money(inter.author, Money.MINIGAME_LOSS.value)
            await helpers.add_user_xp(inter.author, Experience.MINIGAME_LOSS.value, inter.channel)

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
            n_total_claims = r.db("waifus") \
                                .table("claims") \
                                .get_all(str(inter.author.id), index="user_id") \
                                .count() \
                                .run(conn)
            embed = disnake.Embed(
                description=f"You've gotten {n_total_claims} waifus!",
                color=disnake.Color.teal()
            ).set_author(name=f"{inter.author.name}'s waifudex", icon_url=inter.author.display_avatar.url)

            return await inter.edit_original_response(embed=embed)

        # Return all characters from that series
        elif not name and series and not tag and not birthday:
            result = r.db("waifus") \
                        .table("core") \
                        .filter(
                            r.row["series"].contains(series)
                        ) \
                        .order_by("name") \
                        .run(conn)
        
        # Return all characters that have this tag
        elif not name and not series and tag and not birthday:
            result = r.db("waifus") \
                        .table("core") \
                        .filter(
                            r.row["tags"].contains(tag)
                        ) \
                        .order_by("name") \
                        .run(conn)
        
        # Return characters that were born today
        elif not name and not series and not tag and birthday:
            result = r.db("waifus") \
                        .table("core") \
                        .filter(
                            r.and_(
                                r.row["birthday_month"].eq(r.now().month()),
                                r.row["birthday_day"].eq(r.now().day())
                            )
                        ) \
                        .order_by("name") \
                        .run(conn)

        # Return characters with the same name
        elif name and not series and not tag and not birthday:
            if re.search(r"\[.*\]", name):
                match = re.match(r"^(.*?)\s*\[(.*?)\]$", name)
                name = match.group(1).strip()
                series = match.group(2).strip()

                result = r.db("waifus") \
                            .table("core") \
                            .get_all(name, index="name") \
                            .filter(
                                r.row["series"].contains(series)
                            ) \
                            .run(conn)
            else:
                series = ""
                result = r.db("waifus") \
                            .table("core") \
                            .filter(
                                r.row["name"].match(f"(?i){name}")
                            ) \
                            .order_by("name") \
                            .run(conn)

        if not result:
            return await inter.edit_original_response(
                embed=utilities.get_error_embed(f"Couldn't find any waifus that match:\nname={name}\nseries={series}\ntag={tag}\nbirthday={birthday}")
            )
        
        embeds = list()
        for doc in result:
            waifu = Waifu(**doc)
            embed = await helpers.get_waifu_core_embed(waifu)
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
        nyah_player = await reql_helpers.get_nyah_player(inter.author)
        
        # Check if user's waifu is available to claim
        if await helpers.user_is_on_cooldown(inter.author, Cooldowns.CLAIM):
            next_claim_at = await helpers.user_cooldown_expiration_time(inter.author, Cooldowns.CLAIM)
            return await inter.response.send_message(
                content=f"Whoa now! That's too many waifus right now - this isn't a hanime, big guy.\n"
                        f"Try again {utilities.get_dyn_time_relative(next_claim_at)} ({utilities.get_dyn_time_short(next_claim_at)})",
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
        
        # Get a random waifu from the db with wishlist chance
        if nyah_player.wishlist:
            wishlist_slug = random.choice(nyah_player.wishlist)
            wishlist_chance = 0.05 * nyah_player.wishlist.count(wishlist_slug)
            if random.random() < wishlist_chance:
                result = r.db("waifus") \
                            .table("core") \
                            .get(wishlist_slug) \
                            .run(conn)
                result["popularity_rank"] = random.randint(1000, 5000) #!!! REMOVE
                result["like_rank"] = random.randint(1000, 5000) #!!! REMOVE
                result["trash_rank"] = random.randint(1000, 5000) #!!! REMOVE
                nyah_player.wishlist = [item for item in nyah_player.wishlist if item != wishlist_slug]
            else:
                result = r.db("waifus") \
                            .table("core") \
                            .has_fields(["popularity_rank", "like_rank", "trash_rank"]) \
                            .filter(
                                r.row["husbando"].eq(False)
                            ) \
                            .sample(1) \
                            .nth(0) \
                            .run(conn)
        else:
            result = r.db("waifus") \
                        .table("core") \
                        .has_fields(["popularity_rank", "like_rank", "trash_rank"]) \
                        .filter(
                            r.row["husbando"].eq(False)
                        ) \
                        .sample(1) \
                        .nth(0) \
                        .run(conn)
        new_waifu = Waifu(**result)

        # Roll traits
        trait_dropper = traits.CharacterTraitDropper(nyah_player.level)
        rolled_traits = trait_dropper.roll_all_traits()

        # Normalize each ranking, adding some various permutations to a list
        num_ranks = r.db("waifus").table("core").count().run(conn)
        normalized_popularity_rank = 1 - (new_waifu.popularity_rank - 1) / (num_ranks - 1)
        normalized_like_rank = 1 - (new_waifu.like_rank - 1) / (num_ranks - 1)
        normalized_trash_rank = (new_waifu.trash_rank - 1) / (num_ranks - 1)
        base_normalizations = [
            normalized_like_rank - normalized_trash_rank,
            normalized_popularity_rank - normalized_trash_rank,
            normalized_popularity_rank + normalized_like_rank - normalized_trash_rank,
        ]

        # Calculate base stats
        attack = max(0, min(100, int(round((random.choice(base_normalizations) + random.uniform(-0.2, 0.2)) * 100))))
        defense = max(0, min(100, int(round((random.choice(base_normalizations) + random.uniform(-0.2, 0.2)) * 100))))
        health = max(0, min(100, int(round((random.choice(base_normalizations) + random.uniform(-0.2, 0.2)) * 100))))
        speed = max(0, min(100, int(round((random.choice(base_normalizations) + random.uniform(-0.2, 0.2)) * 100))))
        magic = max(0, min(100, int(round((random.choice(base_normalizations) + random.uniform(-0.2, 0.2)) * 100))))
        
        # Calculate price
        normalized_total_stats = ((attack + defense + health + speed + magic) / 500)
        popularity_price = int(round(normalized_popularity_rank * 1000))
        stats_price = int(round(0.2 * normalized_total_stats * 100))
        traits_price = sum([t.get_trait_value() for t in rolled_traits.values() if t != None])
        price = max(100, popularity_price + stats_price + traits_price)

        # TODO re-assess how to best assign base stats, here is just completely random
        # TODO but i left price using stats calculated via waifu rank, since that seemed fine
        attack = random.randint(0, 100)
        defense = random.randint(0, 100)
        health = random.randint(0, 100)
        speed = random.randint(0, 100)
        magic = random.randint(0, 100)

        # Generate the claim object
        new_waifu_uuid = r.uuid().run(conn)
        index = await reql_helpers.get_harem_size(inter.guild, inter.author)
        claim = Claim(
            id=new_waifu_uuid,
            slug=new_waifu.slug,
            guild_id=None,
            channel_id=None,
            message_id=None,
            user_id=str(inter.author.id),
            jump_url=None,
            image_url=new_waifu.image_url,
            cached_images_urls=None,
            state=WaifuState.INACTIVE.name,
            index=index,
            price=price,
            attack=attack,
            defense=defense,
            health=health,
            speed=speed,
            magic=magic,
            attack_mod=0,
            defense_mod=0,
            health_mod=0,
            speed_mod=0,
            magic_mod=0,
            trait_common=rolled_traits["common"].name if rolled_traits["common"] else None,
            trait_uncommon=rolled_traits["uncommon"].name if rolled_traits["uncommon"] else None,
            trait_rare=rolled_traits["rare"].name if rolled_traits["rare"] else None,
            trait_legendary=rolled_traits["legendary"].name if rolled_traits["legendary"] else None,
            timestamp=None,
            timestamp_cooldown=None
        )
        logger.info(f"{inter.guild.name}[{inter.guild.id}] | "
                    f"{inter.channel.name}[{inter.channel.id}] | "
                    f"{inter.author}[{inter.author.id}] | "
                    f"Claimed {new_waifu.slug}[{new_waifu_uuid}]")

        # Apply trait modifiers
        if claim.trait_common:
            trait = traits.CharacterTraitsCommon.get_trait_by_name(claim.trait_common)
            trait.apply_modifiers(claim)
        if claim.trait_uncommon:
            trait = traits.CharacterTraitsUncommon.get_trait_by_name(claim.trait_uncommon)
            trait.apply_modifiers(claim)
        if claim.trait_rare:
            trait = traits.CharacterTraitsRare.get_trait_by_name(claim.trait_rare)
            trait.apply_modifiers(claim)
        if claim.trait_legendary:
            trait = traits.CharacterTraitsLegendary.get_trait_by_name(claim.trait_legendary)
            trait.apply_modifiers(claim)

        # Send the waifu
        waifu_embed = await helpers.get_waifu_claim_embed(claim, inter.author)
        claim_view = WaifuClaimView(claim, inter.author)
        message = await inter.edit_original_response(
            content=inter.author.mention,
            embed=waifu_embed,
            view=claim_view
        )
        claim_view.message = message

        # Insert claim, update harem in db
        claim.guild_id=str(message.guild.id)
        claim.channel_id=str(message.channel.id)
        claim.message_id=str(message.id)
        claim.jump_url=message.jump_url
        claim.timestamp=message.created_at
        r.db("waifus").table("claims").insert(claim.__dict__).run(conn)
        await helpers.reindex_guild_user_harem(inter.guild, inter.author)

        # Update user info in db
        nyah_player.timestamp_last_claim = disnake.utils.utcnow()
        await reql_helpers.set_nyah_player(nyah_player)
        await helpers.add_user_xp(inter.author, Experience.CLAIM.value, inter.channel)
        return

    @commands.slash_command()
    async def listmywaifus(self, inter: disnake.ApplicationCommandInteraction):
        """ List your harem! """
        await inter.response.defer()

        harem = await reql_helpers.get_harem(inter.guild, inter.author)
        
        if not harem:
            return await inter.edit_original_response(
                embed=utilities.get_error_embed(f"{inter.author.mention} your harem is empty!\n\nUse `/getmywaifu` to get started")
            )
        
        embed = disnake.Embed(
            description="",
            color=disnake.Color.dark_red()
        )
        embeds = []
        for i, claim in enumerate(harem, 1):
            waifu = await reql_helpers.get_waifu_core(claim.slug)
            if i == 1:
                embed.set_thumbnail(url=claim.image_url)
            
            embed.description += f"`{i}` "
            
            if claim.state == WaifuState.ACTIVE.name:
                embed.description += Emojis.STATE_MARRIED
            elif claim.state == WaifuState.COOLDOWN.name:
                embed.description += Emojis.STATE_COOLDOWN
            elif claim.state == WaifuState.INACTIVE.name:
                embed.description += Emojis.STATE_UNMARRIED
            
            embed.description += f" {waifu.name} ({claim.stats_str()}) "
            
            if claim.trait_common:
                embed.description += Emojis.TRAIT_COMMON
            if claim.trait_uncommon:
                embed.description += Emojis.TRAIT_UNCOMMON
            if claim.trait_rare:
                embed.description += Emojis.TRAIT_RARE
            if claim.trait_legendary:
                embed.description += Emojis.TRAIT_LEGENDARY
            
            embed.description += "\n"

            if i % 10 == 0:
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

        harem = await reql_helpers.get_harem(inter.guild, inter.author)

        if waifu:
            try:
                index = int(waifu.split(".")[0])
            except:
                return await inter.edit_original_response(
                    embed=utilities.get_error_embed(f"`{waifu}` is not a valid waifu!")
                )

            if index > len(harem) or index <= 0:
                return await inter.edit_original_response(
                    embed=utilities.get_error_embed(f"`{waifu}` does not have a valid index!")
                )
            harem = [harem.pop(index - 1)]
                
        if not harem:
            return await inter.edit_original_response(
                embed=utilities.get_error_embed(f"{inter.author.mention} your harem is empty!\n\nUse `/getmywaifu` to get started")
            )
        
        embeds: typing.List[disnake.Embed] = list()
        for h in harem:
            harem_waifu = Claim(**dict(h))
            embed = await helpers.get_waifu_harem_embed(harem_waifu)
            embed.set_footer(text=harem_waifu.id)
            embeds.append(embed)

        waifu_war_event = await self.get_waifu_war_event(inter.guild)
        if waifu_war_event and waifu_war_event.status == disnake.GuildScheduledEventStatus.active:
            return await inter.edit_original_response(embed=embeds[0], view=None)
        
        view = WaifuMenuView(embeds, inter.author)
        message = await inter.edit_original_response(embed=embeds[0], view=view)
        view.message = message
        return

    @commands.slash_command()
    async def skillmywaifu(
        self,
        inter: disnake.ApplicationCommandInteraction,
        waifu: str
    ):
        """ View/modify your waifu's skills!

            Parameters
            ----------
            waifu: `str`
                The waifu to skill.
        """
        await inter.response.defer()
        
        # Parse string input for waifu select
        index = int(waifu.split(".")[0])

        # Get claim from db
        claim = await reql_helpers.get_waifu_claim_index(inter.author, index)

        # Get waifu
        waifu = await reql_helpers.get_waifu_core(claim.slug)

        # Send message with waifu and new skill points
        embed = await helpers.get_waifu_skills_embed(claim)
        embed.description = f"Reroll **__{waifu.name}'s__** skills for `{Money.SKILL_COST.value:,}` {Emojis.COINS}?"
        skill_view = WaifuSkillView(claim, inter.author)
        message = await inter.edit_original_response(embed=embed, view=skill_view)
        skill_view.message = message
        return

    @commands.slash_command()
    async def duelmywaifu(
        self, 
        inter: disnake.ApplicationCommandInteraction,
        waifu: str
    ):
        """ Use your best waifu to duel other user's waifus! """
        def calculate_total_score(claim: Claim) -> float:
            base_score = claim.attack * 0.4 + claim.defense * 0.35 + claim.health * 0.36 + claim.speed * 0.39 + claim.magic * 0.38
            random_modifier = random.uniform(0.6, 1.2)
            return base_score * random_modifier
        
        def generate_bot_claim(total_sp: int) -> Claim:
            result = r.db("waifus") \
                        .table("core") \
                        .has_fields("popularity_rank") \
                        .order_by("popularity_rank") \
                        .limit(100) \
                        .sample(1) \
                        .nth(0) \
                        .run(conn)
            waifu = Waifu(**result)
            claim = Claim(
                id=r.uuid().run(conn),
                slug=waifu.slug,
                guild_id=None,
                channel_id=None,
                message_id=None,
                user_id=str(self.bot.user.id),
                jump_url=None,
                image_url=waifu.image_url,
                cached_images_urls=None,
                state=None,
                index=None,
                price=None,
                attack=None,
                defense=None,
                health=None,
                speed=None,
                magic=None,
                attack_mod=0,
                defense_mod=0,
                health_mod=0,
                speed_mod=0,
                magic_mod=0,
                trait_common=None,
                trait_uncommon=None,
                trait_rare=None,
                trait_legendary=None,
                timestamp=None,
                timestamp_cooldown=None,
            )
            r.db("waifus").table("claims").insert(claim.__dict__).run(conn)

            skills = [0,0,0,0,0]
            total_sp = max(total_sp + random.choice([0, 1, -1]), 0)
            for i, _ in enumerate(skills):
                max_sp = total_sp - sum(skills)
                if max_sp == 0:
                    break
                skills[i] = min(100, random.randint(1, max_sp))
            claim.attack = skills[0]
            claim.defense = skills[1]
            claim.health = skills[2]
            claim.speed = skills[3]
            claim.magic = skills[4]
            return claim
        
        # Check if user's duel on cooldown
        if await helpers.user_is_on_cooldown(inter.author, Cooldowns.DUEL):
            next_duel_at = await helpers.user_cooldown_expiration_time(inter.author, Cooldowns.DUEL)
            return await inter.response.send_message(
                content=f"{inter.author.mention} you are on a duel cooldown now.\n"
                        f"Try again {utilities.get_dyn_time_relative(next_duel_at)} ({utilities.get_dyn_time_short(next_duel_at)})",
                ephemeral=True
            )

        await inter.response.defer()
        
        opponent = await self.find_duel_opponent(inter.guild, inter.author)
        if not opponent:
            return await inter.edit_original_response(content=f"Couldn't find an opponent!")

        # Select both user's waifus
        index = int(waifu.split(".")[0]) # Parse string input for waifu select TODO add some error handling here like in managemywaifus
        users_claim = await reql_helpers.get_waifu_claim_index(inter.author, index)
        if opponent.id == self.bot.user.id:
            opps_claim = generate_bot_claim(users_claim.calculate_total_stats())
        else:
            opps_married_harem = await reql_helpers.get_harem_married(inter.guild, opponent)
            opps_claim = random.choice(opps_married_harem)
        
        # Create the duel VS image
        duel_image_url = await self.create_waifu_vs_img(users_claim, opps_claim)
        
        # Create the embed for the duel
        red_name = r.db("waifus").table("core").get(users_claim.slug).get_field("name").run(conn)
        blue_name = r.db("waifus").table("core").get(opps_claim.slug).get_field("name").run(conn)
        end_at = disnake.utils.utcnow() + datetime.timedelta(seconds=20)
        duel_embed = disnake.Embed(
            description=f"### {inter.author.mention} vs. {opponent.mention}\n"
                        f"- Choose your fate by selecting __**three**__ moves below!\n"
                        f"- Duel ends {utilities.get_dyn_time_relative(end_at)}",
            color=disnake.Color.yellow()
        ) \
        .set_image(url=duel_image_url) \
        .add_field(
            name=f"{red_name} ({users_claim.stats_str()})",
            value=users_claim.skill_str()
        ) \
        .add_field(
            name=f"{blue_name} ({opps_claim.stats_str()})",
            value=opps_claim.skill_str()
        )
        
        # Set timestamp in db
        nyah_player = await reql_helpers.get_nyah_player(inter.author)
        nyah_player.timestamp_last_duel = disnake.utils.utcnow()
        await reql_helpers.set_nyah_player(nyah_player)

        # Generate the results of the duel for the user to choose from
        duel_choices = []
        for _ in range(6): #TODO move magic number somewhere else
            user_score = calculate_total_score(users_claim)
            opps_score = calculate_total_score(opps_claim)
            if user_score > opps_score:
                duel_choices.append(True)
            elif user_score < opps_score:
                duel_choices.append(False)
            else:
                if random.random() < 0.5:
                    duel_choices.append(True)
                else:
                    duel_choices.append(False)
        logger.debug(duel_choices)

        # Send the message
        message = await inter.edit_original_response(embed=duel_embed)
        
        # Create our view
        duel_view = WaifuDuelView(
            embed=duel_embed,
            author=inter.author,
            duel_choices=duel_choices
        )
        duel_view.message = message
        
        # Add the view to the message
        await inter.edit_original_response(view=duel_view)
        
        # Give the user some time to make selections
        await asyncio.sleep(20)
        await duel_view.on_timeout()

        # If user won, they attain MMR and gain XP
        if duel_view.author_won:
            result_embed = disnake.Embed(
                title="Win",
                description=f"- {inter.author.mention}'s __**{red_name}**__ defeated {opponent.mention}'s __**{blue_name}**__\n"
                            f"- You gained `{MMR.DUEL_WIN.value}` MMR and earned `{Experience.DUEL_WIN.value}` XP",
                color=disnake.Color.green()
            )
            logger.debug(f"{inter.author.name} beat {opponent.name} & gained {MMR.DUEL_WIN.value} MMR")
            await helpers.add_user_mmr(inter.author, MMR.DUEL_WIN.value)
            await helpers.add_user_xp(inter.author, Experience.DUEL_WIN.value, inter.channel)

        # If user lost, they lose MMR but gain XP
        else:
            result_embed = disnake.Embed(
                title="Loss",
                description=f"- {inter.author.mention}'s __**{red_name}**__ lost to {opponent.mention}'s __**{blue_name}**__\n"
                            f"- You lost `{MMR.DUEL_LOSS.value}` MMR and earned `{Experience.DUEL_LOSS.value}` XP",
                color=disnake.Color.red()
            )
            logger.debug(f"{inter.author.name} lost to {opponent.name} & lost {MMR.DUEL_LOSS.value} MMR")
            await helpers.add_user_mmr(inter.author, MMR.DUEL_LOSS.value)
            await helpers.add_user_xp(inter.author, Experience.DUEL_LOSS.value, inter.channel)

        # Edit message to add embed with the result of the match
        return await inter.edit_original_response(embeds=[duel_embed, result_embed])

    ##*************************************************##
    ##********          AUTOCOMPLETES           *******##
    ##*************************************************##

    @skillmywaifu.autocomplete("waifu")
    @managemywaifus.autocomplete("waifu")
    @duelmywaifu.autocomplete("waifu")
    async def harem_autocomplete(
        self,
        inter: disnake.ApplicationCommandInteraction,
        user_input: str
    ) -> list:
        harem_size = await reql_helpers.get_harem_size(inter.guild, inter.author)
        
        if user_input.isdigit() and int(user_input) <= harem_size:
            index = int(user_input)
            claim = await reql_helpers.get_waifu_claim_index(inter.author, index)
            waifu = await reql_helpers.get_waifu_core(claim.slug)
            formatted_name = f"{claim.index + 1}. {waifu.name}"
            waifu_names = [formatted_name]
        else:
            harem = await reql_helpers.get_harem(inter.guild, inter.author)
            
            waifu_names = []
            for claim in harem:
                waifu = await reql_helpers.get_waifu_core(claim.slug)
                formatted_name = f"{claim.index + 1}. {waifu.name} ({claim.stats_str()})"
                waifu_names.append(formatted_name)
        
        return deque(waifu_names, maxlen=25)

    @waifudex.autocomplete("name")
    async def waifu_name_autocomplete(
        self,
        inter: disnake.ApplicationCommandInteraction,
        user_input: str
    ) -> list:
        waifus = await reql_helpers.get_waifu_core_name(user_input)
        return deque([f"{waifu.name} [{waifu.series[0]}]" for waifu in waifus if len(waifu.series)], maxlen=25)

    @waifudex.autocomplete("series")
    async def waifu_series_autocomplete(
        self,
        inter: disnake.ApplicationCommandInteraction,
        user_input: str
    ) -> list:
        result = r.db("waifus") \
                    .table("core") \
                    .get_field("series") \
                    .concat_map(lambda x: x) \
                    .run(conn)
        result = list(set(result))
        comp = re.compile(f"(?i)^{user_input}")

        return list(filter(comp.match, result))[:25]

    @waifudex.autocomplete("tag")
    async def waifu_tag_autocomplete(
        self,
        inter: disnake.ApplicationCommandInteraction,
        user_input: str
    ) -> list:
        result = r.db("waifus") \
                    .table("core") \
                    .get_field("tags") \
                    .concat_map(lambda x: x) \
                    .run(conn)
        result = list(set(result))
        comp = re.compile(f"(?i)^{user_input}")

        return list(filter(comp.match, result))[:25]

def setup(bot: commands.Bot):
    required_env_vars = ["MAL_CLIENT_ID", "GOOGLE_KEY", "GOOGLE_SEARCH_ID"]
    for env_var in required_env_vars:
        if env_var not in os.environ or not os.environ[env_var]:
            return logger.error(f"Cannot load cog 'Waifus' | {env_var} not in environment!")
    bot.add_cog(Waifus(bot))