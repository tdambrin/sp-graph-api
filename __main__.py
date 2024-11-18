import json

import items
from config import OUTPUT_DIR
from tasks import TaskManager

selected_types = [
    items.ValidItem.TRACK.value,
    items.ValidItem.ALBUM.value,
    items.ValidItem.ARTIST.value,
]
keywords = input("Search what (space separated)")
keywords_ = keywords.split(" ")

ctrl = TaskManager(session_id="my_uuid", selected_types=selected_types)
result = ctrl.search_task(keywords=keywords_, save=True)
filename = OUTPUT_DIR / ("_".join(["search", *keywords, "0", "4"]) + ".json")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
with open(filename, "w", encoding="utf-8") as f:
    json.dump(result, f)

print(f"Saved search results to {filename}")
