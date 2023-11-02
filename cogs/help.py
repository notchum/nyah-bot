import datetime

import disnake
from disnake.ext import commands

from bot import NyahBot
from views import WaifuPaginator
from utils import Money, Emojis
import utils.traits as traits
import utils.utilities as utils

class Help(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot: NyahBot = bot

    ##*************************************************##
    ##********           ABSTRACTIONS           *******##
    ##*************************************************##

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
        for event in guild.scheduled_events:
            if event.creator_id != self.bot.user.id:
                continue
            if event.name == "Waifu War":
                return event
        return None

    ##*************************************************##
    ##********              EVENTS              *******##
    ##*************************************************##

    ##*************************************************##
    ##********              TASKS               *******##
    ##*************************************************##

    ##*************************************************##
    ##********             COMMANDS             *******##
    ##*************************************************##

    @commands.slash_command()
    async def info(self, inter: disnake.ApplicationCommandInteraction):
        """ Everything you need to know! """
        await inter.response.defer()

        nyah_config = await self.bot.mongo.fetch_nyah_config()
        start_time = datetime.datetime.combine(
            date=disnake.utils.utcnow().date(),
            time=datetime.time(nyah_config.waifu_war_hour, 0), #??? should this be hour in UTC? it is MDT now...
        )
        
        waifu_war_event = await self.get_waifu_war_event(inter.guild)
        waifu_war_event_link = waifu_war_event.url if waifu_war_event else "**__None scheduled right now :(__**"

        embed1 = disnake.Embed(
            title="What are the main commands?",
            color=disnake.Color.random(),
            description=f"- `/getmywaifu`: Get a random waifu! (Cooldown time: `{nyah_config.interval_claim_mins / 60}` hours)\n"
                        f"- `/listmywaifus`: View all of your waifus (your harem) that you have now.\n"
                        f"- `/managemywaifus`: Scroll through your harem to change the order, pick a new image, sell, or marry a waifu.\n"
                        f"- `/duelmywaifu`: Use one of your married waifus to fight against other player's waifus to climb the leaderboard. (Cooldown time: `{nyah_config.interval_duel_mins / 60}` hours)\n"
                        f"- `/minigame`: Play a waifu minigame for a chance to earn coins. (Cooldown time: `{nyah_config.interval_minigame_mins / 60}` hours)\n"
                        f"- `/profile`: View your current level, XP, SP, and balance.\n"
                        f"- `/leaderboard`: View the player rankings ladder.\n",
        )

        embed2 = disnake.Embed(
            title="How do duels work?",
            color=disnake.Color.random(),
            description=f"- Choose three moves from the choices that appear below the image.\n"
                        f"- If your move fails, the button will turn red and you lose a life.\n"
                        f"- If your move succeeds, the button will turn green and reveal a failing move (don't press it!).\n"
                        f"- If 2 out of 3 of your moves succeed, you win the duel!\n"
                        f"- Winning a duel will give you both XP and MMR that will increase your leaderboard rank."
                        f" Losing will lose you MMR, decreasing your rank.\n",
        )

        embed3 = disnake.Embed(
            title="What is a Waifu War?",
            color=disnake.Color.random(),
            description=f"- A Waifu War is a bracket-style tournament that you and your harem can participate in."
                        f" There is a Waifu War held every day at {utils.get_dyn_time_short(start_time)}\n"
                        f"- To enter a Waifu War, mark yourself as interested to the event in this Discord server.\n"
                        f"  - Next scheduled Waifu War: {waifu_war_event_link}\n"
                        f"- Your harem will be matched up against another player's harem during each round of the tournament."
                        f" One random waifu from your harem will be put up against one of your oppenent's waifus."
                        f" The winner is decided via a poll, in which all users are allowed to cast a vote for the winner."
                        f" The waifu with the most votes wins the battle (tied votes are broken by the bot)."
                        f" __The user with the losing waifu will lose their waifu from their harem.__\n"
                        f"- To advance to the next round, your harem will have to defeat all waifus in your opponent's harem.\n"
                        f"- Participating in a Waifu War will always give you XP; but the further you make it, the more XP you recieve!\n"
                        f"- Rewards for making the grand finals are:\n"
                        f"  - `{Money.WAR_FIRST.value:,}` {Emojis.COINS} for first place\n"
                        f"  - `{Money.WAR_SECOND.value:,}` {Emojis.COINS} for runner-up\n",
        )
        
        embed4 = disnake.Embed(
            title="FAQ",
            color=disnake.Color.random(),
            description=f"- **How do I level-up?**\n"
                        f"  - Playing minigames, participating in Waifu Wars, and dueling all grant you XP to level-up.\n"
                        f"- **How do skill points work?**\n"
                        f"  - Each waifu has five skills: **🗡️Attack, 🛡️Defense, ❤️Health, 🌀Speed, & ✨Magic**."
                        f" Each skill will have a value `0`-`100`."
                        f" These skills increase your waifu's odds of winning in a duel the higher they are.\n"
                        f"  - Using `/skillmywaifu`, you can select one of your waifus and reroll their skill points (SP).\n"
                        f"- **What are traits**\n"
                        f"  - Each waifu will have a chance of acquiring certain traits."
                        f" It is possible to have one trait from each tier: **🟢 Common, 🔵 Uncommon, 🟣 Rare, & 🟠 Legendary**."
                        f" As you level-up, your odds of getting higher tiered traits increase."
                        f" Traits that increase certain skills make it possible to increase any single skill beyond the base cap of `100`.\n"
                        f"  - Use `/traits` to view all possible traits.\n"
                        f"- **What do I spend my coins on?**\n"
                        f"  - Rerolling the SP of any one of your waifus (as mentioned above) will cost `{Money.SKILL_COST.value:,}` {Emojis.COINS} each time.\n"
                        f"  - Wishlisting a waifu with `/wishlist add` will cost `{Money.WISHLIST_COST.value:,}` {Emojis.COINS} for an extra 5% chance to pull that waifu.\n"
                        f"- **Can I wishlist a waifu more than once?**\n"
                        f"  - Yes, wishlist the same waifu multiple times for even better odds you get them!\n"
                        f"  - If you pull a waifu from your wishlist, that waifu is removed from your wishlist.\n"
                        f"- **How do I win?**\n"
                        f"  - You win by topping the leaderboard ladder!\n"
                        f"- **What resets at the end of a season?**\n"
                        f"  - A season lasts `{nyah_config.interval_season_days}` days."
                        f" All user's waifus, scores, and coins are reset at the end of the season.\n",
        )
        
        embeds = [embed1, embed2, embed3, embed4]
        
        waifu_page_view = WaifuPaginator(embeds, inter.author)
        message = await inter.edit_original_response(embed=embeds[0], view=waifu_page_view)
        waifu_page_view.message = message
        return

    @commands.slash_command()
    async def traits(self, inter: disnake.ApplicationCommandInteraction):
        """ View all traits and their effects! """
        await inter.response.defer()

        embeds = []
        for i, title, color in [(traits.CharacterTraitsCommon, "🟢 Common Traits", disnake.Color.green()),
                                (traits.CharacterTraitsUncommon, "🔵 Uncommon Traits", disnake.Color.blue()),
                                (traits.CharacterTraitsRare, "🟣 Rare Traits", disnake.Color.purple()),
                                (traits.CharacterTraitsLegendary, "🟠 Legendary Traits", disnake.Color.orange())]:
            e = disnake.Embed(
                title=title,
                description=i.__str__(),
                color=color
            )
            embeds.append(e)
        
        waifu_page_view = WaifuPaginator(embeds, inter.author)
        message = await inter.edit_original_response(embed=embeds[0], view=waifu_page_view)
        waifu_page_view.message = message
        return

    ##*************************************************##
    ##********          AUTOCOMPLETES           *******##
    ##*************************************************##

def setup(bot: commands.Bot):
    bot.add_cog(Help(bot))