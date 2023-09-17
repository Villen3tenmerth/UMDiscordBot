from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from threading import RLock
from datetime import datetime
from pytz import timezone
from utils import ROOT_DIR
import os


class SpreadsheetGameLogger:
    SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
    LOG_CELLS = '!A2:H'
    STANDINGS_CELLS = '!A2:B'

    def __init__(self, spreadsheet_id, log_name, standings_name):
        self.spreadsheet_id = spreadsheet_id
        self.log_range = log_name + self.LOG_CELLS
        self.use_standings = False
        if standings_name is not None:
            self.use_standings = True
            self.standings_range = standings_name + self.STANDINGS_CELLS
        cred_path = os.path.join(ROOT_DIR, 'resources/bot-key.json')
        self.creds = Credentials.from_service_account_file(cred_path, scopes=self.SCOPES)
        self.lock = RLock()

    def log_match(self, match, is_rated):
        with self.lock:
            service = build('sheets', 'v4', credentials=self.creds)

            tz = timezone('Europe/Moscow')
            values = [[datetime.now(tz).strftime("%d.%m.%Y %H:%M:%S"),
                       match.winner,
                       match.loser,
                       match.winner_character,
                       match.loser_character,
                       match.board,
                       "Победитель" if match.winner_first else "Проигравший",
                       "+" if is_rated else "-"]]
            body = {'values': values}

            sheet = service.spreadsheets()
            sheet.values().append(spreadsheetId=self.spreadsheet_id, range=self.log_range,
                                  valueInputOption="RAW", body=body).execute()

    def update_standings(self, standings):
        if not self.use_standings:
            return
        with self.lock:
            service = build('sheets', 'v4', credentials=self.creds)

            values = [[name, str(rank)] for name, rank in standings]
            body = {'values': values}

            sheet = service.spreadsheets()
            sheet.values().update(spreadsheetId=self.spreadsheet_id, range=self.standings_range,
                                  valueInputOption="RAW", body=body).execute()

    def load_results(self):
        service = build('sheets', 'v4', credentials=self.creds)

        sheet = service.spreadsheets()
        response = sheet.values().get(spreadsheetId=self.spreadsheet_id, range=self.log_range).execute()
        rows = response.get('values', [])

        return [[r[1], r[2]] for r in rows]
