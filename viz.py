"""
Visualization only -> build PyVis graph
"""
from pathlib import Path
from typing import Any, Dict, List, Union

import networkx as nx
from jinja2 import Environment, FileSystemLoader
from pyvis.network import Network

import commons
from config import OUTPUT_DIR, PROJECT_ROOT


def sample_graph():
    g = nx.Graph()  # or DiGraph, MultiGraph, MultiDiGraph, etc
    g.add_node(1)
    g.add_node("Hello")
    other_g = nx.Graph([(0, 1), (1, 2), (2, 0)])
    g.add_node(other_g)
    g.number_of_nodes()
    return g


class GraphVisualizer:

    def __init__(
            self,
            graph: nx.Graph = None,
            nodes: List[Dict[str, Any]] = None,
            edges: List[Dict[str, Any]] = None,
            bg_color: str = "#ffffff",
            height: str = "1200px",
    ):
        """

        Args:
            graph: if provided, nodes and edges None
            nodes: if provided, graph None
            edges:  if provided, graph None
            bg_color: background for the graph
            height: height of the graph div
        """
        if graph is not None and (nodes is not None or edges is not None):
            raise ValueError(
                "[viz.GraphVisualizer.__init__] graph and (nodes and/or edges) both provided."
            )

        if graph:
            self.__graph = graph
        else:
            assert nodes is not None
            self.__graph = commons.di_graph_from_list_of_dict(
                nodes=nodes,
                edges=edges,
            )

        self.__network = Network(bgcolor=bg_color, height=height, width="100%",)
        self.__network.from_nx(self.__graph)

        # set physics options
        self.__network.force_atlas_2based()

        # set interaction options
        self.__network.options.interaction.zoomSpeed = .5
        self.__network.options.interaction.hover = True

        # temp fix until pyvis href support
        self.__network.templateEnv = Environment(loader=FileSystemLoader(PROJECT_ROOT / "templates"))

    def save(self, path: Union[str, Path] = OUTPUT_DIR / "tmp.html"):
        self.__network.show(path, notebook=False)

    def html_str(self) -> str:
        html_str = self.__network.generate_html(notebook=False)
        return html_str

    @staticmethod
    def show_example():
        g = Network()
        g.from_nx(nx.florentine_families_graph())
        g.show_buttons(filter_=["nodes"])
        g.show(str(OUTPUT_DIR / "example.html"), notebook=False)


if __name__ == "__main__":
    GraphVisualizer.show_example()
