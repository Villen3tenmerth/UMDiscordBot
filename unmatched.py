import Levenshtein as lev
import json
import os
from rating import *
from spreadsheets import SpreadsheetGameLogger
from utils import ROOT_DIR


class UMException(Exception):
    pass


def search(name, items):
    name = ''.join(name.lower().split())
    res = ''
    dist = 10 ** 9
    for item in items:
        for alias in item["aliases"] + [item["name"]]:
            new_dist = lev.distance(name, ''.join(alias.lower().split()))
            if new_dist < dist:
                dist = new_dist
                res = item["name"]
    return res


class Roster:
    def __init__(self):
        path = os.path.join(ROOT_DIR, 'resources/roster.json')
        with open(path, 'r', encoding='utf-8') as fin:
            data = json.load(fin)
        self.characters = data['characters']
        self.boards = data['boards']

    def parse_character(self, name):
        return search(name, self.characters)

    def parse_board(self, name):
        return search(name, self.boards)


ROSTER = Roster()


class Match:
    def __init__(self, winner, loser, win_char, lose_char, board, winner_first):
        self.winner = winner
        self.loser = loser
        self.winner_character = ROSTER.parse_character(win_char)
        self.loser_character = ROSTER.parse_character(lose_char)
        self.board = ROSTER.parse_board(board)
        self.winner_first = winner_first


class Tournament:
    def __init__(self):
        self.lock = RLock()
        self.name = ""
        self.characters = []
        self.boards = []
        self.rating = None
        self.standings = {}
        self.logger = None
        self.dummy = ""

    def __load_state(self):
        matches = self.logger.load_results()
        for winner, loser in matches:
            if winner not in self.standings:
                self.standings[winner] = self.rating.default_rank()
            if loser not in self.standings:
                self.standings[loser] = self.rating.default_rank()

            w_rank = self.standings[winner]
            l_rank = self.standings[loser]
            new_w_rank, new_l_rank = self.rating.update_rank(w_rank, l_rank)
            self.standings[winner] = new_w_rank
            self.standings[loser] = new_l_rank

    def start(self, name):
        self.name = name
        with self.lock:
            cfg_file = os.path.join(ROOT_DIR, "resources/" + name + ".json")
            if not os.path.isfile(cfg_file):
                raise UMException("Tournament config file not found")
            with open(cfg_file, "r", encoding='utf-8') as fin:
                cfg = json.load(fin)

            if "characters" not in cfg:
                raise UMException("Missing character list")
            if cfg["characters"] == 'all':
                self.characters = [x.name for x in ROSTER.characters]
            else:
                self.characters = [ROSTER.parse_character(x) for x in cfg["characters"]]

            if "boards" not in cfg:
                raise UMException("Missing boards list")
            if cfg["boards"] == 'all':
                self.boards = [x["name"] for x in ROSTER.boards]
            else:
                self.boards = [ROSTER.parse_board(x) for x in cfg["boards"]]

            if "rating" not in cfg:
                self.rating = EmptyRankManager()
            elif cfg["rating"] == "counter":
                self.rating = CounterRankManager()
            elif cfg["rating"] == "ladder":
                self.rating = LadderRankManager()
            else:
                raise UMException("Unknown rating type: " + str(cfg["rating"]))
            self.dummy = self.rating.default_rank()

            if "spreadsheet_id" not in cfg:
                raise UMException("Missing spreadsheet_id")
            if "log_sheet" not in cfg:
                raise UMException("Missing log_sheet name")
            standings_sheet = None
            if "standings_sheet" in cfg:
                standings_sheet = cfg["standings_sheet"]
            self.logger = SpreadsheetGameLogger(cfg["spreadsheet_id"], cfg["log_sheet"], standings_sheet)
            self.__load_state()

    def report_match(self, match):
        if match.winner_character not in self.characters:
            raise UMException("Forbidden character: " + match.winner_character)
        if match.loser_character not in self.characters:
            raise UMException("Forbidden character: " + match.loser_character)
        if match.board not in self.boards:
            raise UMException("Forbidden board: " + match.board)

        if match.winner not in self.standings:
            self.standings[match.winner] = self.rating.default_rank()
        if match.loser not in self.standings:
            self.standings[match.loser] = self.rating.default_rank()

        is_rated = True
        w_rank = self.standings[match.winner]
        l_rank = self.standings[match.loser]
        new_w_rank, new_l_rank = self.rating.update_rank(w_rank, l_rank)
        if self.rating.to_number(w_rank) == self.rating.to_number(new_w_rank) and \
                self.rating.to_number(l_rank) == self.rating.to_number(new_l_rank):
            is_rated = False
        self.standings[match.winner] = new_w_rank
        self.standings[match.loser] = new_l_rank

        self.logger.log_match(match, is_rated)
        stand = sorted(list(self.standings.items()), key=lambda x: self.rating.to_number(x[1]), reverse=True)
        self.logger.update_standings(stand)

    def get_rank(self, player):
        if player in self.standings:
            return str(self.standings[player])
        else:
            return str(self.dummy)

    def check_game(self, winner, loser):
        w_rank = self.standings.get(winner, self.dummy)
        l_rank = self.standings.get(loser, self.dummy)
        r1, r2 = self.rating.update_rank(w_rank, l_rank)
        return str(r1), str(r2)

    def get_winners(self):
        stand = sorted(list(self.standings.items()), key=lambda x: self.rating.to_number(x[1]), reverse=True)
        res = []
        for player, rank in stand:
            if self.rating.to_number(rank) == self.rating.to_number(stand[0][1]):
                res.append(player)
            else:
                break
        return res
