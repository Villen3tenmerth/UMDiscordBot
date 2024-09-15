from spreadsheets import SpreadsheetGameLogger
from utils import ROOT_DIR
import json
import os
import csv
from datetime import datetime


class StatsLoader:
    def __init__(self):
        self.last_update = datetime.min
        self.tables_path = os.path.join(ROOT_DIR, 'resources/AllTables.json')
        self.stats_path = os.path.join(ROOT_DIR, 'resources/stats.csv')
        self.UPDATE_TIME_SECONDS = 600

    def load_stats(self):
        cur_time = datetime.now()
        if (cur_time - self.last_update).total_seconds() < self.UPDATE_TIME_SECONDS:
            return self.stats_path

        self.last_update = cur_time
        with open(self.tables_path, 'r', encoding='utf-8') as fin:
            data = json.load(fin)

        stats = dict()
        for table in data['tables']:
            for sheet in table['sheets']:
                logger = SpreadsheetGameLogger(table['id'], sheet, None)
                results = logger.load_results(get_stats=True)
                for winner, loser in results:
                    flipped = False
                    if winner > loser:
                        flipped = True
                        winner, loser = loser, winner
                    key = (winner, loser)
                    if key not in stats:
                        stats[key] = [0, 0]
                    if flipped:
                        stats[key][1] += 1
                    else:
                        stats[key][0] += 1

        with open(self.stats_path, 'w',  newline='', encoding='utf-8') as fout:
            writer = csv.writer(fout, delimiter=',')
            for key, score in stats.items():
                writer.writerow([key[0], key[1], score[0], score[1]])
        return self.stats_path
