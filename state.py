import json
import os
from utils import ROOT_DIR

STATE_FILE = os.path.join(ROOT_DIR, 'resources/state.json')


def dump_state(tournaments):
    data = []
    for channel in tournaments:
        tour = tournaments[channel]
        data.append((channel.id, tour.name))
    with open(STATE_FILE, 'w') as fstate:
        json.dump(data, fstate)


def load_state():
    data = []
    try:
        with open(STATE_FILE, 'r') as fstate:
            data = json.load(fstate)
    except:
        pass
    return data
