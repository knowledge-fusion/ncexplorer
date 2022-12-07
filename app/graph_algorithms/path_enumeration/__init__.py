import heapq
from itertools import chain

import networkx as nx

# input list of kg nodes, out put a graph with root nodes


def find_path(nodes, find_neighbors_callback):
    """

    :param nodes: list of WikidataEntity
    :return:
    """
    frontier_queues = []
    distance_matrix = nx.Graph()
    for idx, node in enumerate(nodes):
        queue = []
        distance_matrix.add_node(node)
        heapq.heappush(queue, (0, node))
        frontier_queues.append(queue)
    min_distance, node, distance_matrix = _path_enumeration(
        frontier_queues, distance_matrix, find_neighbors_callback
    )
    iteration = 0
    max_iteration = 200
    # check
    connected = nx.is_connected(distance_matrix)
    while (not connected) and iteration < max_iteration and min_distance < 2:
        iteration += 1
        min_distance, node, distance_matrix = _path_enumeration(
            frontier_queues, distance_matrix, find_neighbors_callback
        )
        connected = nx.is_connected(distance_matrix)
        print(f"iteration {iteration}, min_distance {min_distance}")

    print(f"terminate, connected? {connected}, last poped node is {node}")
    return connected, distance_matrix


def _path_enumeration(frontier_queues, distance_matrix, find_neightbors_callback):
    node_with_min_distance = None
    min_distance = 10  # max distance
    remaining_queues = [item for item in frontier_queues if item]
    if not remaining_queues:
        return min_distance, node_with_min_distance, distance_matrix
    min_distance = min(item[0][0] for item in remaining_queues)
    candidate_entities_to_pop = [
        frontier_queue[0][1]
        for frontier_queue in remaining_queues
        if frontier_queue[0][0] == min_distance
    ]
    heapq.heapify(candidate_entities_to_pop)
    candidate_to_pop = candidate_entities_to_pop[-1]
    for frontier_queue in remaining_queues:
        if frontier_queue and frontier_queue[0][1] == candidate_to_pop:
            min_distance, node_with_min_distance = heapq.heappop(frontier_queue)
            print(f"pop {node_with_min_distance}")
            break
    neighbors_dict = find_neightbors_callback(node_with_min_distance)
    for [neighbor, attributes] in neighbors_dict:
        if neighbor in [item[1] for item in frontier_queue]:  # check heapq
            distance = nx.shortest_path_length(
                distance_matrix, source=neighbor, target=node_with_min_distance
            )
            if distance > 1:
                distance_matrix.add_edge(
                    neighbor,
                    node_with_min_distance,
                    **attributes,
                )
        else:
            heapq.heappush(frontier_queue, (min_distance + 1, neighbor))
            distance_matrix.add_node(neighbor)
            distance_matrix.add_edge(neighbor, node_with_min_distance, **attributes)

    return min_distance, node_with_min_distance, distance_matrix
