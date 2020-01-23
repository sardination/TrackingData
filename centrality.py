import formations
import OPTA as opta
import OPTA_weighted_networks as onet

from itertools import combinations
import networkx as nx
import numpy as np


def current_flow_betweenness_directed(graph, start_node=None):
    """
    Calculates current-based (node) betweenness for a directed graph

    Args:
        graph (nx.DiGraph): graph with weights defined in 'weight' attr
    """

    nodes = list(graph.nodes())
    if start_node is not None:
        nodes.remove(start_node)
        nodes.insert(0,start_node)
    edges = list(graph.edges())

    n = len(nodes)

    betweennesses = {p_id: 0 for p_id in nodes}

    A = np.array([[graph[v][w]['weight'] if (v != w and (v,w) in edges) else 0 for v in nodes] for w in nodes])
    L = np.diag(np.sum(A, axis=1)) - A
    L_tilde = L[1:,1:]
    L_tilde_inverse = np.linalg.inv(L_tilde)
    C = np.zeros((n, n))
    C[1:,1:] = L_tilde_inverse

    throughputs = {s: {t: {v: 0 for v in nodes} for t in nodes} for s in nodes}
    # currents = {s: {t: {e: 0 for e in edges} for t in nodes} for s in nodes}

    for s_index, s in enumerate(nodes):
        for t_index, t in enumerate(nodes):
            if s == t:
                continue

            b = np.zeros((n, 1))
            b[s_index][0] = 1
            b[t_index][0] = -1

            p = C @ b

            currents = {e: 0 for e in edges}

            for e in edges:
                v, w = e
                v_index = nodes.index(v)
                w_index = nodes.index(w)

                # currents[s][t][e] = (p[v_index][0] - p[w_index][0]) * graph[v][w]['weight']
                currents[e] = (p[v_index][0] - p[w_index][0]) * graph[v][w]['weight']

            for v_index, v in enumerate(nodes):
                # throughputs[s][t][v] = 0.5 * (-abs(b[v_index][0]) + sum([abs(currents[s][t][e]) for e in edges if v in e]))
                throughputs[s][t][v] = 0.5 * (-abs(b[v_index][0]) + sum([abs(currents[e]) for e in edges if v in e]))

    for v in nodes:
        betweennesses[v] = (1.0 / ((n - 1) * (n - 2))) * sum([throughputs[s][t][v] for s in nodes for t in nodes])

    return betweennesses


def current_flow_edge_betweenness_directed(graph, start_node=None):
    """
    Calculates current-based (edge) betweenness for a directed graph

    Args:
        graph (nx.DiGraph): graph with weights defined in 'weight' attr
    """

    nodes = list(graph.nodes())
    if start_node is not None:
        nodes.remove(start_node)
        nodes.insert(0,start_node)
    edges = list(graph.edges())

    n = len(nodes)
    m = len(edges)

    betweennesses = {e: 0 for e in edges}

    A = np.array([[graph[v][w]['weight'] if (v != w and (v,w) in edges) else 0 for v in nodes] for w in nodes])
    L = np.diag(np.sum(A, axis=1)) - A
    L_tilde = L[1:,1:]
    L_tilde_inverse = np.linalg.inv(L_tilde)
    C = np.zeros((n, n))
    C[1:,1:] = L_tilde_inverse

    throughputs = {s: {t: {e: 0 for e in edges} for t in nodes} for s in nodes}

    for s_index, s in enumerate(nodes):
        for t_index, t in enumerate(nodes):
            if s == t:
                continue

            b = np.zeros((n, 1))
            b[s_index][0] = 1
            b[t_index][0] = -1

            p = C @ b

            for e in edges:
                v, w = e
                v_index = nodes.index(v)
                w_index = nodes.index(w)

                throughputs[s][t][e] = abs((p[v_index][0] - p[w_index][0]) * graph[v][w]['weight'])

    for e in edges:
        betweennesses[e] = (1.0 / ((m - 1) * (m - 2))) * sum([throughputs[s][t][e] for s in nodes for t in nodes])

    return betweennesses


def current_flow_closeness_directed(graph, start_node=None):
    """
    Calculates current-based closeness for a directed graph

    Args:
        graph (nx.DiGraph): graph with weights defined in 'weight' attr
    """

    nodes = list(graph.nodes())
    if start_node is not None:
        nodes.remove(start_node)
        nodes.insert(0,start_node)
    edges = list(graph.edges())

    n = len(nodes)

    closenesses = {v: 0 for v in nodes}

    A = np.array([[graph[v][w]['weight'] if (v != w and (v,w) in edges) else 0 for v in nodes] for w in nodes])
    L = np.diag(np.sum(A, axis=1)) - A
    L_tilde = L[1:,1:]
    L_tilde_inverse = np.linalg.inv(L_tilde)
    C = np.zeros((n, n))
    C[1:,1:] = L_tilde_inverse

    for s_index, s in enumerate(nodes):
        p_sum = 0
        for t_index, t in enumerate(nodes):
            if s == t:
                continue

            b = np.zeros((n, 1))
            b[s_index][0] = 1
            b[t_index][0] = -1

            p = C @ b

            p_sum += p[s_index][0] - p[t_index][0]

        closenesses[s] = 1.0 / p_sum

    return closenesses


fpath = "../Copenhagen/"
all_copenhagen_match_ids = [
    984459,
    984463,
    984468,
    984478,
    984486,
    984496,
    984507,
    984514,
    984517,
    984528,
    984533,
    984542,
    984548,
    984552,
    984558,
    984567,
    984574,
    984581,
    984591,
    984596,
    984606,
    984612,
    984615,
    984625,
    984634
]
copenhagen_team_id = 569


copenhagen_formations = formations.read_formations_from_csv('../copenhagen_formations.csv')

all_copenhagen_match_ids = [984567]

for formation in copenhagen_formations:
    match_id = formation.match_id

    if match_id not in all_copenhagen_match_ids:
        continue

    fname = str(match_id)
    match_OPTA = opta.read_OPTA_f7(fpath, fname)
    match_OPTA = opta.read_OPTA_f24(fpath, fname, match_OPTA)

    home_or_away = "home"
    home_team = onet.get_team(match_OPTA, team="home")
    away_team = onet.get_team(match_OPTA, team="away")
    if home_team.team_id != copenhagen_team_id:
        home_or_away = "away"

    team_object = onet.get_team(match_OPTA, team=home_or_away)
    formation.add_team_object(team_object)
    formation.add_goalkeeper()

    substitution_events = [e for e in team_object.events if e.is_substitution]

    player_times = team_object.get_on_pitch_periods()

###
    # TODO: allow for resettable formations (pd 2 should have the subs from pd 1 pre-substituted)
    # for period in [0,1,2]:
    for period in [0]:
        pass_map = onet.get_all_pass_destinations(match_OPTA, team=home_or_away, exclude_subs=False, half=period)
        # TODO: ^^ fix connectedness by using substitutes for the appropriate players within the formation
        # graph = formation.get_formation_graph(pass_map=pass_map, directed=True)

        total_player_times = {p_id: 0 for p_id in pass_map.keys()}
        for p_id in pass_map.keys():
            time_list = player_times[p_id]
            for time_dict in time_list:
                if period == 0 or time_dict['period'] == period:
                    total_player_times[p_id] += time_dict['end'] - time_dict['start']

        total_pair_times = {p_id: {r_id: 0 for r_id in pass_map.keys()} for p_id in pass_map.keys()}
        for p_id, r_id in combinations(pass_map.keys(), 2):
            p_time_list = player_times[p_id]
            r_time_list = player_times[r_id]
            for p_time_dict in p_time_list:
                for r_time_dict in r_time_list:
                    if p_time_dict['period'] != r_time_dict['period']:
                        continue
                    overlap_start = max(p_time_dict['start'], r_time_dict['start'])
                    overlap_end = min(p_time_dict['end'], r_time_dict['end'])

                    total_pair_times[p_id][r_id] += overlap_end - overlap_start
                    total_pair_times[r_id][p_id] += overlap_end - overlap_start


        max_played_time = max(total_player_times.values())

        # create a directed graph
        graph = nx.DiGraph()
        mapped_players = pass_map.keys()
        for p_id in mapped_players:
            for r_id in mapped_players:
                if pass_map[p_id][r_id]["num_passes"] == 0:
                    continue
                # graph.add_edge(p_id, r_id, weight=pass_map[p_id][r_id]["num_passes"])
                graph.add_edge(
                    p_id,
                    r_id,
                    weight=pass_map[p_id][r_id]["num_passes"] * (total_pair_times[p_id][r_id]) / max_played_time
                )

        # ball_in_node = 0
        # while ball_in_node in graph.nodes():
        #     ball_in_node += 1
        # graph.add_edge(ball_in_node, formation.goalkeeper, weight=1)

        period_subs = [e for e in substitution_events if (e.period_id == period or period == 0)]
        on_player = None
        off_player = None
        for e in period_subs:
            if e.sub_direction == "on":
                on_player = e.player_id
            elif e.sub_direction == "off":
                off_player = e.player_id

            if on_player is not None and off_player is not None:
                formation.add_substitute(off_player, on_player)
                print("sub {} for {}".format(on_player, off_player))
                on_player = None
                off_player = None

        betweenness = current_flow_betweenness_directed(graph, start_node=formation.goalkeeper)
        print("BETWEENNESS")
        for key, value in sorted(betweenness.items(), key=lambda t:-t[1]):
            print("{}: {}".format(key, value))

        print()

        edge_betweenness = current_flow_edge_betweenness_directed(graph, start_node=formation.goalkeeper)
        print("EDGE BETWEENNESS")
        for key, value in sorted(edge_betweenness.items(), key=lambda t:-t[1]):
            print("{} -- {} --> {}: {}".format(key[0], pass_map[key[0]][key[1]]['num_passes'], key[1], value))

        print()

        closenesses = current_flow_closeness_directed(graph, start_node=formation.goalkeeper)
        print("CLOSENESS")
        for key, value in sorted(closenesses.items(), key=lambda t:-t[1]):
            print("{}: {}".format(key, value))

        formation.get_formation_graph(pass_map)
###

