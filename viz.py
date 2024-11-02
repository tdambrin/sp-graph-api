from pathlib import Path
from typing import Union

import streamlit as st
import networkx as nx
from pyvis.network import Network
from jinja2 import Environment, FileSystemLoader

from commons import ThreadSafeSingleton
from config import PROJECT_ROOT, OUTPUT_DIR


def sample_graph():
    g = nx.Graph()  # or DiGraph, MultiGraph, MultiDiGraph, etc
    g.add_node(1)
    g.add_node("Hello")
    other_g = nx.Graph([(0, 1), (1, 2), (2, 0)])
    g.add_node(other_g)
    g.number_of_nodes()
    return g


class GraphVisualizer:

    def __init__(self, graph: nx.Graph = None, bg_color: str = "#ffffff", height: str = "1200px"):
        self.__graph = graph
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

    def set_singleton(self) -> str:
        return GraphVisualizerSingleton().set_graph(self)

    @staticmethod
    def show_example():
        g = Network()
        g.from_nx(nx.florentine_families_graph())
        g.show_buttons(filter_=["nodes"])
        g.show(str(OUTPUT_DIR / "example.html"), notebook=False)


class GraphVisualizerSingleton(metaclass=ThreadSafeSingleton):
    DEFAULT = '<strong>Enter search keywords to compute the graph </strong>'

    def __init__(self):
        self.__graph_as_html = GraphVisualizerSingleton.DEFAULT

    @property
    def graph_as_html(self):
        return self.__graph_as_html

    def reset_graph(self):
        self.__graph_as_html = GraphVisualizerSingleton.DEFAULT

    def set_loading(self):
        self.__graph_as_html = open(PROJECT_ROOT / "templates" / "loader.html").read()

    def set_graph(self, graph_visualizer: GraphVisualizer) -> str:
        self.__graph_as_html = graph_visualizer.html_str()
        return self.__graph_as_html


if __name__ == "__main__":
    GraphVisualizer.show_example()
