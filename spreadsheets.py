from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from threading import RLock
from datetime import datetime
from pytz import timezone


class SpreadsheetGameLogger:
    SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
    LOG_RANGE = 'Игры!A2:H'
    STANDINGS_RANGE = 'Текущее положение!A2:B'

    def __init__(self, spreadsheet_id):
        self.spreadsheet_id = spreadsheet_id
        self.creds = Credentials.from_service_account_file('resources/bot-key.json', scopes=self.SCOPES)
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
            sheet.values().append(spreadsheetId=self.spreadsheet_id, range=self.LOG_RANGE,
                                  valueInputOption="RAW", body=body).execute()

    def update_standings(self, standings):
        with self.lock:
            service = build('sheets', 'v4', credentials=self.creds)

            values = [[name, str(rank)] for name, rank in standings]
            body = {'values': values}

            sheet = service.spreadsheets()
            sheet.values().update(spreadsheetId=self.spreadsheet_id, range=self.STANDINGS_RANGE,
                                  valueInputOption="RAW", body=body).execute()

    def load_results(self):
        service = build('sheets', 'v4', credentials=self.creds)

        sheet = service.spreadsheets()
        response = sheet.values().get(spreadsheetId=self.spreadsheet_id, range=self.LOG_RANGE).execute()
        rows = response.get('values', [])

        return [[r[1], r[2]] for r in rows]
