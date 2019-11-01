# -*- coding: utf-8 -*-
"""
Created on Tue Oct 29 12:09:00 2019

@author: skandaswamy
"""

import OPTA as OPTA
import matplotlib.pyplot as plt
import numpy as np
import networkx as nx


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

    pass_map = {p_id: {r_id: 0 for r_id in mapped_players} for p_id in mapped_players}

    last_pass = None
    for e in events_raw:
        if last_pass is not None:
            pass_map[last_pass.player_id][e.player_id] += 1

        if e.is_pass and e.outcome == 1:
            last_pass = e
        else:
            last_pass = None

    return pass_map


def map_weighted_passing_network(match_OPTA, team="home", exclude_subs=False):
    """
    Display a visual representation of the passing network. This network is not spatially
    aware in terms of player location on the pitch, but the length of each edge is inversely
    proportional to the number of passes on that edge.
    """

    team_object = get_team(match_OPTA, team=team)
    pass_map = get_all_pass_destinations(match_OPTA, team=team, exclude_subs=exclude_subs)

    # TODO: deal with bi-directional edges of different weights (add?)
    G = nx.Graph()
    for p_id, pass_dict in pass_map.items():
        for r_id, n_passes in pass_dict.items():
            G.add_edge(p_id, r_id, weight=n_passes)

    pos = nx.spring_layout(G)

    # get labels
    labels = {}
    for p_id in G.nodes():
        labels[p_id] = str(team_object.player_map[p_id])

    nx.draw_networkx_nodes(G, pos, node_size=700)
    nx.draw_networkx_edges(G, pos, width=2)
    nx.draw_networkx_labels(G, pos, labels, font_size=12, font_family='sans-serif')

    plt.axis('off')
    plt.show()


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
    for poss_triplet in combinations([player.id for player in mapped_players], 3):
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
            triplet_scores[tuple(sorted(set(consecutive_passers)))] += 1

        # clear the consecutive passers list if the ball has been lost or shot
        if event.is_shot or event.outcome == 0:
            consecutive_passers = []

    sorted_triplets = sorted([ts for ts in triplet_scores.items()], key=lambda ts:-ts[1])
    max_popularity = float(sorted_triplets[0][1])

    return sorted_triplets