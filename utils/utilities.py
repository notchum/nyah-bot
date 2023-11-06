import re
import uuid
import traceback

import disnake

from utils import Experience

##*************************************************##
##********            NYAH UTILS            *******##
##*************************************************##

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

##*************************************************##
##********          DISCORD UTILS           *******##
##*************************************************##

""" Get a dynamic date-time display in your Discord messages. """
get_dyn_time_short = lambda t: f"<t:{int(t.timestamp())}:t>"
get_dyn_time_long = lambda t: f"<t:{int(t.timestamp())}:T>"
get_dyn_date_short = lambda t: f"<t:{int(t.timestamp())}:d>"
get_dyn_date_long = lambda t: f"<t:{int(t.timestamp())}:D>"
get_dyn_date_long_time_short = lambda t: f"<t:{int(t.timestamp())}:f>"
get_dyn_date_long_time_long = lambda t: f"<t:{int(t.timestamp())}:F>"
get_dyn_time_relative = lambda t: f"<t:{int(t.timestamp())}:R>"

##*************************************************##
##********          GENERAL UTILS           *******##
##*************************************************##

def create_trace(err: Exception, advance: bool = True) -> str:
    """ A way to debug your code anywhere.

        Parameters
        ----------
        err: `Exception`
            The exception to trace
        advance: `bool`
            +++. (Default: True)

        Returns
        -------
        `str`: A formatted string of the debug trace
    """
    _traceback = ''.join(traceback.format_tb(err.__traceback__))
    error = ('```py\n{1}{0}: {2}\n```').format(type(err).__name__, _traceback, err)
    return error if advance else f"{type(err).__name__}: {err}"

def chunkify(to_chunk: str) -> list:
    """ Split up a long string into 1000 character substrings.

        Parameters
        ----------
        to_chunk: `str`
            The string to split up
        
        Returns
        -------
        `list`: A list containing the 'chunks' of strings capped
            at 1000 characters each
    """
    len_chunks = -(len(to_chunk) // -1000) # upside-down floor (ceiling)
    chunks = []
    for i in range(len_chunks):
        chunked_str = to_chunk[(1000 * i) : (1000 if i == 0 else 1000 * (i + 1))]
        chunks.append(chunked_str)
    return chunks

def extract_uuid(input_string: str) -> str | None:
    """ Extract the UUID from any string.

        Parameters
        ----------
        input_string: `str`
            A string that has a UUID.
        
        Returns
        -------
        `str`: The UUID or `None` if no UUID is found.
    """
    # Regular expression to match any version 4 UUID
    uuid_pattern = r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-4[0-9a-fA-F]{3}-[89abAB][0-9a-fA-F]{3}-[0-9a-fA-F]{12}"
    
    # Find the first matching UUID in the input string
    uuid_match = re.search(uuid_pattern, input_string)
    
    if uuid_match:
        return uuid.UUID(uuid_match.group())
    else:
        return None

def ceildiv(a: int, b: int) -> int:
    """ Upside-down floor division (ceiling).
    
        Parameters
        ----------
        a: `int`
            The dividend
        b: `int`
            The divisor
    """
    return -(a // -b)
