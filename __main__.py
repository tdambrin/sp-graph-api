import items
from config import OUTPUT_DIR
from tasks import TaskManager
from viz import GraphVisualizer

selected_types = [
    items.ValidItem.TRACK.value,
    items.ValidItem.ALBUM.value,
    items.ValidItem.ARTIST.value,
]
keywords = input("Search what (space separated)")
keywords_ = keywords.split(" ")

ctrl = TaskManager(selected_types=selected_types)
result = ctrl.search_task(keywords=keywords_, save=True)
filename = OUTPUT_DIR / ("_".join(["main_result", *keywords, "0", "4"]) + ".html")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
with open(
    filename,
    "w",
) as f:
    f.write(
        GraphVisualizer(nodes=result.get("nodes"), edges=result.get("edges")).html_str()
    )

print(f"Saved search graph to {filename}")
