import centrality
import change_patterns
import formations
import OPTA as opta
import OPTA_weighted_networks as onet

import matplotlib.colors as mpl_colors
import matplotlib.pyplot as plt
import numpy as np

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

matches = {}
copenhagen_team_objects = {}
copenhagen_home_away = {}
pass_maps = [{} for h in range(0, 3)]

for match_id in all_copenhagen_match_ids:
    fname = str(match_id)
    match_OPTA = opta.read_OPTA_f7(fpath, fname)
    match_OPTA = opta.read_OPTA_f24(fpath, fname, match_OPTA)
    matches[match_id] = match_OPTA

    if match_OPTA.hometeam.team_id == copenhagen_team_id:
        copenhagen_team_objects[match_id] = match_OPTA.hometeam
        copenhagen_home_away[match_id] = "home"
    else:
        copenhagen_team_objects[match_id] = match_OPTA.awayteam
        copenhagen_home_away[match_id] = "away"

    for half in range(0, 3):
        pass_maps[half][match_id] = onet.get_all_pass_destinations(
            matches[match_id],
            team=copenhagen_home_away[match_id],
            exclude_subs=False,
            half=half
        )

# Find most popular triplets
triplet_count = {}
top_5_triplet_count = {}
for match_id, match in matches.items():
    team_object = copenhagen_team_objects[match_id]
    home_or_away = copenhagen_home_away[match_id]
    pass_map = onet.get_all_pass_destinations(match, team=home_or_away, exclude_subs=False, half=0)

    role_mappings, role_pass_map = onet.convert_pass_map_to_roles(team_object, pass_map)
    triplet_list_by_id = onet.find_player_triplets_by_team(team_object, half=0) # full match
    triplet_list = []
    for triplet, num_passes in triplet_list_by_id:
        new_triplet = []
        for p in triplet:
            new_triplet.append(role_mappings[p])
        triplet_list.append((tuple(sorted(new_triplet)), num_passes))

    this_match_triplets = {}
    for triplet, num_passes in triplet_list:
        try:
            triplet_count[triplet] += num_passes
        except KeyError:
            triplet_count[triplet] = num_passes

        try:
            this_match_triplets[triplet] += num_passes
        except KeyError:
            this_match_triplets[triplet] = num_passes

    for triplet, num_passes in sorted(this_match_triplets.items(), key=lambda t: -t[1])[:5]:
        try:
            top_5_triplet_count[triplet] += 1
        except KeyError:
            top_5_triplet_count[triplet] = 1

top_5_triplet_count_sorted = sorted(top_5_triplet_count.items(), key=lambda t:-t[1])
print(top_5_triplet_count_sorted)
triplet_count_sorted = sorted(triplet_count.items(), key=lambda t:-t[1])[:10]
print(triplet_count_sorted)

print()
print("------ AVERAGE FORMATION ------")
all_players = []
for formation in copenhagen_formations.values():
    all_players.extend(pass_maps[0][formation.match_id].keys())
all_players = list(set(all_players))
average_pass_map = [{p_id: {r_id: {
                        "num_passes": 0,
                        "avg_pass_dist": 0,
                        "avg_pass_dir": 0,
                        "total_appearances": 0
                    } for r_id in all_players} for p_id in all_players} for h in range(0, 3)]
average_role_pass_map = [{p_id: {r_id: {
    "num_passes": 0,
    "avg_pass_dist": 0,
    "avg_pass_dir": 0,
    "total_appearances": 0
} for r_id in range(1, 12)} for p_id in range(1, 12)} for h in range(0, 3)]
transfer_map = {}

for match_id, formation in copenhagen_formations.items():
    match = matches[match_id]
    team_object = copenhagen_team_objects[match_id]
    formation.add_team_object(team_object)
    formation.add_goalkeeper()
    home_or_away = copenhagen_home_away[match_id]

    for half in range(0, 3):
        pass_map = pass_maps[half][match_id]

        for p_id, p_dict in pass_map.items():
            for r_id, pass_info in p_dict.items():
                average_pass_map[half][p_id][r_id]["num_passes"] += pass_info["num_passes"]
                average_pass_map[half][p_id][r_id]["avg_pass_dist"] += pass_info["avg_pass_dist"]
                average_pass_map[half][p_id][r_id]["avg_pass_dir"] += pass_info["avg_pass_dir"]
                average_pass_map[half][p_id][r_id]["total_appearances"] += 1

        role_mappings, role_pass_map = onet.convert_pass_map_to_roles(team_object, pass_map)

        for p_id, p_dict, in role_pass_map.items():
            for r_id, pass_info in p_dict.items():
                average_role_pass_map[half][p_id][r_id]["num_passes"] += pass_info["num_passes"]
                average_role_pass_map[half][p_id][r_id]["avg_pass_dist"] += pass_info["avg_pass_dist"]
                average_role_pass_map[half][p_id][r_id]["avg_pass_dir"] += pass_info["avg_pass_dir"]
                average_role_pass_map[half][p_id][r_id]["total_appearances"] += 1

        # for p_id, role_id in role_mappings.items():
        #     current_role = transfer_map.get(p_id)
        #     if current_role is not None and current_role != role_id:
        #         print("Differing roles for player {}: {} and {}".format(p_id, current_role, role_id))

        #     transfer_map[p_id] = role_id

num_formations = len(copenhagen_formations.values())
for p_id in all_players:
    for r_id in all_players:
        for half in range(0, 3):
            pass_dict = average_pass_map[half][p_id][r_id]
            if pass_dict["total_appearances"] == 0:
                average_pass_map[half][p_id][r_id] = {
                    "num_passes": pass_dict["num_passes"] / num_formations,
                    "avg_pass_dist": 0,
                    "avg_pass_dir": 0
                }
                continue
            average_pass_map[half][p_id][r_id] = {
                "num_passes": pass_dict["num_passes"] / num_formations,
                "avg_pass_dist": pass_dict["avg_pass_dist"] / pass_dict["total_appearances"],
                "avg_pass_dir": pass_dict["avg_pass_dir"] / pass_dict["total_appearances"]
            }

for p_id in range(1, 12):
    for r_id in range(1, 12):
        for half in range(0, 3):
            pass_dict = average_role_pass_map[half][p_id][r_id]
            if pass_dict["total_appearances"] == 0:
                average_pass_map[half][p_id][r_id] = {
                    "num_passes": pass_dict["num_passes"] / num_formations,
                    "avg_pass_dist": 0,
                    "avg_pass_dir": 0
                }
                continue
            average_role_pass_map[half][p_id][r_id] = {
                "num_passes": pass_dict["num_passes"] / num_formations,
                "avg_pass_dist": pass_dict["avg_pass_dist"] / pass_dict["total_appearances"],
                "avg_pass_dir": pass_dict["avg_pass_dir"] / pass_dict["total_appearances"]
            }

average_formation = formations.average_formations(copenhagen_formations.values())

for half in range(0, 3):
    # print("--- AVERAGE FORMATION FOR PERIOD {} ---".format(half))
    average_graph = centrality.get_directed_graph_without_times(average_role_pass_map[half])
    edge_betweenness = centrality.current_flow_edge_betweenness_directed(
        average_graph,
        start_node=1
    )
    print("EDGE BETWEENNESS (TOP 10) PD {}".format(half))
    print("Team {}".format(team_object.team_id))
    top_10_edges = list(sorted(edge_betweenness.items(), key=lambda t:-t[1]))[:10]
    for key, value in top_10_edges:
        print("{} -- {} --> {}: {}".format(key[0], average_role_pass_map[half][key[0]][key[1]]['num_passes'], key[1], value))
    average_formation.get_formation_graph(
        pass_map=average_role_pass_map[half],
        highlight_edges=top_10_edges
    )
    # average_formation.get_formation_graph(pass_map=average_role_pass_map[half])

# print()
# print("--- DIFFERENCING NETWORKS ---")
# match_id = 984517
# match_pass_maps = [
#     onet.get_all_pass_destinations(
#         matches[match_id],
#         team=copenhagen_home_away[match_id],
#         exclude_subs=False,
#         half=half
#     )
#     for half in [0,1,2]
# ]
# formation = copenhagen_formations[match_id]
# for half in [0, 1, 2]:
#     print("--- DIFFERENCE FOR PERIOD {} ---".format(half))
#     formation.get_formation_difference_graph(
#         match_pass_maps[half],
#         average_formation,
#         average_role_pass_map[half],
#         other_role=True
#     )

# average_formation.get_formation_difference_graph(
#     average_role_pass_map[1],
#     average_formation,
#     average_role_pass_map[2],
#     self_role=True,
#     other_role=True
# )

# for half in range(0, 3):
#     ns, ac = onet.get_eigenvalues(average_role_pass_map[half].keys(), average_role_pass_map[half], goalie=1)
#     print("{} half {}: network strength: {}, algebraic connectivity: {}".format(copenhagen_team_id, half, ns, ac))

# for half in range(0, 3):
#     roles = set(average_role_pass_map[half].keys())
#     roles.add(0)
#     weighted_adjacency_matrix = np.array(onet.get_weighted_adjacency_matrix(
#         sorted(list(roles)),
#         average_role_pass_map[half]
#     ))

#     # TODO: heatmap weights by role vs role
#     fig, ax = plt.subplots()
#     plt.imshow(
#         weighted_adjacency_matrix,
#         cmap='hot',
#         interpolation='nearest',
#         norm=mpl_colors.Normalize(vmin=0, vmax=30)
#     )
#     plt.show()


# for half in range(0, 3):
#     change_patterns.plot_closeness_vs_betweenness_from_pass_map(
#         average_role_pass_map[half],
#         title="Average Period {}".format(half)
#     )

# change_patterns.plot_cross_match_centrality_by_pass_maps(
#     {
#         "Average Half 1": average_role_pass_map[1],
#         "Average Half 2": average_role_pass_map[2]
#     }
# )

# change_patterns.plot_cross_match_centrality_by_pass_maps(
#     {
#         "Average Half 1": average_role_pass_map[1],
#         "Average Half 2": average_role_pass_map[2]
#     },
#     metric="betweenness"
# )

# average_pageranks = onet.get_average_pagerank(matches, copenhagen_home_away)

# match_id = 984517
# change_patterns.plot_match_to_average_pagerank(
#     average_pageranks,
#     matches[match_id],
#     team=copenhagen_home_away[match_id],
#     match_id=match_id
# )

