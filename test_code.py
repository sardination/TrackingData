import formations
import OPTA as opta
import OPTA_visuals as ovis
import OPTA_weighted_networks as onet


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

all_copenhagen_match_ids = [984514, 984567]

# PAGERANK SORTING

# all_matches = []
# all_pageranked_players = []
# for match_id in all_copenhagen_match_ids:
#     fname = str(match_id)
#     match_OPTA = opta.read_OPTA_f7(fpath, fname)
#     match_OPTA = opta.read_OPTA_f24(fpath, fname, match_OPTA)
#     all_matches.append(match_OPTA)

#     home_or_away = "home"
#     home_team = onet.get_team(match_OPTA, team="home")
#     away_team = onet.get_team(match_OPTA, team="away")
#     if home_team.team_id != copenhagen_team_id:
#         home_or_away = "away"

#     pagerank = onet.get_pagerank(match_OPTA, team=home_or_away)
#     sorted_players = sorted([(p_id, pr) for p_id, pr in pagerank.items()], key=lambda t:-t[1])
#     all_pageranked_players.append(sorted_players)

# match_weights = onet.determine_similarity(all_matches, copenhagen_team_id, exclude_subs=True)
# for pairs in zip(*match_weights):
#     for pair in pairs:
#         print(pair)
#     print()

# for players in zip(*all_pageranked_players):
#     print(players)
#     print()


# PRINT MATCH OUTCOMES

# for match_id in all_copenhagen_match_ids:
#     fname = str(match_id)
#     match_OPTA = opta.read_OPTA_f7(fpath, fname)
#     match_OPTA = opta.read_OPTA_f24(fpath, fname, match_OPTA)

#     home_or_away = "home"
#     home_team = onet.get_team(match_OPTA, team="home")
#     away_team = onet.get_team(match_OPTA, team="away")
#     if home_team.team_id != copenhagen_team_id:
#         home_or_away = "away"

#     print(match_id)
#     if home_or_away == "home":
#         print(match_OPTA.awayteam.team_id, match_OPTA.awayteam.teamname)
#         print("Copenhagen: {} v {}".format(match_OPTA.homegoals, match_OPTA.awaygoals))
#     else:
#         print(match_OPTA.hometeam.team_id, match_OPTA.hometeam.teamname)
#         print("Copenhagen: {} v {}".format(match_OPTA.awaygoals, match_OPTA.homegoals))

#     print()


# NETWORK VISUALIZATION METHODS

# copenhagen_formations = formations.read_formations_from_csv('../copenhagen_formations.csv')
# for match_id in all_copenhagen_match_ids:
#     fname = str(match_id)
#     match_OPTA = opta.read_OPTA_f7(fpath, fname)
#     match_OPTA = opta.read_OPTA_f24(fpath, fname, match_OPTA)

#     home_or_away = "home"
#     home_team = onet.get_team(match_OPTA, team="home")
#     away_team = onet.get_team(match_OPTA, team="away")
#     if home_team.team_id != copenhagen_team_id:
#         home_or_away = "away"

#     # Average Player Location
#     # ovis.plot_passing_network(match_OPTA, team=home_or_away, relative_positioning=False, display_passes=True, weighting="regular")
#     # ovis.plot_passing_network(match_OPTA, team=home_or_away, relative_positioning=True, display_passes=True, weighting="regular")

#     # Relationship Strength
#     # onet.map_weighted_passing_network(match_OPTA, team=home_or_away, exclude_subs=True, use_triplets=False, block=True)

#     # Fixed Formation
#     for formation in copenhagen_formations:
#         if formation.match_id != match_id:
#             continue

#         pass_map = onet.get_all_pass_destinations(match_OPTA, team=home_or_away, exclude_subs=False)

#         # add goalkeeper to formation representation
#         for p_id in pass_map.keys():
#             team_object = onet.get_team(match_OPTA, team=home_or_away)
#             print(p_id, team_object.player_map[p_id].position)
#             if team_object.player_map[p_id].position == "Goalkeeper":
#                 formation.add_goalkeeper(p_id)

#         formation.get_formation_graph(pass_map=pass_map)

#         eig, lat_eig = onet.get_eigenvalues(pass_map.keys(), pass_map)
#         print("Eig: {}, Lat_eig: {}".format(eig, lat_eig))

#         coeffs = onet.get_clustering_coefficients(pass_map.keys(), pass_map, weighted=True)
#         sorted_coeffs = sorted([(p_id, coeff) for p_id, coeff in coeffs.items()], key=lambda t:-t[1])
#         print("Coeffs: {}".format(sorted_coeffs))

#         pagerank = onet.get_pagerank(match_OPTA, team=home_or_away)
#         sorted_pageranks = sorted([(p_id, pr) for p_id, pr in pagerank.items()], key=lambda t:-t[1])
#         print("PageRanks: {}".format(sorted_pageranks))

###


# SHOW NETWORK WITH NODES POSITIONED BY FORMATION

copenhagen_formations = formations.read_formations_from_csv('../copenhagen_formations.csv')

# test_f = copenhagen_formations[1]
# test_f.get_formation_graph()

all_copenhagen_match_ids = [984567]

# for match_id in all_copenhagen_match_ids:
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

    for period in [0,1,2]:
        pass_map = onet.get_all_pass_destinations(match_OPTA, team=home_or_away, exclude_subs=False, half=period)

        # for p_id in pass_map.keys():
        #     print(p_id, team_object.player_map[p_id].position)
        #     if team_object.player_map[p_id].position == "Goalkeeper":
        #         formation.add_goalkeeper(p_id)

        formation.get_formation_graph(pass_map=pass_map)
