import datetime

import disnake
from loguru import logger

from nyahbot.util.constants import (
    Emojis,
    WaifuState,
    Experience,
    Money,
    Cooldowns,
)
from nyahbot.util.dataclasses import (
    Waifu,
    Claim,
)
from nyahbot.util import (
    reql_helpers,
    api_helpers,
)

cooldown_attribute_map = {
    Cooldowns.CLAIM: {
        "interval": "interval_claim_mins",
        "timestamp": "timestamp_last_claim",
    },
    Cooldowns.DUEL: {
        "interval": "interval_duel_mins",
        "timestamp": "timestamp_last_duel",
    },
    Cooldowns.MINIGAME: {
        "interval": "interval_minigame_mins",
        "timestamp": "timestamp_last_minigame",
    },
}

def calculate_xp_for_level(level: int) -> int:
    """ Returns the XP needed for this level before the next. """
    if level == 1:
        return Experience.BASE_LEVEL.value
    else:
        previous_xp = calculate_xp_for_level(level - 1)
        return int(previous_xp + int(previous_xp * 0.05))

def calculate_accumulated_xp(level: int) -> int:
    """ Returns the total XP needed to reach this level. """
    xp_accumulated = 0
    for level in range(1, level + 1):
        xp_needed = calculate_xp_for_level(level)
        xp_accumulated += xp_needed
    return xp_accumulated

async def add_user_xp(user: disnake.Member | disnake.User, xp: int, channel: disnake.TextChannel = None) -> None:
    nyah_player = await reql_helpers.get_nyah_player(user)
    nyah_player.xp += xp
    logger.info(f"{user.name}[{user.id}] gained {xp}XP ({nyah_player.xp}XP)")

    # check if they leveled up
    if nyah_player.xp > calculate_accumulated_xp(nyah_player.level + 1):
        nyah_player.level += 1
        level_money = Money.PER_LEVEL.value * nyah_player.level
        nyah_player.money += level_money
        if channel:
            level_up_embed = disnake.Embed(
                description=f"### ㊗️ Congratulations {user.mention}! You are now level {nyah_player.level}!\n\n"
                            f"You have been awarded `{level_money:,}` {Emojis.COINS}",
                color=disnake.Color.dark_teal()
            ).set_thumbnail(url=user.avatar.url)
            await channel.send(embed=level_up_embed)
        logger.info(f"{user.name}[{user.id}] leveled up to level {nyah_player.level}")
    
    await reql_helpers.set_nyah_player(nyah_player)

async def add_user_mmr(user: disnake.Member | disnake.User, mmr: int) -> None:
    nyah_player = await reql_helpers.get_nyah_player(user)
    if nyah_player.score + mmr <= 0:
        nyah_player.score = 0
    else:
        nyah_player.score += mmr
    await reql_helpers.set_nyah_player(nyah_player)

async def add_user_money(user: disnake.Member | disnake.User, money: int) -> None:
    nyah_player = await reql_helpers.get_nyah_player(user)
    if nyah_player.money + money <= 0:
        nyah_player.money = 0
    else:
        nyah_player.money += money
    await reql_helpers.set_nyah_player(nyah_player)

async def sell_waifu(user: disnake.Member | disnake.User, claim: Claim) -> None:
    claim.state = WaifuState.SOLD.name
    claim.index = None
    await reql_helpers.set_waifu_claim(claim)
    await add_user_money(user, claim.price)

async def user_is_on_cooldown(user: disnake.Member | disnake.User, cooldown_type: Cooldowns) -> bool:
    nyah_guild = await reql_helpers.get_nyah_guild(user.guild)
    nyah_player = await reql_helpers.get_nyah_player(user)
    
    interval: int = nyah_guild.__dict__[cooldown_attribute_map[cooldown_type]["interval"]]
    timestamp: datetime.datetime = nyah_player.__dict__[cooldown_attribute_map[cooldown_type]["timestamp"]]

    if timestamp == None:
        return False # user not on cooldown
    
    timedelta = disnake.utils.utcnow() - timestamp
    if timedelta > datetime.timedelta(minutes=interval):
        return False # user not on cooldown
    
    return True # user is on cooldown

async def user_cooldown_expiration_time(user: disnake.Member | disnake.User, cooldown_type: Cooldowns) -> datetime.datetime:
    nyah_guild = await reql_helpers.get_nyah_guild(user.guild)
    nyah_player = await reql_helpers.get_nyah_player(user)
    
    interval: int = nyah_guild.__dict__[cooldown_attribute_map[cooldown_type]["interval"]]
    timestamp: datetime.datetime = nyah_player.__dict__[cooldown_attribute_map[cooldown_type]["timestamp"]]

    return timestamp + datetime.timedelta(minutes=interval)

async def reset_user_cooldown(user: disnake.Member | disnake.User, cooldown_type: str) -> None:
    nyah_player = await reql_helpers.get_nyah_player(user)

    nyah_player.__dict__[cooldown_attribute_map[cooldown_type]["timestamp"]] = None

    await reql_helpers.set_nyah_player(nyah_player)

async def reindex_guild_user_harem(guild: disnake.Guild, user: disnake.User | disnake.Member) -> None:
    nyah_guild = await reql_helpers.get_nyah_guild(guild)

    # Get user's harem
    harem = await reql_helpers.get_harem(guild, user)

    # Figure out how many waifus are ACTIVE and INACTIVE
    active_count = sum(1 for claim in harem if claim.state == WaifuState.ACTIVE.name)
    inactive_count = sum(1 for claim in harem if claim.state == WaifuState.INACTIVE.name)

    # Ensure there are at most 3 ACTIVE claims and at least 0 INACTIVE claims
    if active_count < nyah_guild.waifu_max_marriages and inactive_count > 0:
        for claim in harem:
            if claim.state == WaifuState.INACTIVE.name:
                claim.state = WaifuState.ACTIVE.name
                active_count += 1
            if active_count >= nyah_guild.waifu_max_marriages:
                break
    elif active_count > nyah_guild.waifu_max_marriages:
        for claim in harem:
            if claim.state == WaifuState.ACTIVE.name:
                claim.state = WaifuState.INACTIVE.name
                active_count -= 1
            if active_count <= nyah_guild.waifu_max_marriages:
                break
    
    # Sort by state and index
    sorted_harem = sorted(harem, key=lambda claim: (WaifuState[claim.state].value, claim.index))

    # Re-index
    for i, claim in enumerate(sorted_harem):
        claim.index = i
        
        # Update the claim in the db
        await reql_helpers.set_waifu_claim(claim)
    
    logger.info(f"{guild.name}[{guild.id}] | "
                f"{user.name}[{user.id}] | "
                f"Reindexed user's harem")

##*************************************************##
##********          WAIFU EMBEDS            *******##
##*************************************************##

async def get_waifu_base_embed(waifu: Waifu) -> disnake.Embed:
    """ Get a bare-bones embed for a waifu.
        - Name
        - Husbando classification
        - Default Image
        - Series (with MAL links)

    """
    # Get links to series on MAL
    waifu_series = []
    for series in waifu.series:
        mal_url = await api_helpers.search_mal_series(series)
        if mal_url:
            waifu_series.append(f"[{series}]({mal_url})")
        else:
            waifu_series.append(series)
    waifu_series = "\n".join(waifu_series)
    
    embed = disnake.Embed(
        title=waifu.name + "  ♂️" if waifu.husbando else waifu.name + "  ♀️",
        url=waifu.url,
        color=disnake.Color.fuchsia()
    ) \
    .set_image(url=waifu.image_url) \
    .add_field(name="Appears In", value=waifu_series)

    return embed

async def get_waifu_core_embed(waifu: Waifu) -> disnake.Embed:
    """ Get an ultra-detailed embed for a waifu.
        - Alternate names
        - Age & DOB
        - Measurements
        - Origin
        
    """
    embed = await get_waifu_base_embed(waifu)
    embed.description = (waifu.description[:4092] + "...") if len(waifu.description) > 4092 else waifu.description
    embed.color = disnake.Color.teal()
    embed.add_field(name="Original Name", value=waifu.original_name if waifu.original_name else "-") \
         .add_field(name="Romaji Name", value=waifu.romaji_name if waifu.romaji_name else "-") \
         .add_field(name="Place of Origin", value=waifu.origin if waifu.origin else "-") \
         .add_field(name="Age", value=waifu.age if waifu.age else "-") \
         .add_field(name="Date of Birth", value=waifu.date_of_birth if waifu.date_of_birth else "-") \
         .add_field(name="Height", value=waifu.height if waifu.height else "-") \
         .add_field(name="Weight", value=waifu.weight if waifu.weight else "-") \
         .add_field(name="Blood Type", value=waifu.blood_type if waifu.blood_type else "-") \
         .add_field(name="Bust", value=waifu.bust if waifu.bust else "-") \
         .add_field(name="Waist", value=waifu.waist if waifu.waist else "-") \
         .add_field(name="Hip", value=waifu.hip if waifu.hip else "-")
    return embed

async def get_waifu_skills_embed(claim: Claim) -> disnake.Embed:
    waifu = await reql_helpers.get_waifu_core(claim.slug)
    
    embed = await get_waifu_base_embed(waifu)
    embed.add_field(name="Price", value=claim.price_str())
    embed.add_field(name="Traits", value=claim.trait_str())
    embed.add_field(name=f"Skills ({claim.stats_str()})", value=claim.skill_str())
    embed.set_footer(text=claim.id)
    embed.set_image(url=claim.image_url)
    return embed

async def get_waifu_claim_embed(claim: Claim, owner: disnake.User | disnake.Member) -> disnake.Embed:
    """ Get an embed of a waifu just claimed.
        - Price listed.
        - Skills listed.
        - Traits listed.

        Parameters
        ----------
        waifu: `Waifu`
            The waifu to retrieve.
        owner: `disnake.User` | `disnake.Member`
            The owner of this waifu.
        
        Returns
        -------
        `disnake.Embed`
            The embed.
    """
    waifu = await reql_helpers.get_waifu_core(claim.slug)
    waifu_type = "husbando" if waifu.husbando else "waifu"

    embed = await get_waifu_skills_embed(claim)
    embed.timestamp = disnake.utils.utcnow()
    embed.set_footer(text=f"A {waifu_type} for {owner.name} >.<")
    return embed

async def get_waifu_harem_embed(claim: Claim) -> disnake.Embed:
    """ Get an embed of a waifu in a harem.
        - Embed color represents state.
        - Skills listed.
        - Price listed.
        - Traits listed.
        - Marriage status.
    
    """
    if claim.state == WaifuState.ACTIVE.name:
        color = disnake.Color.green()
        status = f"💕 Married"
    elif claim.state == WaifuState.COOLDOWN.name:
        color = disnake.Color.blue()
        status = f"❄️ Cooldown"
    elif claim.state == WaifuState.INACTIVE.name:
        color = disnake.Color.red()
        status = f"💔 Unmarried"
    
    embed = await get_waifu_skills_embed(claim)
    embed.add_field(name="Status", value=status)
    embed.color = color
    return embed

##*************************************************##
##********           WAIFU WARS             *******##
##*************************************************##

