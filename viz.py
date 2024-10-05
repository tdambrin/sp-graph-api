from pathlib import Path
from typing import Union

import networkx as nx
from pyvis.network import Network

from config import OUTPUT_DIR


def sample_graph():
    g = nx.Graph()  # or DiGraph, MultiGraph, MultiDiGraph, etc
    g.add_node(1)
    g.add_node("Hello")
    other_g = nx.Graph([(0, 1), (1, 2), (2, 0)])
    g.add_node(other_g)
    g.number_of_nodes()
    return g


class GraphVisualizer:

    def __init__(self, graph: nx.Graph = None):
        self.__graph = graph

    def save(self, path: Union[str, Path] = OUTPUT_DIR / "nx.html"):
        nt = Network()
        nt.from_nx(self.__graph)
        nt.show(path, notebook=False)

    @staticmethod
    def show_example():
        nx_graph = nx.cycle_graph(10)
        nx_graph.nodes[1]['title'] = 'Number 1'
        nx_graph.nodes[1]['group'] = 1
        nx_graph.nodes[3]['title'] = 'I belong to a different group!'
        nx_graph.nodes[3]['group'] = 10
        nx_graph.add_node(20, size=20, title='couple', group=2)
        nx_graph.add_node(21, size=15, title='couple', group=2)
        nx_graph.add_edge(20, 21, weight=5)
        nx_graph.add_node(25, size=25, label='lonely', title='lonely node', group=3)
        nt = Network('500px', '500px')
        # populates the nodes and edges data structures
        nt.from_nx(nx_graph)
        nt.show('nx.html', notebook=False)
        nx_graph.nodes[1]['title'] = 'Number 1'
        nx_graph.nodes[1]['group'] = 1
        nx_graph.nodes[3]['title'] = 'I belong to a different group!'
        nx_graph.nodes[3]['group'] = 10
        nx_graph.add_node(20, size=20, title='couple', group=2)
        nx_graph.add_node(21, size=15, title='couple', group=2)
        nx_graph.add_edge(20, 21, weight=5)
        nx_graph.add_node(25, size=25, label='lonely', title='lonely node', group=3)
        nt = Network('500px', '500px')
        # populates the nodes and edges data structures
        nt.from_nx(nx_graph)
        nt.show(OUTPUT_DIR / 'nx.html', notebook=False)


if __name__ == "__main__":
    GraphVisualizer().show_example()
