import OPTA as opta
import OPTA_weighted_networks as onet

import csv
from itertools import combinations
import networkx as nx

from graphrole import (
    RecursiveFeatureExtractor,
    RoleExtractor
)


def get_graph_edges(fpath, match_ids, team_id, weighted=False, with_clustering=False, halves=False):
    """
    Returns the edges and the node to player_id key

    Args:
        fpath (str): folder path for match XML files
        match_ids (list of ints): list of match IDs to include in the large graph evaluation
        team_id (int): team ID being evaluated
    Kwargs:
        weighted (bool): whether to weight the graph edges based on the number of passes between players
        with_clustering (bool): whether to include the clustering coefficient for each player node
        halves (bool): whether to split each match into separate halves

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

        period_ids = [0]
        if halves:
            period_ids = [1,2]

        for half in period_ids:
            pass_map = onet.get_all_pass_destinations(match_OPTA, team=home_or_away, exclude_subs=False, half=half)
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

            clustering_coeffs = None
            if with_clustering:
                clustering_coeffs = onet.get_clustering_coefficients(mapped_player_ids, pass_map, weighted=True)

            for p_id, num in ids_to_nums.items():
                num_to_id_key[num] = {'id': p_id, 'match_id': match_id}
                if with_clustering:
                    num_to_id_key[num]['clustering'] = clustering_coeffs[p_id]
                if halves:
                    num_to_id_key[num]['half'] = half

    return edges, num_to_id_key


def generate_graph_csv(fpath, match_ids, team_id, weighted=False, with_clustering=False, halves=False, name_append=""):
    """
    Generate a CSV file from team and match info

    Args:
        fpath (str): folder path for match XML files
        match_ids (list of ints): list of match IDs to include in the large graph evaluation
        team_id (int): team ID being evaluated
    Kwargs:
        weighted (bool): whether to weight the graph edges based on the number of passes between players
        with_clustering (bool): whether to include the clustering coefficient for each player node
        halves (bool): whether to split each match into separate halves
        name_append (str): a string to insert into the csv filenames
    """
    if name_append != "":
        name_append = "_{}".format(name_append)

    key_filename = '{team_id}{name_append}_largenetwork_key.csv'.format(team_id=team_id, name_append=name_append)
    output_filename = '{team_id}{name_append}_largenetwork.csv'.format(team_id=team_id, name_append=name_append)

    # if weighted:
    #     key_filename = '{team_id}_weighted_largenetwork_key.csv'.format(team_id=team_id)
    #     output_filename = '{team_id}_weighted_largenetwork.csv'.format(team_id=team_id)

    # if with_clustering:
    #     key_filename = '{team_id}_clustered_largenetwork_key.csv'.format(team_id=team_id)
    #     output_filename = '{team_id}_clustered_largenetwork.csv'.format(team_id=team_id)

    edges, num_to_id_key = get_graph_edges(
        fpath,
        match_ids,
        team_id,
        weighted=weighted,
        with_clustering=with_clustering,
        halves=halves
    )

    with open(key_filename, 'w') as csvfile:
        op_writer = csv.writer(csvfile)
        for key, value_dict in num_to_id_key.items():
            row_list = [key]
            row_list.extend(value_dict.values())
            op_writer.writerow(row_list)

    with open(output_filename, 'w') as csvfile:
        op_writer = csv.writer(csvfile)
        for edge in edges:
            op_writer.writerow(edge)


def generate_total_graph(fpath, match_ids, team_id, weighted=False, with_clustering=False, halves=False):
    """
    Generate a complete graph of all matches based on matches and team ID

    Args:
        fpath (str): folder path for match XML files
        match_ids (list of ints): list of match IDs to include in the large graph evaluation
        team_id (int): team ID being evaluated
    Kwargs:
        weighted (bool): whether to weight the graph edges based on the number of passes between players
        with_clustering (bool): whether to include the clustering coefficient for each player node
        halves (bool): whether to split matches into halves, treating each half separately

    Returns:
        total_graph (nx.Graph): the total graph of all the listed matches played by the given team
    """
    print('getting edges')
    edges, num_to_id_key = get_graph_edges(
        fpath,
        match_ids,
        team_id,
        weighted=weighted,
        with_clustering=with_clustering,
        halves=halves
    )

    print('generating graph')
    if not weighted and not with_clustering:
        total_graph = nx.from_edgelist(edges)
        return total_graph

    total_graph = nx.Graph()
    if weighted:
        for p_id, r_id, w in edges:
            total_graph.add_edge(p_id, r_id, weight=w)
    else:
        total_graph = nx.from_edgelist(edges)
    if with_clustering:
        for p_id in total_graph.nodes():
            # total_graph[p_id]['clustering'] = num_to_id_key[p_id]['clustering']
            nx.set_node_attributes(total_graph, {p_id: num_to_id_key[p_id]['clustering']}, 'clustering')

    return total_graph


def generate_graph_from_csv(filepath, weighted=False):
    """
    Generate a complete graph from edge information in given csv file

    Args:
        filepath (str): path to CSV file
    Kwargs:
        weighted (bool): whether the graph edges in the file are weighted or not

    Returns:
        graph (nx.Graph): the graph of all the edges listed in the file

    TODO: use clustering from key as well
    """

    graph = nx.Graph()

    with open(filepath, 'r') as csvfile:
        csvreader = csv.reader(csvfile)
        if weighted:
            for row in csvreader:
                graph.add_edge(int(row[0]), int(row[1]), weight=int(row[2]))
        else:
            for row in csvreader:
                graph.add_edge(int(row[0]), int(row[1]))

    return graph


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


def dict_from_csv(filename, keys=None):
    """
    Generate a dictionary from CSV. The first element of each row is the
    dictionary key and the second element is the value.

    Args:
        filename (str): the CSV file to be read from
    Kwargs:
        keys (list of strs): the keys for the dict entries

    Returns:
        dictionary (dict): the extracted dictionary
    """

    dictionary = {}
    with open(filename, 'r') as csvfile:
        csvreader = csv.reader(csvfile)
        for row in csvreader:
            if keys is None:
                dictionary[row[0]] = row[1]
            else:
                dictionary[row[0]] = {key : row[i + 1] for i, key in enumerate(keys)}

    return dictionary


def show_ids_with_roles(num_to_id, num_to_role):
    """
    Display the roles that each player has been assigned to across matches.

    Args:
        num_to_id (dict): dictionary mapping large graph node numbers to player IDs
        num_to_role (dict): dictionary mapping large graph node numbers to roles
    """

    id_to_nums = {}
    for num, p_dict in num_to_id.items():
        p_id = p_dict['id']
        if id_to_nums.get(p_id) is None:
            id_to_nums[p_id] = []
        id_to_nums[p_id].append(num)

    for p_id, nums in id_to_nums.items():
        print("---{}---".format(p_id))
        for n in nums:
            print("{}: {}".format(n, num_to_role[n]))
        print()


def show_player_roles_from_match_id(num_to_id, num_to_role, match_id, half=None):
    """
    Display the roles that each player played in a match (or match half)

    Args:
        num_to_id (dict): dictionary mapping large graph node numbers to player IDs
        num_to_role (dict): dictionary mapping large graph node numbers to roles

    Kwargs:
        half (int): which half, 1 or 2, to display mappings for
    """

    # for num, p_dict in num_to_id.items():
    # iterate through node nums sorted by player id
    for num in sorted(num_to_id.keys(), key=lambda n:num_to_id[n]['id']):
        p_dict = num_to_id[num]

        if int(p_dict['match_id']) != match_id:
            continue

        p_half = p_dict.get('half')
        if p_half and half in [1,2] and int(p_half) != half:
            continue

        print("{}: {}".format(p_dict['id'], num_to_role[num]))


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

# num_to_id = dict_from_csv('569_largenetwork_key.csv', keys=['id', 'match_id'])
# num_to_role = dict_from_csv('569_roles.csv')
# show_ids_with_roles(num_to_id, num_to_role)

# WEIGHTED
# generate_graph_csv(fpath, all_copenhagen_match_ids, copenhagen_team_id, weighted=True, name_append="weighted")
# graph = generate_total_graph(fpath, all_copenhagen_match_ids, copenhagen_team_id, weighted=True)
# role_extractor = get_roles_from_graph(graph, roles_file="569_weighted_roles.csv", percentages_file="569_weighted_role_percentages.csv")

# num_to_id = dict_from_csv('569_weighted_largenetwork_key.csv', keys=['id', 'match_id'])
# num_to_role = dict_from_csv('569_weighted_roles.csv')
# show_ids_with_roles(num_to_id, num_to_role)

# graph = generate_graph_from_csv("569_weighted_largenetwork.csv", weighted=True)
# role_extractor = get_roles_from_graph(graph)

# num_to_id = dict_from_csv('569_weighted_largenetwork_key.csv', keys=['id', 'match_id'])
# num_to_role = dict_from_csv('569_weighted_roles.csv')
# show_ids_with_roles(num_to_id, num_to_role)

# TODO: observe roles based on match, not just player
# for match_id in all_copenhagen_match_ids:
#     print("-- MATCH {} --".format(match_id))
#     for num, p_dict in num_to_id.items():
#         if int(p_dict['match_id']) == match_id:
#             print("{}: {}".format(p_dict['id'], num_to_role[num]))

# CLUSTERING
# TODO: adjust how roles are learned (which features are used)
# generate_graph_csv(fpath, all_copenhagen_match_ids, copenhagen_team_id, with_clustering=True, name_append="clustered")
# graph = generate_total_graph(fpath, all_copenhagen_match_ids, copenhagen_team_id, with_clustering=True)
# role_extractor = get_roles_from_graph(graph, roles_file="569_clustered_roles.csv", percentages_file="569_clustered_role_percentages.csv")

# num_to_id = dict_from_csv('569_clustered_largenetwork_key.csv', keys=['id', 'match_id', 'clustering'])
# num_to_role = dict_from_csv('569_clustered_roles.csv')
# show_ids_with_roles(num_to_id, num_to_role)

# WEIGHTED + MATCH HALVES
# generate_graph_csv(fpath, all_copenhagen_match_ids, copenhagen_team_id, weighted=True, halves=True, name_append="weighted_halves")
# graph = generate_total_graph(fpath, all_copenhagen_match_ids, copenhagen_team_id, weighted=True, halves=True)
# role_extractor = get_roles_from_graph(graph, roles_file="569_weighted_halves_roles.csv", percentages_file="569_weighted_halves_role_percentages.csv")

num_to_id = dict_from_csv('569_weighted_halves_largenetwork_key.csv', keys=['id', 'match_id', 'half'])
num_to_role = dict_from_csv('569_weighted_halves_roles.csv')
show_ids_with_roles(num_to_id, num_to_role)
for match_id in all_copenhagen_match_ids:
    for half in [1,2]:
        print("-------- {} - {} --------".format(match_id, half))
        show_player_roles_from_match_id(num_to_id, num_to_role, match_id, half=half)
        print()

# graph = generate_graph_from_csv("569_weighted_largenetwork.csv", weighted=True)
# role_extractor = get_roles_from_graph(graph)

# num_to_id = dict_from_csv('569_weighted_largenetwork_key.csv', keys=['id', 'match_id'])
# num_to_role = dict_from_csv('569_weighted_roles.csv')
# show_ids_with_roles(num_to_id, num_to_role)

# TODO: observe roles based on match, not just player
# for match_id in all_copenhagen_match_ids:
#     print("-- MATCH {} --".format(match_id))
#     for num, p_dict in num_to_id.items():
#         if int(p_dict['match_id']) == match_id:
#             print("{}: {}".format(p_dict['id'], num_to_role[num]))

