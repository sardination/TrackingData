# -*- coding: utf-8 -*-
"""
Created on Tue Oct 29 12:09:00 2019

@author: skandaswamy
"""

import OPTA as OPTA

from itertools import combinations
import matplotlib.pyplot as plt
import numpy as np
import networkx as nx


# node color mappings for different positions
position_color_mapping = {
    "Goalkeeper": "black",
    "Defender": "red",
    "Midfielder": "yellow",
    "Striker": "green",
    "Substitute": "blue",
    "misc": "grey"
}


def get_color_by_gradient(value, low_color = "0000ff", high_color = "ff0000"):
    """
    Return RGB hex color for a 0-1 gradient between `low_color`
    and `high_color` at position `value`

    Args:
        value (float): value between 0 and 1 in the gradient

    Kwargs:
        low_color (hex string): color corresponding to 0 in the gradient (default blue)
        high_color (hex string): color corresponding to 1 in the gradient (default red)

    Return:
        gradient_color (hex string): color corresponding to `value` in the gradient
    """

    if value < 0:
        value = 0
    elif value > 1:
        value = 1

    if low_color[0] == "#":
        low_color = low_color[1:]
    if high_color[0] == "#":
        high_color = high_color[1:]

    low_color_rgb = [int(low_color[i:i+2], 16) for i in range(0, 6, 2)]
    high_color_rgb = [int(high_color[i:i+2], 16) for i in range(0, 6, 2)]

    grad_rgb = [
        int((h - l) * value) if h > l else int((l - h) * (1 - value))
        for l,h in zip(low_color_rgb, high_color_rgb)
    ]

    grad_hex = ''.join([hex(el)[2:].rjust(2, "0") for el in grad_rgb])

    return "#{}".format(grad_hex)


def get_team(match_OPTA, team="home"):
    """
    Return the appropriate team object from the match_OPTA

    Args:
        match_OPTA (OPTAmatch): match in question
    Kwargs:
        team (string): "home" or "away"

    Return:
        team_object (OPTAteam)
    """

    return match_OPTA.hometeam if team == "home" else match_OPTA.awayteam


def get_substitutes(match_OPTA, team="home"):
    """
    Return a list of players that were substituted in and a list of players that were
    substituted out during the game for the given team

    Args:
        match_OPTA (OPTAmatch): match in question
    Kwargs:
        team (string): "home" or "away"

    Return:
        substitutes_on, substitutes_off (list, list)
    """

    team_object = get_team(match_OPTA, team=team)
    events_raw = [e for e in team_object.events if e.is_substitution]

    substitutes_on = []
    substitutes_off = []

    for e in events_raw:
        if e.sub_direction == "on":
            substitutes_on.append(e.player_id)
        else:
            substitutes_off.append(e.player_id)

    return substitutes_on, substitutes_off


def get_mapped_players(match_OPTA, team="home", exclude_subs=False):
    """
    Find which players have had a role in the game and should be mapped

    Args:
        match_OPTA (OPTAmatch): match in question
    Kwargs:
        team (string): "home" or "away"
        exclude_subs (bool): whether to exclude substitutes from the map

    Return:
        mapped_players (set)
    """

    team_object = get_team(match_OPTA, team=team)
    events_raw = [e for e in team_object.events if e.is_pass or e.is_shot]

    exclude_players = get_substitutes(match_OPTA, team=team)[0] if exclude_subs else []

    mapped_players = set([])

    for e in events_raw:
        if e.player_id not in exclude_players:
            mapped_players.add(e.player_id)

    return mapped_players


def get_clustering_coefficients(mapped_players, pass_map, weighted=True):
    """
    Return the clustering coefficient of every mapped player as an array

    Args:
        mapped_players (list): list of player_ids for every mapped player
        pass_map (dict of dicts): pass_map[u][v] is number of passes from u to v
    Kwargs:
        weighted (bool): whether to get the weighted clustering coefficients

    Return:
        clustering_coefficients (1D array)
    """

    freq_matrix = np.array([[0] * len(mapped_players) for _ in range(len(mapped_players))])
    for p_index, p_id in enumerate(mapped_players):
        for r_index, r_id in enumerate(mapped_players):
            freq_matrix[p_index][r_index] = pass_map[p_id][r_id]['num_passes']
    adjacency_matrix = np.array(freq_matrix).astype('bool')
    weighted_matrix = freq_matrix ** (1/3)

    degrees = np.sum(adjacency_matrix, axis=0) + np.sum(adjacency_matrix, axis=1)
    degrees_inout = adjacency_matrix * adjacency_matrix.T
    np.fill_diagonal(degrees_inout, 0)
    degrees_inout = np.sum(degrees_inout, axis=1)

    coeffs = []
    if weighted:
        coeffs = np.diagonal(
                np.linalg.matrix_power((weighted_matrix + weighted_matrix.T), 3)
            ) /(2 * (degrees * (degrees - 1)) - 2 * degrees_inout)
    else:
        coeffs = np.diagonal(np.linalg.matrix_power(
            (adjacency_matrix + adjacency_matrix.T), 3)
        ) / (2 * (degrees * (degrees - 1)) - 2 * degrees_inout)

    return {p_id : coeff for p_id, coeff in zip(mapped_players, coeffs)}


def get_all_pass_destinations(match_OPTA, team="home", exclude_subs=False):
    """
    Generate a dictionary of dictionaries where d[p_id1][p_id2] is the number of
    passes from p_id1 to p_id2

    Args:
        match_OPTA (OPTAmatch): match in question
    Kwargs:
        team (string): "home" or "away"
        exclude_subs (bool): whether to exclude substitutes from the map
    """

    team_object = get_team(match_OPTA, team=team)
    events_raw = [e for e in team_object.events if e.is_pass or e.is_shot]

    exclude_players = get_substitutes(match_OPTA, team=team)[0] if exclude_subs else []
    mapped_players = get_mapped_players(match_OPTA, team=team, exclude_subs=exclude_subs)

    pass_map = {p_id: {r_id: {
                    "num_passes": 0,
                    "avg_pass_dist": 0,
                    "avg_pass_dir": 0 # scale of 0 to 1 indicating lateral - lengthwise
                } for r_id in mapped_players} for p_id in mapped_players}

    last_pass = None
    epsilon = 0.00000000001
    for e in events_raw:
        if last_pass is not None and last_pass.player_id in mapped_players and e.player_id in mapped_players:
            # pass_map[last_pass.player_id][e.player_id] += 1
            pass_map[last_pass.player_id][e.player_id]["num_passes"] += 1
            pass_dist = np.linalg.norm(np.array([e.x, e.y]) - np.array([last_pass.x, last_pass.y]))
            pass_map[last_pass.player_id][e.player_id]["avg_pass_dist"] += pass_dist
            pass_laterality = np.degrees(np.arctan(np.abs(
                float(last_pass.y - e.y + epsilon) / float(last_pass.x - e.x + epsilon)
            )))
            pass_map[last_pass.player_id][e.player_id]["avg_pass_dir"] += pass_laterality

        if e.is_pass and e.outcome == 1:
            last_pass = e
        else:
            last_pass = None

    for p_id in mapped_players:
        for r_id in mapped_players:
            num_passes = pass_map[p_id][r_id]["num_passes"]
            if num_passes == 0:
                continue
            pass_map[p_id][r_id]["avg_pass_dist"] /= num_passes
            pass_map[p_id][r_id]["avg_pass_dir"] /= num_passes

    # Normalize pass direction using max laterality (for now)
    max_laterality = 90
    for p_id in mapped_players:
        for r_id in mapped_players:
           pass_map[p_id][r_id]["avg_pass_dir"] = pass_map[p_id][r_id]["avg_pass_dir"] / max_laterality

    return pass_map


def map_weighted_passing_network(match_OPTA, team="home", exclude_subs=False, use_triplets=True, block=True):
    """
    Display a visual representation of the passing network. This network is not spatially
    aware in terms of player location on the pitch, but the length of each edge is inversely
    proportional to the number of passes on that edge.

    Args:
        match_OPTA (OPTAmatch): match in question
    Kwargs:
        team (string): "home" or "away"
        exclude_subs (bool): whether to exclude subs from map
        use_triplets (bool): whether to map connections based on triplets or all passes
        block(bool): whether to block the display of the network plt
    """

    team_object = get_team(match_OPTA, team=team)
    pass_map = get_all_pass_destinations(match_OPTA, team=team, exclude_subs=exclude_subs)

    G = nx.Graph()

    if use_triplets:
        triplets = find_player_triplets(match_OPTA, team=team, exclude_subs=exclude_subs)
        max_popularity = float(triplets[-1][1])

        for triplet in triplets:
            players = [p_id for p_id in triplet[0]]
            players.append(players[0])
            for i in range(len(players) - 1):
                p_id = players[i]
                r_id = players[i + 1]
                G.add_edge(p_id, r_id, weight=triplet[1])

    else:
        # WEIGHTED BY NUMBER OF PASSES
        # TODO: if unweighted, add bidirectional edges?
        for p_id, pass_dict in pass_map.items():
            for r_id, pass_info in pass_dict.items():
                n_passes = pass_info["num_passes"]
                if not G.has_edge(p_id, r_id):
                    G.add_edge(p_id, r_id, weight=n_passes)
                else:
                    G.add_edge(p_id, r_id, weight=n_passes + pass_map[r_id][p_id]["num_passes"])

    # hold goalkeeper node in position (0,0) on all graphs
    set_pos = {}
    for p_id in pass_map.keys():
        if team_object.player_map[p_id].position == "Goalkeeper":
            set_pos[p_id] = (0,0)
    pos = nx.spring_layout(G, pos=set_pos, fixed=set_pos.keys())

    # get node groups - labels and colors
    node_groups = {position: {"ids": [], "labels": {}} for position, _ in position_color_mapping.items()}
    # labels = {}
    for p_id in G.nodes():
        # labels[p_id] = str(team_object.player_map[p_id])
        # labels[p_id] = "{}".format(team_object.player_map[p_id].lastname)

        player = team_object.player_map[p_id]
        player_position = player.position
        if position_color_mapping.get(player_position) is None:
            player_position = "misc"

        node_groups[player_position]["ids"].append(p_id)
        # node_groups[player_position]["labels"][p_id] = "{}".format(team_object.player_map[p_id].lastname)
        node_groups[player_position]["labels"][p_id] = p_id

    clustering_coeffs = get_clustering_coefficients(pass_map.keys(), pass_map, weighted=True)
    print(clustering_coeffs)
    max_clustering_coeff = max(clustering_coeffs.values()) ** 3 # ^ 3 to exaggerate effect
    max_node_size = 1200
    node_sizes = [(clustering_coeffs[n] ** 3 / max_clustering_coeff) * max_node_size for n in G.nodes()]

    # nx.draw_networkx_nodes(G, pos, node_size=700)
    for position, node_group_info in node_groups.items():
        nx.draw_networkx_nodes(
            G,
            pos,
            # node_size=700,
            node_size=node_sizes,
            nodelist=node_group_info["ids"],
            node_color=position_color_mapping[position],
        )
        nx.draw_networkx_labels(
            G,
            pos,
            node_group_info["labels"],
            font_size=12,
            font_family='sans-serif',
            font_color='cyan'
        )
    # edge_widths = [G[u][v]['weight'] for u,v in G.edges()]
    # average the average distances from u to v and from v to u for the thickness of each edge
    # take the reciprocal because closer passes should be thicker
    edge_widths = [1 / ((pass_map[u][v]["avg_pass_dist"] + pass_map[v][u]["avg_pass_dist"]) / 2)
        if pass_map[u][v]["avg_pass_dist"] + pass_map[v][u]["avg_pass_dist"] != 0 else 0
        for u,v in G.edges()
    ]
    max_width = max(edge_widths)
    max_thickness = 3
    edge_widths = [(w / max_width) * max_thickness for w in edge_widths]

    edge_colors = [get_color_by_gradient((pass_map[u][v]["avg_pass_dir"] + pass_map[u][v]["avg_pass_dir"]) / 2)
        for u,v in G.edges()
    ]

    nx.draw_networkx_edges(G, pos, width=edge_widths, edge_color=edge_colors)
    # nx.draw_networkx_labels(G, pos, labels, font_size=12, font_family='sans-serif', font_color='red')

    plt.axis('off')
    plt.show(block=block)


def find_player_triplets(match_OPTA, team="home", exclude_subs=False):
    """
    Determine triplets of players that are strongly connected

    Args:
        match_OPTA (OPTAmatch): match OPTA information

    Kwargs:
        team (string): "home" or "away" to specify which team from the match is being displayed

    Return:
        sorted_triples (list of tuples): list of triplets (members, weight) in descending order of weight
    """

    team_object = get_team(match_OPTA, team=team)
    mapped_players = get_mapped_players(match_OPTA, team=team, exclude_subs=exclude_subs)
    all_events = [e for e in team_object.events if e.is_pass or e.is_shot]

    triplet_scores = {}
    for poss_triplet in combinations([p_id for p_id in mapped_players], 3):
        triplet_scores[tuple(sorted(poss_triplet))] = 0

    consecutive_passers = []

    for event in all_events:
        player_id = event.player_id

        if player_id not in mapped_players:
            consecutive_passers = []
            continue

        consecutive_passers.append(player_id)

        # if a new passer has been added, pushing the unique players above a triplet, then remove the earliest
        #   passers until a triplet is formed from the latest passes
        while len(set(consecutive_passers)) > 3:
            consecutive_passers = consecutive_passers[1:]

        # if there are 3 unique passers in the last series of consecutive passes, then add another pass to the triplet
        if len(set(consecutive_passers)) == 3:
            # USING RAW NUMBER OF TRIPLETS
            triplet_scores[tuple(sorted(set(consecutive_passers)))] += 1

        # clear the consecutive passers list if the ball has been lost or shot
        if event.is_shot or event.outcome == 0:
            consecutive_passers = []

    sorted_triplets = sorted([ts for ts in triplet_scores.items()], key=lambda ts:ts[1])
    max_popularity = float(sorted_triplets[0][1])

    return sorted_triplets
