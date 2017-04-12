from pygraphviz import AGraph
from hsmpy import HSM, State, FAILED


class Visualizer:

    def __init__(self, hsm):
        self.graph = AGraph(strict=False, directed=True, name=type(hsm).__name__)
        self._load_transitions(hsm)

    def _load_transitions(self, hsm, group=None):
        prefix = group + "." if group else ""
        nodes = []
        for t in hsm.transitions:

            # if origin is an HSM we have to connect from it's final node
            if issubclass(t["from"], HSM):
                u = prefix + t["from"].__name__ + ".FINAL"
            else:
                u = prefix + t["from"].__name__
            nodes.append(u)

            # if we connect to an HSM we must create a new substructure and load from the hsm recursively
            if issubclass(t["to"], HSM):
                sub = t["to"].__name__
                v = prefix + sub + "." + t["to"].init_state.__name__
                nodes.append(v)
                self._load_transitions(t["to"], group=sub)

            # there is always only one FAILED
            elif issubclass(t["to"], FAILED):
                v = FAILED.__name__
            else:
                v = prefix + t["to"].__name__
                nodes.append(v)
            # finally add it to the graph
            self.graph.add_edge(u, v, label=self._get_condition_string(t["condition"]))
        sg = self.graph.add_subgraph(nodes, name="cluster_" + prefix, style="dotted") #TODO not done here yet

    def _get_condition_string(self, cond):
        if isinstance(cond, dict):
            return str(list(cond.keys())[0].name) + ": " + str(list(cond.values())[0])
        elif callable(cond):
            return cond.__name__
        return cond.name

    def save_graph(self, filename):
        self.graph.layout(prog="dot")
        self.graph.draw(filename)


