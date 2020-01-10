import OPTA as opta
import OPTA_weighted_networks as onet

import csv
from itertools import combinations
import networkx as nx

from graphrole import (
    RecursiveFeatureExtractor,
    RoleExtractor
)


def get_graph_edges(fpath, match_ids, team_id, weighted=False):
    """
    Returns the edges and the node to player_id key

    Args:
        fpath (str): folder path for match XML files
        match_ids (list of ints): list of match IDs to include in the large graph evaluation
        team_id (int): team ID being evaluated
    Kwargs:
        weighted (bool): whether to weight the graph edges based on the number of passes between players

    Returns:
        edges (list of tuples): list of edges (passer_id, receiver_id [, weight if weighted=True])
        num_to_id_key (dict): dictionary of graph node numbers mapped to player IDs
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
                    if weighted:
                        node_pair = (ids_to_nums[p_id], ids_to_nums[r_id], pass_map[p_id][r_id]['num_passes'])
                    edges.append(node_pair)

        for id, num in ids_to_nums.items():
            num_to_id_key[num] = id

    return edges, num_to_id_key


def generate_graph_csv(fpath, match_ids, team_id, weighted=False):
    """
    Generate a CSV file from team and match info

    Args:
        fpath (str): folder path for match XML files
        match_ids (list of ints): list of match IDs to include in the large graph evaluation
        team_id (int): team ID being evaluated
    Kwargs:
        weighted (bool): whether to weight the graph edges based on the number of passes between players
    """
    key_filename = '{team_id}_largenetwork_key.csv'.format(team_id=team_id)
    output_filename = '{team_id}_largenetwork.csv'.format(team_id=team_id)

    if weighted:
        key_filename = '{team_id}_weighted_largenetwork_key.csv'.format(team_id=team_id)
        output_filename = '{team_id}_weighted_largenetwork.csv'.format(team_id=team_id)

    edges, num_to_id_key = get_graph_edges(fpath, match_ids, team_id, weighted=weighted)

    with open(key_filename, 'w') as csvfile:
        op_writer = csv.writer(csvfile)
        for entry in num_to_id_key.items():
            op_writer.writerow(entry)

    with open(output_filename, 'w') as csvfile:
        op_writer = csv.writer(csvfile)
        for edge in edges:
            op_writer.writerow(edge)


def generate_total_graph(fpath, match_ids, team_id, weighted=False):
    """
    Generate a complete graph of all matches based on matches and team ID

    Args:
        fpath (str): folder path for match XML files
        match_ids (list of ints): list of match IDs to include in the large graph evaluation
        team_id (int): team ID being evaluated
    Kwargs:
        weighted (bool): whether to weight the graph edges based on the number of passes between players

    Returns:
        total_graph (nx.Graph): the total graph of all the listed matches played by the given team
    """
    print('getting edges')
    edges, num_to_id_key = get_graph_edges(fpath, match_ids, team_id, weighted=weighted)

    print('generating graph')
    if weighted:
        total_graph = nx.Graph()
        for p_id, r_id, w in edges:
            total_graph.add_edge(p_id, r_id, weight=w)
        return total_graph

    total_graph = nx.from_edgelist(edges)
    return total_graph


def get_roles_from_graph(graph, roles_file=None, percentages_file=None):
    """
    Use `graphrole` package to extract roles from the large team match graph

    Args:
        graph (nx.Graph): total graph of all matches played by a team
    Kwargs:
        roles_file (str): filename that extracted roles should be saved into
        percentages_file (str): filename that extracted role likelihood percentages should be saved into

    Returns:
        role_extractor (RoleExtractor): RoleExtractor object that contains roles and role percentages
    """
    print('extracting features')
    feature_extractor = RecursiveFeatureExtractor(graph)
    features = feature_extractor.extract_features()

    print('extracting roles')
    role_extractor = RoleExtractor(n_roles=None)
    role_extractor.extract_role_factors(features)

    if roles_file is not None:
        roles = role_extractor.roles
        with open(roles_file, 'w') as rf:
            for node_id, role in roles.items():
                line = "{}, {}\n".format(node_id, role)
                rf.write(line)

    if percentages_file is not None:
        percentages = role_extractor.role_percentage
        with open(percentages_file, 'w') as pf:
            for index, row in percentages.iterrows():
                line = "{}, {}\n".format(index, ', '.join([str(n) for n in row]))
                pf.write(line)

    return role_extractor


def dict_from_csv(filename):
    """
    Generate a dictionary from 2-element CSV. The first element of each row is the
    dictionary key and the second element is the value.

    Args:
        filename (str): the CSV file to be read from

    Returns:
        dictionary (dict): the extracted dictionary
    """

    dictionary = {}
    with open(filename, 'r') as csvfile:
        csvreader = csv.reader(csvfile)
        for row in csvreader:
            dictionary[row[0]] = row[1]

    return dictionary


def show_ids_with_roles(num_to_id, num_to_role):
    """
    Display the roles that each player has been assigned to across matches.

    Args:
        num_to_id (dict): dictionary mapping large graph node numbers to player IDs
        num_to_role (dict): dictionary mapping large graph node numbers to roles
    """

    id_to_nums = {}
    for num, p_id in num_to_id.items():
        if id_to_nums.get(p_id) is None:
            id_to_nums[p_id] = []
        id_to_nums[p_id].append(num)

    for p_id, nums in id_to_nums.items():
        print("---{}---".format(p_id))
        for n in nums:
            print("{}: {}".format(n, num_to_role[n]))
        print()


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

# UNWEIGHTED
# generate_graph_csv(fpath, all_copenhagen_match_ids, copenhagen_team_id)
# graph = generate_total_graph(fpath, all_copenhagen_match_ids, copenhagen_team_id)
# role_extractor = get_roles_from_graph(graph, roles_file="569_roles.csv", percentages_file="569_role_percentages.csv")

# num_to_id = dict_from_csv('569_largenetwork_key.csv')
# num_to_role = dict_from_csv('569_roles.csv')
# show_ids_with_roles(num_to_id, num_to_role)

# WEIGHTED
generate_graph_csv(fpath, all_copenhagen_match_ids, copenhagen_team_id, weighted=True)
graph = generate_total_graph(fpath, all_copenhagen_match_ids, copenhagen_team_id, weighted=True)
role_extractor = get_roles_from_graph(graph, roles_file="569_weighted_roles.csv", percentages_file="569_weighted_role_percentages.csv")

num_to_id = dict_from_csv('569_weighted_largenetwork_key.csv')
num_to_role = dict_from_csv('569_weighted_roles.csv')
show_ids_with_roles(num_to_id, num_to_role)


