import OPTA as opta
import OPTA_weighted_networks as onet

import csv
from itertools import combinations
import networkx as nx

from graphrole import (
    RecursiveFeatureExtractor,
    RoleExtractor
)


def get_graph_edges(fpath, match_ids, team_id):
    """
    Returns the edges and the node to player_id key
    """

    node_num = 0
    edges = []
    num_to_id_key = {}
    for match_id in match_ids:
        fname = str(match_id)
        match_OPTA = opta.read_OPTA_f7(fpath, fname)
        match_OPTA = opta.read_OPTA_f24(fpath, fname, match_OPTA)

        home_or_away = "home"
        home_team = onet.get_team(match_OPTA, team="home")
        away_team = onet.get_team(match_OPTA, team="away")
        this_team = home_team
        if home_team.team_id != copenhagen_team_id:
            home_or_away = "away"
            this_team = away_team

        pass_map = onet.get_all_pass_destinations(match_OPTA, team=home_or_away, exclude_subs=False)
        # mapped_player_ids = this_team.player_map.keys()
        mapped_player_ids = pass_map.keys()

        ids_to_nums = {p_id : node_num + i for i, p_id in enumerate(mapped_player_ids)}
        node_num += len(mapped_player_ids)

        for p_id in pass_map.keys():
            for r_id in pass_map.keys():
                if pass_map[p_id][r_id]['num_passes'] > 0:
                    node_pair = (ids_to_nums[p_id], ids_to_nums[r_id])
                    edges.append(node_pair)

        for id, num in ids_to_nums.items():
            num_to_id_key[num] = id

    return edges, num_to_id_key


def generate_graph_csv(fpath, match_ids, team_id):
    key_filename = '{team_id}_largenetwork_key.csv'.format(team_id=team_id)
    output_filename = '{team_id}_largenetwork.csv'.format(team_id=team_id)

    edges, num_to_id_key = get_graph_edges(fpath, match_ids, team_id)

    with open(key_filename, 'w') as csvfile:
        op_writer = csv.writer(csvfile)
        for entry in num_to_id_key.items():
            op_writer.writerow(entry)

    with open(output_filename, 'w') as csvfile:
        op_writer = csv.writer(csvfile)
        for edge in edges:
            op_writer.writerow(edge)


def generate_total_graph(fpath, match_ids, team_id):
    print("getting edges")
    edges, num_to_id_key = get_graph_edges(fpath, match_ids, team_id)

    print('generating graph')

    total_graph = nx.from_edgelist(edges)

    return total_graph


def get_roles_from_graph(graph):
    print('extracting features')
    feature_extractor = RecursiveFeatureExtractor(graph)
    features = feature_extractor.extract_features()

    print('extracting roles')

    role_extractor = RoleExtractor(n_roles=None)
    role_extractor.extract_role_factors(features)

    import ipdb
    ipdb.set_trace()

    return role_extractor.roles


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

# generate_graph_csv(fpath, all_copenhagen_match_ids, copenhagen_team_id)
graph = generate_total_graph(fpath, all_copenhagen_match_ids, copenhagen_team_id)
roles = get_roles_from_graph(graph)

