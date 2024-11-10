from api_clients.wrappers import SpotifyWrapper
from config import OUTPUT_DIR
from items import ItemStore
from viz import GraphVisualizer

spotify = SpotifyWrapper()
graph_key = spotify.search(["khruangbin"],  max_depth=2)
# graph_key = spotify.search(["khruangbin"], initial_types=["album"], restricted_types=["album"],  max_depth=2)

graph = ItemStore().get_graph(graph_key)

# filename = input("Enter file name for graph html:")
GraphVisualizer(graph).save(OUTPUT_DIR / "khruangbin_v2.html")
print(graph.nodes)
