def get_neighbors(node):
    neighbors_map = {}
    neighbors_map[-1] = [[-1, {"length": 1}]]

    neighbors_map[0] = [[-1, {"length": 1}]]
    neighbors_map[1] = [[0, {"length": 1}]]
    neighbors_map[2] = [[0, {"length": 1}]]
    neighbors_map[3] = [[6, {"length": 1}]]
    neighbors_map[4] = [[7, {"length": 1}], [8, {"length": 1}]]
    neighbors_map[5] = [[0, {"length": 1}]]
    neighbors_map[10] = [[9, {"length": 1}]]
    neighbors_map[6] = [[0, {"length": 1}]]
    neighbors_map[7] = [[0, {"length": 1}]]
    neighbors_map[8] = [[0, {"length": 1}]]
    neighbors_map[9] = [[0, {"length": 1}]]
    res = neighbors_map[node]
    return res


def test_path_enumberation():
    leafs = [1, 2, 3, 4, 5, 10]
    from app.graph_algorithms.path_enumeration import find_path

    find_path(leafs, find_neighbors_callback=get_neighbors)


def test_connected_graph():
    import networkx as nx

    G = nx.Graph()
    G.add_node(1)
    G.add_node(2)

    is_connected = nx.is_connected(G)
    assert not is_connected

    G.add_node(0)
    G.add_edge(1, 0)
    is_connected = nx.is_connected(G)
    assert not is_connected

    G.add_edge(2, 0)
    is_connected = nx.is_connected(G)
    assert is_connected
