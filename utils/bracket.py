import math
import uuid
import random
import datetime
from typing import List, Optional
from dataclasses import dataclass


from models import (
    Claim,
    Vote,
    Battle,
    Match,
    Round,
    War,
)

@dataclass(kw_only=True)
class BracketTeam():
    user_id: Optional[str] = None
    name: Optional[str] = None
    ranking: Optional[int] = None

class Bracket():
    def __init__(
        self,
        war_id: str,
        bracket: List[Round] = list(),
        participants: List[BracketTeam] = list()
    ):
        self.war_id = war_id
        self.bracket = bracket
        self.participants = participants
        self.champion = None
        
        if self.bracket and self.participants:
            self.num_teams = len(self.participants)
            self.num_rounds = len(self.bracket)
    
    @classmethod
    def from_data(
        cls,
        bracket: List[dict],
        participants: List[dict]
    ):
        return cls(
            bracket=Round.schema().load(bracket, many=True),
            participants=BracketTeam.schema().load(participants, many=True)
        )

    def __str__(self):
        """ Returns a string representation of the Bracket object. """
        # create charmap as 2d array
        bracket_map = list()

        # get longest team name
        longest_name_len = len(max([x.name for x in self.participants], key=len)) + 2

        for n in range(self.num_rounds):
            round_num = n + 1 # 1-based round number

            # add blank list for column in map
            bracket_map.append(list())

            # determine number of characters for inter-round filler
            extra_char_len = 2**n

            # determine number of blank lines to place
            num_blank_lines = 2 * last_round_num_blank_lines + 1 if round_num > 1 else 1

            # get the number of matches in this round
            num_matches = self.get_num_matches_in_round(round_num)

            # add blanks before match in second round and onward
            for _ in range(2**n - 1):
                line_str = (" " * longest_name_len) + (" " * extra_char_len)
                bracket_map[n].append(line_str)

            for match_num in range(1, num_matches + 1):
                match_teams = self.get_match_teams(round_num, match_num)
                match_team_names = [t.name for t in match_teams]

                # add match teams and blank line
                for first_team_added, (team, endl) in enumerate(zip(match_team_names, [" ", "/"])):
                    if not team: team = '_'

                    # add team string
                    line_str = f"_{team :{'_'}<{longest_name_len-2}}_{endl}" + " " * (extra_char_len-1)
                    bracket_map[n].append(line_str)

                    # add blanks between team names and matches
                    for i in range(num_blank_lines):
                        if first_team_added:
                            line_str = (" " * longest_name_len) + (" " * extra_char_len)
                        else:
                            line_str = " " * longest_name_len
                            s = list(" " * extra_char_len)
                            if i < ((num_blank_lines + 1) / 2):
                                s[i] = "\\"
                            else:
                                j = int(((num_blank_lines + 1) / 2) - (i + 1))
                                s[j] = "/"
                            line_str += "".join(s)
                        bracket_map[n].append(line_str)

            # add blanks after match in second round and onward
            for _ in range(2**n - 1):
                line_str = (" " * longest_name_len) + (" " * extra_char_len)
                bracket_map[n].append(line_str)

            # save round number for future calculation
            last_round_num = round_num
            last_round_num_blank_lines = num_blank_lines
        
        # add the grand finals winner line after the last round
        if self.champion:
            team = self.champion.name
        else:
            team = "_"
        line_str = f"_{team :{'_'}<{longest_name_len-2}}_" + " " * extra_char_len
        bracket_map.append([" " * longest_name_len for _ in range(len(bracket_map[0]))])
        bracket_map[-1][(len(bracket_map[0]) // 2) - 1] = line_str

        bracket_str = ""
        for i in range(len(bracket_map[0]) - 1):
            bracket_str += "".join([x[i] for x in bracket_map])
            bracket_str += "\n"

        return bracket_str
    
    def add_team(self, name: str, user_id: str, ranking: int):
        """ Adds a team to the tournament with the given name and ranking. """
        self.participants.append(
            BracketTeam(
                user_id=user_id,
                name=name,
                ranking=ranking
            )
        )
        
    def create_bracket(self) -> None:
        """ Creates the tournament bracket based on the list of teams. """

        def gen_num_first_round_teams(n: int) -> int:
            """ Generates the number of teams in the first round given the number of teams in the bracket.

                Used to find the numbers of BYEs in the first round.
            """
            if n == 1: return 2
            else:      return 2 * gen_num_first_round_teams(n-1)

        def gen_optimal_seed_order(num_rounds) -> List[int]:
            """ Generates the bracket-optimal 1-based seed ordering for a bracket with num_rounds rounds.

                Optimal means that none of the top 2^p ranked players can meet earlier than the p-th from last round of the competition.
                See <a href="https://oeis.org/A208569">The Online Encyclopedia of Integer Sequences - A208569</a>
            """
            def t(L: int, k: int) -> int:
                if k == 1:
                    return 1
                m = (k - 1) & -(k - 1)
                return 1 + L // m - t(L, k - m)

            L = 2 ** num_rounds
            return [t(L, i + 1) for i in range(L)]

        # seed teams based on their ranking
        self.participants.sort(key=lambda x: x.ranking)

        # get number of teams
        self.num_teams = len(self.participants)

        # number of rounds in the bracket (assuming a standard knockout tournament)
        self.num_rounds = math.ceil(math.log(self.num_teams, 2))

        # fill missing first-round teams with byes
        num_byes = gen_num_first_round_teams(self.num_rounds) - self.num_teams
        for _ in range(num_byes):
            self.num_teams += 1
            self.participants.append(
                BracketTeam(
                    user_id="BYE",
                    name="BYE",
                    ranking=self.num_teams,
                )
            )

        # generate all of the matches in the entire bracket
        num_matches_in_round = self.num_teams // 2 
        first_round_seed_order = gen_optimal_seed_order(self.num_rounds)
        for round_num in range(self.num_rounds):
            round_uuid = uuid.uuid4()
            round = Round(
                id=round_uuid,
                war_id=self.war_id,
                message_id=None,
                number=round_num + 1,
                timestamp_start=None,
                timestamp_end=None
            )
            for match_num in range(num_matches_in_round):
                match_uuid = uuid.uuid4()
                if round_num == 0:
                    # first round should have each match filled
                    now = datetime.datetime.now(datetime.timezone.utc)
                    match = Match(
                        id=match_uuid,
                        round_id=round_uuid,
                        user_red_id=self.participants[first_round_seed_order[match_num * 2] - 1].user_id,
                        user_blue_id=self.participants[first_round_seed_order[match_num * 2 + 1] - 1].user_id,
                        winner_id=None,
                        number=match_num + 1,
                        timestamp_start=None,
                        timestamp_end=None
                    )
                    round.timestamp_start = now
                else:
                    # latter rounds should be empty initially
                    match = Match(
                        id=match_uuid,
                        round_id=round_uuid,
                        user_red_id=None,
                        user_blue_id=None,
                        winner_id=None,
                        number=match_num + 1,
                        timestamp_start=None,
                        timestamp_end=None
                    )
                r.db("wars").table("matches").insert(match.__dict__).run(conn)
            r.db("wars").table("rounds").insert(round.__dict__).run(conn)
            num_matches_in_round //= 2
            self.bracket.append(round)

    #---------------------------------
    #          ROUND METHODS
    #---------------------------------
    
    def get_round_message_id(self, round: Round) -> str | None:
        return r.db("wars") \
                .table("rounds") \
                .get(round.id) \
                .get_field("message_id") \
                .run(conn)
    
    def set_round_message_id(self, round: Round, message_id: str) -> None:
        r.db("wars") \
            .table("rounds") \
            .get(round.id) \
            .update({
                "message_id": message_id
            }) \
            .run(conn)
    
    def last_round(self, round: Round) -> bool:
        next_round_num = round.number + 1
        if next_round_num > self.get_num_rounds():
            return True
        return False

    def set_round_timestamp_end(self, round: Round) -> None:
        round.timestamp_end = datetime.datetime.now(datetime.timezone.utc)
        r.db("wars") \
            .table("rounds") \
            .get(round.id) \
            .update(round.__dict__) \
            .run(conn)
        
        if self.last_round(round):
            r.db("wars") \
                .table("core") \
                .get(self.war_id) \
                .update({
                    "timestamp_end": datetime.datetime.now(datetime.timezone.utc)
                }) \
                .run(conn)
            return

        next_round_num = round.number + 1
        result = r.db("wars") \
                    .table("rounds") \
                    .filter(
                        r.and_(
                            r.row["war_id"].eq(self.war_id),
                            r.row["number"].eq(next_round_num)
                        )
                    ) \
                    .nth(0) \
                    .run(conn)
        next_round = Round(**result)
        next_round.timestamp_start = datetime.datetime.now(datetime.timezone.utc)
        r.db("wars") \
            .table("rounds") \
            .get(next_round.id) \
            .update(next_round.__dict__) \
            .run(conn)

    def start_round_matches(self, round: Round) -> None:
        if not round.timestamp_start:
            round.timestamp_start = datetime.datetime.now(datetime.timezone.utc)
            r.db("wars") \
                .table("rounds") \
                .get(round.id) \
                .update(round.__dict__) \
                .run(conn)
        
        for match in self.get_round_matches(round):
            match.timestamp_start = datetime.datetime.now(datetime.timezone.utc)
            r.db("wars") \
                .table("matches") \
                .get(match.id) \
                .update(match.__dict__) \
                .run(conn)

    def get_current_round(self) -> Round:
        result = r.db("wars") \
                    .table("rounds") \
                    .filter(
                        r.and_(
                            r.row["war_id"].eq(self.war_id),
                            r.row["timestamp_start"],
                            r.not_(r.row["timestamp_end"])
                        )
                    ) \
                    .order_by("number") \
                    .nth(0) \
                    .run(conn)
        return Round(**result)
    
    def get_round_matches(self, round: Round) -> List[Match]:
        result = r.db("wars") \
                    .table("matches") \
                    .filter(
                        r.row["round_id"].eq(round.id),
                    ) \
                    .order_by("number") \
                    .run(conn)
        return [Match(**doc) for doc in result]
    
    def round_has_bye(self, round: Round) -> bool:
        return r.db("wars") \
                .table("matches") \
                .filter(
                    r.and_(
                        r.row["round_id"].eq(round.id),
                        r.row["user_blue_id"].eq("BYE")
                    )
                ) \
                .count() \
                .gt(0) \
                .run(conn)
    
    def get_num_ongoing_matches(self, round: Round) -> int:
        return r.db("wars") \
                .table("matches") \
                .filter(
                    r.and_(
                        r.row["round_id"].eq(round.id),
                        r.not_(r.row["winner_id"])
                    )
                ) \
                .count() \
                .run(conn)

    def get_num_rounds(self) -> int:
        return r.db("wars") \
                .table("rounds") \
                .filter(
                    r.row["war_id"].eq(self.war_id)
                ) \
                .count() \
                .run(conn)
    
    def get_round_participant_ids(self, round: Round) -> List[str]:
        ids = []
        for m in self.get_round_matches(round):
            ids.append(m.user_red_id)
            if m.user_blue_id != "BYE":
                ids.append(m.user_blue_id)
        return ids

    def round_finished(self, round: Round) -> bool:
        num_matches_in_round = len(self.get_round_matches(round))
        return r.db("wars") \
                    .table("matches") \
                    .filter(
                        r.row["round_id"].eq(round.id),
                    ) \
                    .has_fields("winner_id") \
                    .count() \
                    .eq(num_matches_in_round) \
                    .run(conn)

    #---------------------------------
    #          MATCH METHODS
    #---------------------------------
    
    def match_has_bye(self, match: Match) -> bool:
        return r.db("wars") \
                .table("matches") \
                .get(match.id) \
                .get_field("user_blue_id") \
                .eq("BYE") \
                .run(conn)

    def get_match_winner(self, match: Match) -> str | None:
        return r.db("wars") \
                .table("matches") \
                .get(match.id) \
                .get_field("winner_id") \
                .run(conn)

    def set_match_winner(self, match: Match, winner_id: str) -> None:
        # Update this match with the winner
        match.winner_id = winner_id
        match.timestamp_end = datetime.datetime.now(datetime.timezone.utc)
        r.db("wars") \
            .table("matches") \
            .get(match.id) \
            .update(match.__dict__) \
            .run(conn)
        
        # Get the next round and match
        round = self.get_current_round()
        next_round_num = round.number + 1
        next_match_num = match.number // 2 if match.number % 2 == 0 else (match.number + 1) // 2

        # Set the grand finals champion if we are in that round
        self.num_rounds = self.get_num_rounds()
        if next_round_num > self.num_rounds:
            self.champion = self.get_match_winner(match)
            return

        result = r.db("wars") \
                    .table("rounds") \
                    .filter(
                        r.and_(
                            r.row["war_id"].eq(self.war_id),
                            r.row["number"].eq(next_round_num)
                        )
                    ) \
                    .nth(0) \
                    .run(conn)
        next_round = Round(**result)

        result = r.db("wars") \
                    .table("matches") \
                    .filter(
                        r.and_(
                            r.row["round_id"].eq(next_round.id),
                            r.row["number"].eq(next_match_num)
                        )
                    ) \
                    .nth(0) \
                    .run(conn)
        next_match = Match(**result)

        # Update the next match with the winner of this one
        has_red_user = r.db("wars") \
                        .table("matches") \
                        .get(next_match.id) \
                        .has_fields("user_red_id") \
                        .run(conn)
        if not has_red_user:
            r.db("wars") \
                .table("matches") \
                .get(next_match.id) \
                .update({
                    "user_red_id": winner_id
                }) \
                .run(conn)
        else:
            r.db("wars") \
                .table("matches") \
                .get(next_match.id) \
                .update({
                    "user_blue_id": winner_id
                }) \
                .run(conn)
        
    #---------------------------------
    #         BATTLE METHODS
    #---------------------------------

    def get_battle_message_id(self, battle: Battle) -> str | None:
        return r.db("wars") \
                .table("battles") \
                .get(battle.id) \
                .get_field("message_id") \
                .run(conn)

    def set_battle_message_id(self, battle: Battle, message_id: str) -> None:
        r.db("wars") \
            .table("battles") \
            .get(battle.id) \
            .update({
                "message_id": message_id
            }) \
            .run(conn)

    def get_current_battle(self, match: Match) -> Battle | None:
        match_has_battles = r.db("wars") \
                                .table("battles") \
                                .filter(
                                    r.row["match_id"].eq(match.id)
                                ) \
                                .count() \
                                .gt(0) \
                                .run(conn)
        if not match_has_battles:
            return None
        
        result = r.db("wars") \
                    .table("battles") \
                    .filter(
                        r.row["match_id"].eq(match.id)
                    ) \
                    .order_by(r.desc("number")) \
                    .nth(0) \
                    .run(conn)
        return Battle(**result)

    def create_battle(self, match: Match, red_waifu: Claim, blue_waifu: Claim) -> Battle:
        current_battle = self.get_current_battle(match)
        if not current_battle:
            next_battle_num = 1
        else:
            next_battle_num = current_battle.number + 1
            current_battle.timestamp_end = datetime.datetime.now(datetime.timezone.utc)
            r.db("wars") \
                .table("battles") \
                .get(current_battle.id) \
                .update(current_battle.__dict__) \
                .run(conn)
        
        battle = Battle(
            id=r.uuid().run(conn),
            match_id=match.id,
            waifu_red_id=red_waifu.id,
            waifu_blue_id=blue_waifu.id,
            message_id=None,
            number=next_battle_num,
            timestamp_start=datetime.datetime.now(datetime.timezone.utc),
            timestamp_end=None
        )
        r.db("wars").table("battles").insert(battle.__dict__).run(conn)
        return battle

    def count_battle_votes(self, battle: Battle) -> dict:
        # Count the votes
        red_votes = r.db("wars") \
                        .table("votes") \
                        .filter(
                            r.and_(
                                r.row["battle_id"].eq(battle.id),
                                r.row["waifu_vote_id"].eq(battle.waifu_red_id)
                            )
                        ) \
                        .count() \
                        .run(conn)
        blue_votes = r.db("wars") \
                        .table("votes") \
                        .filter(
                            r.and_(
                                r.row["battle_id"].eq(battle.id),
                                r.row["waifu_vote_id"].eq(battle.waifu_blue_id)
                            )
                        ) \
                        .count() \
                        .run(conn)
        

        d = {
            "result": None,
            "winner": None,
            "loser": None
        }
        
        red_dict = {"id": battle.waifu_red_id, "count": red_votes}
        blue_dict = {"id": battle.waifu_blue_id, "count": blue_votes}
        if not red_votes and not blue_votes:
            # If no votes were recorded, pick a random winner
            d["result"] = "nil"
            d["winner"] = random.choice([red_dict, blue_dict])
            d["loser"] = red_dict if d["winner"] == blue_dict else blue_dict
        elif red_votes == blue_votes:
            # If a tie occurred, pick a random winner
            d["result"] = "tie"
            d["winner"] = random.choice([red_dict, blue_dict])
            d["loser"] = red_dict if d["winner"] == blue_dict else blue_dict
        elif red_votes > blue_votes:
            d["result"] = "red"
            d["winner"] = red_dict
            d["loser"] = blue_dict
        elif blue_votes > red_votes:
            d["result"] = "blue"
            d["winner"] = blue_dict
            d["loser"] = red_dict
        
        return d