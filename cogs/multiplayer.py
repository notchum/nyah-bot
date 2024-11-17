import random
import asyncio
import datetime
from collections import deque
from typing import Tuple, List

import disnake
from disnake.ext import commands
from loguru import logger

import models
from bot import NyahBot
from helpers import ErrorEmbed
from utils.constants import Cooldowns, Experience
from views import DuelView


class Multiplayer(commands.Cog):
    def __init__(self, bot: NyahBot):
        self.bot = bot

    async def find_duel_opponent(self, guild: disnake.Guild, user: disnake.User | disnake.Member) -> Tuple[disnake.User, int]:
        nyah_players = await self.bot.mongo.fetch_all_nyah_players()
        nyah_player = await self.bot.mongo.fetch_nyah_player(user)

        neighbors = []
        user_rating = nyah_player.score
        total_players = len(nyah_players)

        # Determine the number of neighbors above and below the user based on total players
        num_neighbors = min(total_players - 1, 4)  # Max 4 neighbors (2 above, 2 below)

        for i, neighbor in enumerate(nyah_players):
            if await self.bot.mongo.fetch_harem_married_count(neighbor) != 3:
                continue
            if neighbor.user_id != nyah_player.user_id:
                if i < num_neighbors or (total_players - i) <= num_neighbors:
                    neighbors.append(neighbor)

        # No suitable neighbors
        if not neighbors:
            bot_rating = max(user_rating + random.randint(-int(user_rating * 0.03), int(user_rating * 0.10)), 0)
            return self.bot.user, bot_rating

        # Calculate similarity scores for each neighbor
        similarity_scores = []
        for neighbor in neighbors:
            score_diff = abs(user_rating - neighbor.score) // 10
            similarity_score = 1 / (1 + score_diff)
            similarity_scores.append(similarity_score)
        
        # Check if there's a similarity score greater than 20%
        # if max(similarity_scores) < 0.20:
        #     bot_rating = max(user_rating + random.randint(-int(user_rating * 0.03), int(user_rating * 0.10)), 0)
        #     return self.bot.user, bot_rating

        # Select the opponent with the highest similarity score
        # best_opponent = neighbors[similarity_scores.index(max(similarity_scores))]
            
        # Select a random opponent
        best_opponent = random.choice(neighbors)
        opponent = await guild.fetch_member(best_opponent.user_id)
        return opponent, best_opponent.score

    async def generate_bot_claim(self, total_sp: int) -> models.Claim:
        waifu = await self.bot.mongo.fetch_random_waifu([{"$match": {"popularity_rank": {"$lt": 200}}}])

        skills = [0,0,0,0,0]
        ten_percent = int(total_sp * 0.10)
        total_sp = max(total_sp + random.randint(-ten_percent, ten_percent), 0)
        for i, _ in enumerate(skills):
            max_sp = total_sp - sum(skills)
            if max_sp == 0:
                break
            skills[i] = min(100, random.randint(1, max_sp))
        
        return models.Claim(
            slug=waifu.slug,
            name=waifu.name,
            user_id=self.bot.user.id,
            image_url=waifu.image_url,
            cached_images_urls=[],
            tier=1,
            attack=skills[0],
            defense=skills[1],
            health=skills[2],
            speed=skills[3],
            magic=skills[4],
            health_points=skills[2]
        )

    def calculate_total_score(self, claim: models.Claim) -> float:
        base_score = (claim.attack + claim.attack_mod) * 0.4 + \
                     (claim.defense + claim.defense_mod) * 0.35 + \
                     (claim.health + claim.health_mod) * 0.36 + \
                     (claim.speed + claim.speed_mod) * 0.39 + \
                     (claim.magic + claim.magic_mod) * 0.38
        random_modifier = random.uniform(0.6, 1.2)
        return base_score * random_modifier

    def calculate_new_rating(
        self,
        player_a_rating: int,
        player_b_rating: int,
        player_a_won: bool,
        k_factor = 32
    ) -> int:
        expected_probability_a = 1 / (1 + 10**((player_b_rating - player_a_rating) / 400))
        expected_probability_b = 1 - expected_probability_a

        logger.debug(f"Expected probability of player A winning: {expected_probability_a}")

        if player_a_won:
            new_rating_a = player_a_rating + k_factor * (1 - expected_probability_a)
            new_rating_b = player_b_rating - k_factor * (1 - expected_probability_a)
        else:
            new_rating_a = player_a_rating - k_factor * (1 - expected_probability_b)
            new_rating_b = player_b_rating + k_factor * (1 - expected_probability_b)

        rating_difference_a = new_rating_a - player_a_rating
        rating_difference_b = new_rating_b - player_b_rating

        return round(rating_difference_a)

    @commands.slash_command()
    async def leaderboard(self, inter: disnake.ApplicationCommandInteraction):
        """ View the Waifu Wars leaderboard! """
        nyah_config = await self.bot.mongo.fetch_nyah_config()
        season_end = nyah_config.timestamp_last_season_end + datetime.timedelta(days=nyah_config.interval_season_days)
        embed = disnake.Embed(
            description=f"Season ends {disnake.utils.format_dt(season_end, "R")}",
            color=disnake.Color.random()
        )

        nyah_players = await self.bot.mongo.fetch_active_nyah_players()
        if not nyah_players:
            embed.title = "Top Weebs"
            embed.description = "No one is on the scoreboard yet! Use `/getmywaifu` to get started!"
            return embed
        
        ranking_str = ""
        member_str = ""
        for i, player in enumerate(nyah_players, 1):
            if i == 1:
                rank_one_member = await self.bot.fetch_user(player.user_id)
                embed.set_author(name="Top Weebs", icon_url=rank_one_member.display_avatar.url)
            ranking_str += f"`{i}` **{player.score}**\n"
            member_str += f"<@{player.user_id}>\n"

        embed.add_field(name="Ranking", value=ranking_str)
        embed.add_field(name="Member", value=member_str)

        return await inter.response.send_message(embed=embed)

    @commands.slash_command()
    async def duel(self, inter: disnake.ApplicationCommandInteraction):
        """ Use your waifus to duel other user's waifus! """
        # Gather user's db info
        nyah_player = await self.bot.mongo.fetch_nyah_player(inter.author)

        # Check if user's duel on cooldown
        if await nyah_player.user_is_on_cooldown(Cooldowns.DUEL):
            next_duel_at = await nyah_player.user_cooldown_expiration_time(Cooldowns.DUEL)
            return await inter.response.send_message(
                content=f"{inter.author.mention} you are on a duel cooldown now.\n"
                        f"Try again {disnake.utils.format_dt(next_duel_at, "R")} ({disnake.utils.format_dt(next_duel_at, "t")})",
                ephemeral=True
            )
        
        # Gather the config
        nyah_config = await self.bot.mongo.fetch_nyah_config()
        
        # Make sure user has a full harem
        harem_married_size = await self.bot.mongo.fetch_harem_married_count(inter.author)
        if harem_married_size != nyah_config.waifu_max_marriages:
            return await inter.response.send_message(
                embed=ErrorEmbed(f"You need `{nyah_config.waifu_max_marriages}` married waifus to duel!")
            )
        
        await inter.response.defer()
        
        # Find opponent
        opponent, opponent_rating = await self.find_duel_opponent(inter.guild, inter.author)
        if not opponent:
            return await inter.edit_original_response(content=f"Couldn't find an opponent!")
        logger.debug(f"Duel created: {nyah_player.score}.{inter.author.name}[{inter.author.id}] vs "
                              f"{opponent_rating}.{opponent.name}[{opponent.id}]")

        # Get player's harem
        player_married_harem = await self.bot.mongo.fetch_harem_married(inter.author)
        
        # Get opponent's harem
        if opponent.id == self.bot.user.id:
            opponent_married_harem = [await self.generate_bot_claim(500) for _ in range(3)]
        else:
            opponent_married_harem = await self.bot.mongo.fetch_harem_married(opponent)

        # Set timestamp in db
        # nyah_player.timestamp_last_duel = disnake.utils.utcnow()
        # await self.bot.mongo.update_nyah_player(nyah_player)

        # Create the message
        duel_view = DuelView(
            bot=self.bot,
            author=inter.author,
            player_harem=player_married_harem,
            opponent_harem=opponent_married_harem,
        )
        duel_view.message = await inter.edit_original_response(content="Creating duel...", view=duel_view)
        await duel_view.initialize()
        
        # Wait for the battle to finish
        await duel_view.wait()

        await inter.edit_original_response("finished")
        return

        # Calculate and update user's MMR
        rating_change = self.calculate_new_rating(nyah_player.score, opponent_rating, duel_view.author_won)
        await nyah_player.add_user_mmr(rating_change)

        # Opponents lose a slight amount of MMR to discourage inactivity
        if opponent.id != self.bot.user.id and duel_view.author_won:
            opps_nyah_player = await self.bot.mongo.fetch_nyah_player(opponent)
            await opps_nyah_player.add_user_mmr(-int(rating_change * 0.35))

        # If user won
        if duel_view.author_won:
            result_embed = disnake.Embed(
                title="Ranked Win",
                description=f"- {inter.author.mention}'s __**{red_waifu.name}**__ defeated {opponent.mention}'s __**{blue_waifu.name}**__\n"
                            f"- You gained `{rating_change}` MMR and earned `{Experience.DUEL_WIN.value}` XP",
                color=disnake.Color.green()
            )
            await nyah_player.add_user_xp(Experience.DUEL_WIN.value, inter.author, inter.channel)

        # If user lost
        else:
            result_embed = disnake.Embed(
                title="Ranked Loss",
                description=f"- {inter.author.mention}'s __**{red_waifu.name}**__ lost to {opponent.mention}'s __**{blue_waifu.name}**__\n"
                            f"- You lost `{rating_change}` MMR and earned `{Experience.DUEL_LOSS.value}` XP",
                color=disnake.Color.red()
            )
            await nyah_player.add_user_xp(Experience.DUEL_LOSS.value, inter.author, inter.channel)

        logger.debug(f"{inter.author.name}'s new rating: {nyah_player.score}")

        # Edit message to add embed with the result of the match
        return await inter.edit_original_response(embeds=[duel_embed, result_embed])

    @commands.slash_command()
    async def casual(
        self, 
        inter: disnake.ApplicationCommandInteraction,
        opponent: disnake.User,
        waifu: str
    ):
        """ Duel another user for fun. """
        # Gather user's db info
        nyah_player = await self.bot.mongo.fetch_nyah_player(inter.author)

        # Check if user's duel on cooldown TODO
        # if await nyah_player.user_is_on_cooldown(Cooldowns.DUEL):
        #     next_duel_at = await nyah_player.user_cooldown_expiration_time(Cooldowns.DUEL)
        #     return await inter.response.send_message(
        #         content=f"{inter.author.mention} you are on a duel cooldown now.\n"
        #                 f"Try again {disnake.utils.format_dt(next_duel_at, "R")} ({disnake.utils.format_dt(next_duel_at, "t")})",
        #         ephemeral=True
        #     )
        
        # Parse string input for waifu select
        try:
            index = int(waifu.split(".")[0])
        except:
            return await inter.response.send_message(
                embed=ErrorEmbed(f"`{waifu}` is not a valid waifu!"),
                ephemeral=True
            )

        users_claim = await self.bot.mongo.fetch_claim_by_index(inter.author, index)
        if not users_claim:
            return await inter.response.send_message(
                embed=ErrorEmbed(f"`{waifu}` is not a valid character!"),
                ephemeral=True
            )
        if not users_claim.is_married:
            return await inter.response.send_message(
                embed=ErrorEmbed(f"`{waifu}` is not a married character!"),
                ephemeral=True
            )
        if opponent.id == inter.author.id:
            return await inter.response.send_message(
                embed=ErrorEmbed(f"You can't duel yourself!"),
                ephemeral=True
            )
        
        await inter.response.defer()
        
        # Make sure opponent has a married character
        opps_harem_married_size = await self.bot.mongo.fetch_harem_married_count(opponent)
        if opps_harem_married_size == 0:
            return await inter.edit_original_response(
                embed=ErrorEmbed(f"{opponent.mention} has no characters to duel!")
            )

        # Select both user's waifus
        opps_married_harem = await self.bot.mongo.fetch_harem_married(opponent)
        opps_claim = random.choice(opps_married_harem)
        
        # Create the duel VS image
        duel_image_url = await self.bot.create_waifu_vs_img(users_claim, opps_claim)
        
        # Create the embed for the duel
        red_waifu = await self.bot.mongo.fetch_waifu(users_claim.slug)
        blue_waifu = await self.bot.mongo.fetch_waifu(opps_claim.slug)
        end_at = disnake.utils.utcnow() + datetime.timedelta(seconds=20)
        duel_embed = disnake.Embed(
            description=f"### {inter.author.mention} vs. {opponent.mention}\n"
                        f"- Choose your fate by selecting __**three**__ moves below!\n"
                        f"- Duel ends {disnake.utils.format_dt(end_at, "R")}",
            color=disnake.Color.yellow()
        ) \
        .set_image(url=duel_image_url) \
        .add_field(
            name=f"{red_waifu.name} ({users_claim.skill_str_short})",
            value=users_claim.skill_str_long
        ) \
        .add_field(
            name=f"{blue_waifu.name} ({opps_claim.skill_str_short})",
            value=opps_claim.skill_str_long
        )
        
        # Set timestamp in db TODO
        # nyah_player.timestamp_last_duel = disnake.utils.utcnow()
        # await self.bot.mongo.update_nyah_player(nyah_player)

        # Generate the results of the duel for the user to choose from
        duel_choices = []
        for _ in range(6): #TODO move magic number somewhere else
            user_score = self.calculate_total_score(users_claim)
            opps_score = self.calculate_total_score(opps_claim)
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
        duel_view = DuelView(
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

        # If user won
        if duel_view.author_won:
            result_embed = disnake.Embed(
                title="Casual Win",
                description=f"- {inter.author.mention}'s __**{red_waifu.name}**__ defeated {opponent.mention}'s __**{blue_waifu.name}**__\n",
                color=disnake.Color.green()
            )

        # If user lost
        else:
            result_embed = disnake.Embed(
                title="Casual Loss",
                description=f"- {inter.author.mention}'s __**{red_waifu.name}**__ lost to {opponent.mention}'s __**{blue_waifu.name}**__\n",
                color=disnake.Color.red()
            )

        # Edit message to add embed with the result of the match
        return await inter.edit_original_response(embeds=[duel_embed, result_embed])

    @casual.autocomplete("waifu")
    async def harem_autocomplete(
        self,
        inter: disnake.ApplicationCommandInteraction,
        user_input: str
    ) -> List[str]:
        harem_married_size = await self.bot.mongo.fetch_harem_married_count(inter.author)
        if harem_married_size == 0:
            return [f"You have no waifus to duel!"]
        
        if user_input.isdigit() and int(user_input) <= harem_married_size:
            index = int(user_input)
            claim = await self.bot.mongo.fetch_claim_by_index(inter.author, index)
            waifu = await self.bot.mongo.fetch_waifu(claim.slug)
            formatted_name = f"{claim.index}. {waifu.name}"
            waifu_names = [formatted_name]
        else:
            harem = await self.bot.mongo.fetch_harem_married(inter.author)
            
            waifu_names = []
            for claim in harem:
                waifu = await self.bot.mongo.fetch_waifu(claim.slug)
                formatted_name = f"{claim.index}. {waifu.name} ({claim.skill_str_short})"
                waifu_names.append(formatted_name)
        
        return deque(waifu_names, maxlen=25)


def setup(bot: commands.Bot):
    bot.add_cog(Multiplayer(bot))
