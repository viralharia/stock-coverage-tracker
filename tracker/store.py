"""JSON data store for tracked picks."""
import json
import os

DATA_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "picks.json"
)


def load():
    if not os.path.exists(DATA_PATH):
        return {"picks": []}
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def save(data):
    os.makedirs(os.path.dirname(DATA_PATH), exist_ok=True)
    tmp = DATA_PATH + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    os.replace(tmp, DATA_PATH)
