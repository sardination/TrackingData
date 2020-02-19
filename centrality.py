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


def get_directed_graphs(pass_map, player_times, team_object, role_grouped=False, period=0):
    graphs = {}

    for g_type in ['graph', 'inverse_graph', 'scaled_graph', 'inverse_scaled_graph']:
        graphs[g_type] = nx.DiGraph()

    # Find total on-pitch times for weight scaling
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

    # TOGGLE: use role-grouped graph instead of player-separated graph
    if role_grouped:
        role_mappings, pass_map = onet.convert_pass_map_to_roles(team_object, pass_map)
        new_total_pair_times = {p_r_id: {r_r_id: 0 for r_r_id in range(1, 12)} for p_r_id in range(1,12)}
        for p_id, p_role_id in role_mappings.items():
            if p_id not in total_pair_times.keys():
                continue
            for r_id, r_role_id in role_mappings.items():
                if r_id not in total_pair_times.keys():
                    continue
                new_total_pair_times[p_role_id][r_role_id] += total_pair_times[p_id][r_id]
        total_pair_times = new_total_pair_times
    # _, pass_map = onet.convert_pass_map_to_roles(team_object, pass_map)
    # _, opposing_pass_map = onet.convert_pass_map_to_roles(opposing_team_object, opposing_pass_map)

    # Create graphs
    mapped_players = pass_map.keys()
    for p_id in mapped_players:
        for r_id in mapped_players:
            if pass_map[p_id][r_id]["num_passes"] == 0:
                continue
            graphs['graph'].add_edge(p_id, r_id, weight=pass_map[p_id][r_id]["num_passes"])
            graphs['inverse_graph'].add_edge(
                p_id,
                r_id,
                weight=1.0/pass_map[p_id][r_id]["num_passes"]
            )
            graphs['scaled_graph'].add_edge(
                p_id,
                r_id,
                weight=pass_map[p_id][r_id]["num_passes"] * (total_pair_times[p_id][r_id]) / max_played_time
            )
            graphs['inverse_scaled_graph'].add_edge(
                p_id,
                r_id,
                weight=((total_pair_times[p_id][r_id]) / max_played_time) / pass_map[p_id][r_id]["num_passes"]
            )

    return graphs

if __name__ == "__main__":

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


    copenhagen_formations = formations.read_formations_from_csv('../copenhagen_formations.csv', copenhagen_team_id)
    copenhagen_formations = {formation.match_id: formation for formation in copenhagen_formations}
    # opposing_formations = []

    # all_copenhagen_match_ids = [984463]
    all_copenhagen_match_ids = [984574, 984459]

    # for formation in copenhagen_formations:
    #     match_id = formation.match_id

    #     if match_id not in all_copenhagen_match_ids:
    #         continue
    for match_id in all_copenhagen_match_ids:
        formation = copenhagen_formations[match_id]

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

        # Get opposing team info
        opposite_side = "home" if home_or_away == "away" else "away"
        opposing_team_object = onet.get_team(match_OPTA, team=opposite_side)

        substitution_events = [e for e in team_object.events if e.is_substitution]
        opp_substitution_events = [e for e in opposing_team_object.events if e.is_substitution]

        player_times = team_object.get_on_pitch_periods()
        opp_player_times = opposing_team_object.get_on_pitch_periods()

    ###
        original_formation = formation
        for period in [0,1,2]:
            formation = formations.copy_formation(original_formation)
            pass_map = onet.get_all_pass_destinations(match_OPTA, team=home_or_away, exclude_subs=False, half=period)

            # Create opposing team formation
            opposing_player_positions = opposing_team_object.get_player_positions(period=(1 if period == 0 else period))
            opposing_player_positions = sorted(opposing_player_positions.items(), key=lambda t:t[1])
            opposing_player_positions = [p_id for p_id, pos in opposing_player_positions if pos != 0]
            opposing_formation = formations.Formation(
                match_id,
                opposing_team_object.team_id,
                formation.opp_formation_1 if period in [0,1] else formation.opp_formation_2,
                formation.formation_id,
                None,
                player_positions=opposing_player_positions
            )
            opposing_formation.add_team_object(opposing_team_object)
            opposing_formation.add_goalkeeper(opposing_player_positions[0])

            opposing_pass_map = onet.get_all_pass_destinations(match_OPTA, team=opposite_side, exclude_subs=False, half=period)

            # Add in substitutes to formations
            period_subs = [e for e in substitution_events if (e.period_id <= period or period == 0)]
            opp_period_subs = [e for e in opp_substitution_events if (e.period_id <= period or period == 0)]

            for team_period_subs, team_formation in [(period_subs, formation), (opp_period_subs, opposing_formation)]:
                on_player = None
                off_player = None
                for e in team_period_subs:
                    if e.sub_direction == "on":
                        on_player = e.player_id
                    elif e.sub_direction == "off":
                        off_player = e.player_id

                    if on_player is not None and off_player is not None:
                        team_formation.add_substitute(off_player, on_player, replace=(e.period_id < period))
                        print("team {}: sub {} for {} in period {}".format(
                            team_formation.team_id,
                            on_player,
                            off_player,
                            e.period_id
                        ))
                        on_player = None
                        off_player = None

            # create a directed graph
            role_grouped = False ### TOGGLE ###
            graphs = get_directed_graphs(
                pass_map,
                player_times,
                team_object,
                role_grouped=role_grouped,
                period=period
            )
            opposing_graphs = get_directed_graphs(
                opposing_pass_map,
                opp_player_times,
                opposing_team_object,
                role_grouped=role_grouped,
                period=period
            )

            goalkeeper_node = formation.goalkeeper
            opp_goalkeeper_node = opposing_formation.goalkeeper
            original_pass_map = pass_map
            original_opposing_pass_map = opposing_pass_map
            if role_grouped:
                goalkeeper_node = 1
                opp_goalkeeper_node = 1
                _, pass_map = onet.convert_pass_map_to_roles(team_object, pass_map)
                _, opposing_pass_map = onet.convert_pass_map_to_roles(opposing_team_object, opposing_pass_map)

            # Centrality measures
            betweenness = current_flow_betweenness_directed(
                graphs['scaled_graph'],
                start_node=goalkeeper_node
            )
            # opp_betweenness = current_flow_betweenness_directed(
            #     opposing_graphs['scaled_graph'],
            #     start_node=opp_goalkeeper_node
            # )
            # print("BETWEENNESS")
            # # for key, value in sorted(betweenness.items(), key=lambda t:-t[1]):
            # #     print("{}: {}".format(key, value))
            # for (k, v), (ok, ov) in zip(
            #     sorted(betweenness.items(), key=lambda t:-t[1]),
            #     sorted(opp_betweenness.items(), key=lambda t:-t[1])
            # ):
            #     print("{}: {} \t {}: {}".format(k, v, ok, ov))

            # print()

            edge_betweenness = current_flow_edge_betweenness_directed(
                graphs['scaled_graph'],
                start_node=goalkeeper_node
            )
            # opp_edge_betweenness = current_flow_edge_betweenness_directed(
            #     opposing_graphs['scaled_graph'],
            #     start_node=opp_goalkeeper_node
            # )
            # print("EDGE BETWEENNESS (TOP 10)")
            # print("Team {}".format(team_object.team_id))
            # for key, value in list(sorted(edge_betweenness.items(), key=lambda t:-t[1]))[:10]:
            #     print("{} -- {} --> {}: {}".format(key[0], pass_map[key[0]][key[1]]['num_passes'], key[1], value))
            # print("Team {}".format(opposing_team_object.team_id))
            # for key, value in list(sorted(opp_edge_betweenness.items(), key=lambda t:-t[1]))[:10]:
            #     print("{} -- {} --> {}: {}".format(key[0], opposing_pass_map[key[0]][key[1]]['num_passes'], key[1], value))

            # print()

            closenesses = current_flow_closeness_directed(
                graphs['scaled_graph'],
                start_node=goalkeeper_node
            )
            # opp_closenesses = current_flow_closeness_directed(
            #     opposing_graphs['scaled_graph'],
            #     start_node=opp_goalkeeper_node
            # )
            # print("CLOSENESS")
            # # for key, value in sorted(closenesses.items(), key=lambda t:-t[1]):
            # #     print("{}: {}".format(key, value))
            # for (k, v), (ok, ov) in zip(
            #     sorted(closenesses.items(), key=lambda t:-t[1]),
            #     sorted(opp_closenesses.items(), key=lambda t:-t[1])
            # ):
            #     print("{}: {} \t {}: {}".format(k, v, ok, ov))

            print()

            katz_centrality = nx.katz_centrality_numpy(
                graphs['inverse_graph'],
                weight='weight'
            )
            opp_katz_centrality = nx.katz_centrality_numpy(
                opposing_graphs['inverse_graph'],
                weight='weight'
            )
            print("KATZ")
            # for key, value in sorted(katz_centrality.items(), key=lambda t:-t[1]):
            #     print("{}: {}".format(key, value))
            for (k, v), (ok, ov) in zip(
                sorted(katz_centrality.items(), key=lambda t:-t[1]),
                sorted(opp_katz_centrality.items(), key=lambda t:-t[1])
            ):
                print("{}: {} \t {}: {}".format(k, v, ok, ov))

            print()

            ns, ac = onet.get_eigenvalues(pass_map.keys(), pass_map)
            print("network strength: {}, algebraic connectivity: {}".format(ns, ac))

            print(formation.match_id)

            # send in highest betweenness edges to highlight on graph
            highlight_edges = list(sorted(edge_betweenness.items(), key=lambda t:-t[1]))[:10]

            if role_grouped:
                formation.get_formation_graph_by_role(
                    original_pass_map,
                    show_triplets=period
                    # highlight_edges=highlight_edges
                )
                # opposing_formation.get_formation_graph_by_role(original_opposing_pass_map)
            else:
                formation.get_formation_graph(
                    pass_map=pass_map,
                    show_triplets=period
                    # highlight_edges=highlight_edges
                )
                # opposing_formation.get_formation_graph(pass_map=opposing_pass_map)
    ###

