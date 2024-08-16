import re
import traceback
from typing import List

import disnake

from utils import Experience

##*************************************************##
##********            NYAH UTILS            *******##
##*************************************************##


def calculate_xp_for_level(level: int) -> int:
    """Returns the XP needed for this level before the next.
    
    Parameters
    ----------
    level: :class:`int`
        TODO
    
    Returns
    -------
    :class:`int`
        TODO
    """
    if level == 1:
        return Experience.BASE_LEVEL.value
    else:
        previous_xp = calculate_xp_for_level(level - 1)
        return int(previous_xp + int(previous_xp * 0.05))

def calculate_accumulated_xp(level: int) -> int:
    """Returns the total XP needed to reach this level.
    
    Parameters
    ----------
    level: :class:`int`
        TODO
    
    Returns
    -------
    :class:`int`
        TODO
    """
    xp_accumulated = 0
    for level in range(1, level + 1):
        xp_needed = calculate_xp_for_level(level)
        xp_accumulated += xp_needed
    return xp_accumulated


##*************************************************##
##********          DISCORD UTILS           *******##
##*************************************************##


def match_word(message: disnake.Message, word: str) -> bool:
    """Checks if a message contains a given word.

    Parameters
    ----------
    message: :class:`disnake.Message`
        The message.
    word: :class:`str`
        The word to match.

    Returns
    -------
    :class:`bool`
        Whether the message contains a match or not.
    """
    message_content = message.content.strip().lower()
    message_stripped = strip_extra(message_content)

    if word in message_content or word in message_stripped:
        return True
    return False


async def check_automod_block(guild: disnake.Guild, string: str) -> bool:
    """Queries a guild's AutoMod rules to see
        if a given string contains blocked words.

    Parameters
    ----------
    guild: :class:`disnake.Guild`
        The guild being checked.
    string: :class:`str`
        The string to check AutoMod against.

    Returns
    -------
    :class:`bool`
        True if a blocked word was present, False otherwise.
    """
    automod_rules = await guild.fetch_automod_rules()
    for rule in automod_rules:
        if rule.trigger_type.name == "keyword":
            for pattern in rule.trigger_metadata.regex_patterns:
                if re.compile(pattern).match(strip_extra(string)):
                    return True
    return False


def slash_command_mention(name: str, id: int) -> str:
    """A helper function to format a slash command as a Discord clickable mention.

    Parameters
    ----------
    name: :class:`str`
        The name of the command to mention.
    id: :class:`int`
        The ID of the command to mention.
        Obtained by typing the slash command in Discord and right-clicking on the
        pop-up box then 'Copy Command ID'.

    Returns
    -------
    :class:`str`
        The formatted string.
    """
    return f"</{name}:{id}>"


def get_cog_names() -> List[str]:
    """Get the names of every cog/extension that should be loaded.

    Returns
    -------
    List[:class:`str`]
        The cogs/extensions that should be loaded with `load_extension`.
    """
    return [ext_name for ext_name in disnake.utils.search_directory("cogs")]


##*************************************************##
##********          GENERAL UTILS           *******##
##*************************************************##


def strip_extra(string: str) -> str:
    """Return a copy of the string with all non-word
    characters removed.

    Parameters
    ----------
    string: :class:`str`
        The text to strip.

    Returns
    -------
    :class:`str`
        The stripped string.
    """
    return re.sub(r"\W+", "", string.strip().lower())


def create_trace(err: Exception, advance: bool = True) -> str:
    """A way to debug your code anywhere.

    Parameters
    ----------
    err: :class:`Exception`
        The exception to trace.
    advance: :class:`bool`
        +++. (Default: True)

    Returns
    -------
    :class:`str`
        A formatted string of the debug trace.
    """
    _traceback = "".join(traceback.format_tb(err.__traceback__))
    error = ("```py\n{1}{0}: {2}\n```").format(type(err).__name__, _traceback, err)
    return error if advance else f"{type(err).__name__}: {err}"


def chunkify(to_chunk: str) -> List[str]:
    """Split up a long string into 1000 character substrings.

    Parameters
    ----------
    to_chunk: :class:`str`
        The string to split up.

    Returns
    -------
    List[:class:`str`]
        A list containing the 'chunks' of strings capped
        at 1000 characters each.
    """
    len_chunks = ceildiv(len(to_chunk), 1000)
    chunks = []
    for i in range(len_chunks):
        chunked_str = to_chunk[(1000 * i) : (1000 if i == 0 else 1000 * (i + 1))]
        chunks.append(chunked_str)
    return chunks


def humanbytes(B: int) -> str:
    """Return the given bytes as a human friendly KB, MB, GB, or TB string."""
    B = float(B)
    KB = float(1024)
    MB = float(KB**2)  # 1,048,576
    GB = float(KB**3)  # 1,073,741,824
    TB = float(KB**4)  # 1,099,511,627,776

    if B < KB:
        return "{0} {1}".format(B, "Bytes" if 0 == B > 1 else "Byte")
    elif KB <= B < MB:
        return "{0:.2f} KB".format(B / KB)
    elif MB <= B < GB:
        return "{0:.2f} MB".format(B / MB)
    elif GB <= B < TB:
        return "{0:.2f} GB".format(B / GB)
    elif TB <= B:
        return "{0:.2f} TB".format(B / TB)


def extract_uuid(input_string: str) -> str | None:
    """Extract the UUID from any string.

    Parameters
    ----------
    input_string: :class:`str`
        A string that has a UUID.

    Returns
    -------
    :class:`str`
        The UUID or `None` if no UUID is found.
    """
    # Regular expression to match any version 4 UUID
    uuid_pattern = r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-4[0-9a-fA-F]{3}-[89abAB][0-9a-fA-F]{3}-[0-9a-fA-F]{12}"

    # Find the first matching UUID in the input string
    uuid_match = re.search(uuid_pattern, input_string)

    if uuid_match:
        return uuid_match.group()
    else:
        return None


def ceildiv(a: int, b: int) -> int:
    """Upside-down floor division (ceiling).

    Parameters
    ----------
    a: :class:`int`
        The dividend.
    b: :class:`int`
        The divisor.

    Returns
    -------
    :class:`int`
        The result.
    """
    return -(a // -b)
