from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4

from disnake import GuildScheduledEventStatus
from pydantic import Field
from beanie import Document


class Vote(Document):
    class Settings:
        name = "votes"

    id: UUID = Field(default_factory=uuid4)
    battle_id: UUID = Field(default_factory=uuid4)
    waifu_vote_id: UUID = Field(default_factory=uuid4)
    # discord uuid's
    user_id: int
    # other
    timestamp: datetime


class Battle(Document):
    class Settings:
        name = "battles"

    id: UUID = Field(default_factory=uuid4)
    match_id: UUID = Field(default_factory=uuid4)
    waifu_red_id: UUID = Field(default_factory=uuid4)
    waifu_blue_id: UUID = Field(default_factory=uuid4)
    # discord uuid's
    message_id: Optional[int] = None
    # other
    number: int
    timestamp_start: Optional[datetime] = None
    timestamp_end: Optional[datetime] = None


class Match(Document):
    class Settings:
        name = "matches"
    
    id: UUID = Field(default_factory=uuid4)
    round_id: UUID = Field(default_factory=uuid4)
    # discord uuid's
    user_red_id: int
    user_blue_id: int
    winner_id: Optional[int] = None
    # other
    number: int
    timestamp_start: Optional[datetime] = None
    timestamp_end: Optional[datetime] = None


class Round(Document):
    class Settings:
        name = "rounds"
    
    id: UUID = Field(default_factory=uuid4)
    war_id: UUID = Field(default_factory=uuid4)
    # discord uuid's
    message_id: Optional[int] = None
    # other
    number: int
    timestamp_start: Optional[datetime] = None
    timestamp_end: Optional[datetime] = None


class Event(Document):
    class Settings:
        name = "events"
    
    id: UUID = Field(default_factory=uuid4)
    # discord uuid's
    event_id: int
    guild_id: int
    # other
    state: int
    timestamp_start: Optional[datetime] = None
    timestamp_end: Optional[datetime] = None
