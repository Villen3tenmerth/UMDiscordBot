from enum import Enum
from threading import RLock


class EmptyRankManager:
    def default_rank(self):
        return ""

    def update_rank(self, w_rank, l_rank):
        return "", ""

    def to_number(self, rank):
        return 0


class CounterRankManager:
    def default_rank(self):
        return 0

    def update_rank(self, w_rank, l_rank):
        return w_rank + 1, l_rank

    def to_number(self, rank):
        return rank


LadderRankType = Enum('RankType', ['BRONZE', 'SILVER', 'GOLD', 'DIAMOND', 'HERO'])


class LadderRank:
    max_rank = {LadderRankType.BRONZE: 2,
                LadderRankType.SILVER: 3,
                LadderRankType.GOLD: 4,
                LadderRankType.DIAMOND: 5,
                LadderRankType.HERO: -1}

    def __init__(self, rank_type, value, id):
        self.type = rank_type
        self.value = value
        self.id = id
        self.last_opp = 0
        self.streak = 0

    def __str__(self):
        return self.type.name + ' ' + str(self.value)

    def copy(self):
        res = LadderRank(self.type, self.value, self.id)
        res.last_opp = self.last_opp
        res.streak = self.streak
        return res

    def next_rank(self):
        res = self.copy()
        if self.value == self.max_rank[self.type]:
            res.type = LadderRankType(self.type.value + 1)
            res.value = 0
        else:
            res.value += 1
        return res

    def prev_rank(self):
        res = self.copy()
        if self.value != 0:
            res.value -= 1
        return res


class LadderRankManager:
    def __init__(self):
        self.lock = RLock()
        self.last_id = 0

    def default_rank(self):
        with self.lock:
            self.last_id += 1
            return LadderRank(LadderRankType.BRONZE, 0, self.last_id)

    def update_rank(self, w_rank, l_rank):
        new_w_rank = w_rank.copy()
        new_l_rank = l_rank.copy()

        if w_rank.last_opp == l_rank.id:
            new_w_rank.streak += 1
        else:
            new_w_rank.streak = 1
        new_w_rank.last_opp = l_rank.id
        if l_rank.last_opp == w_rank.id:
            new_l_rank.streak += 1
        else:
            new_l_rank.streak = 1
        new_l_rank.last_opp = w_rank.id

        if new_w_rank.streak > 3 and new_l_rank.streak > 3:
            return new_w_rank, new_l_rank

        diff = abs(w_rank.type.value - l_rank.type.value)
        if diff > 1:
            return new_w_rank, new_l_rank

        return new_w_rank.next_rank(), new_l_rank.prev_rank()

    def to_number(self, rank):
        return rank.type.value * 10 + rank.value
