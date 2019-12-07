# -*- coding: utf-8 -*-
import OPTA_visuals as ovis
import OPTA_weighted_networks as onet
import OPTA as opta
import pickle
import matplotlib.pyplot as plt
import numpy as np
import random
"""
Created on Tue Jul  2 11:19:49 2019

@author: laurieshaw
"""

# -*- coding: utf-8 -*-
"""
Created on Thu Jun 13 21:33:43 2019

@author: laurieshaw
"""


# fpath = "/Users/laurieshaw/Documents/Football/Data/TrackingData/Tracab/SuperLiga/All/"
# fpath = "../OPTA/"
fpath = "../Copenhagen/"
# fpath='/n/home03/lshaw/Tracking/Tracab/SuperLiga/' # path to directory of Tracab data

'''
Aalborg Match IDs
984455	SnderjyskE_vs_AalborgBK
984460	AalborgBK_vs_FCMidtjylland
984468	FCKbenhavn_vs_AalborgBK
984476	Vendsyssel_vs_AalborgBK
984481	AalborgBK_vs_FCNordsjlland
984491	ACHorsens_vs_AalborgBK
984495	AalborgBK_vs_EsbjergfB
984505	RandersFC_vs_AalborgBK
984509	AalborgBK_vs_VejleBK
984518	HobroIK_vs_AalborgBK
984523	AalborgBK_vs_OdenseBoldklub
984530	AalborgBK_vs_BrndbyIF
984539	AGFAarhus_vs_AalborgBK
984544	AalborgBK_vs_Vendsyssel
984554	FCNordsjlland_vs_AalborgBK
984558	AalborgBK_vs_FCKbenhavn
984570	VejleBK_vs_AalborgBK
984575	EsbjergfB_vs_AalborgBK
984579	AalborgBK_vs_ACHorsens
984590	OdenseBoldklub_vs_AalborgBK
984593	AalborgBK_vs_RandersFC
984602	FCMidtjylland_vs_AalborgBK
984607	AalborgBK_vs_SnderjyskE
984614	AalborgBK_vs_HobroIK
984623	BrndbyIF_vs_AalborgBK
984628	AalborgBK_vs_AGFAarhus
'''

# team = 'Aalborg BK'
team = 'FC Kbenhavn'
# match_id = 984602
# match_id = 984455
# match_id = 984456
match_id = 984468
fname = str(match_id)

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

# all_copenhagen_match_ids = [all_copenhagen_match_ids[0]]
all_copenhagen_match_ids = [984567]

for match_id in all_copenhagen_match_ids:
    fname = str(match_id)
    match_OPTA = opta.read_OPTA_f7(fpath, fname)
    match_OPTA = opta.read_OPTA_f24(fpath, fname, match_OPTA)

    home_or_away = "home"
    home_team = onet.get_team(match_OPTA, team="home")
    away_team = onet.get_team(match_OPTA, team="away")
    if home_team.team_id != copenhagen_team_id:
        home_or_away = "away"

    onet.plot_passes_vs_dist(match_OPTA, team=home_or_away, exclude_subs=False)

# Player clustering coefficients "over time"
# coefficients = {}
# eigenvalues = {}
# lat_eigenvalues = {}
# match_outcomes = []
# for match_id in all_copenhagen_match_ids:
#     fname = str(match_id)
#     match_OPTA = opta.read_OPTA_f7(fpath, fname)
#     match_OPTA = opta.read_OPTA_f24(fpath, fname, match_OPTA)

#     home_result = 0
#     if match_OPTA.homegoals > match_OPTA.awaygoals:
#         home_result = 1
#     elif match_OPTA.awaygoals > match_OPTA.homegoals:
#         home_result = -1

#     home_or_away = "home"
#     home_team = onet.get_team(match_OPTA, team="home")
#     away_team = onet.get_team(match_OPTA, team="away")
#     if home_team.team_id == copenhagen_team_id:
#         match_outcomes.append(home_result)
#     else:
#         home_or_away = "away"
#         match_outcomes.append(-home_result)

#     pass_map = onet.get_all_pass_destinations(match_OPTA, team=home_or_away, exclude_subs=True)
#     clustering_coefficients = onet.get_clustering_coefficients(pass_map.keys(), pass_map, weighted=True)
#     for p_id, coeff in clustering_coefficients.items():
#         if p_id not in coefficients.keys():
#             coefficients[p_id] = {}
#         coefficients[p_id][match_id] = coeff

#     eigenvalues[match_id], lat_eigenvalues[match_id] = onet.get_eigenvalues(pass_map.keys(), pass_map)

# x = [str(match_id) for match_id in all_copenhagen_match_ids]
# player_ids = coefficients.keys()
# ys = {p_id: [coefficients.get(p_id).get(match_id) for match_id in all_copenhagen_match_ids] for p_id in player_ids}

# color_digits = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9', 'A', 'B', 'C', 'D', 'E', 'F']

# fig, axes = plt.subplots(len(player_ids) + 3, 1, sharex='col')
# for i, p_id in enumerate(player_ids):
#     color = '#' + ''.join([random.choice(color_digits) for _ in range(6)])
#     axes[i].plot(x, ys[p_id], color=color, label="{}".format(p_id))
# axes[-3].plot(x, [eigenvalues[m_id] for m_id in all_copenhagen_match_ids], color='green', label='eig')
# axes[-2].plot(x, [lat_eigenvalues[m_id] for m_id in all_copenhagen_match_ids], color='blue', label='l_eig')
# axes[-1].plot(x, match_outcomes, color='red', label="outcomes")
# plt.xticks(rotation='vertical')
# plt.legend(loc="lower right", frameon=False)
# plt.show()

# all_pageranks = {}
# p_ids = []
# match_outcomes = []
# for match_id in all_copenhagen_match_ids:
#     fname = str(match_id)
#     match_OPTA = opta.read_OPTA_f7(fpath, fname)
#     match_OPTA = opta.read_OPTA_f24(fpath, fname, match_OPTA)

#     home_result = 0
#     if match_OPTA.homegoals > match_OPTA.awaygoals:
#         home_result = 1
#     elif match_OPTA.awaygoals > match_OPTA.homegoals:
#         home_result = -1

#     home_or_away = "home"
#     home_team = onet.get_team(match_OPTA, team="home")
#     away_team = onet.get_team(match_OPTA, team="away")
#     if home_team.team_id == copenhagen_team_id:
#         match_outcomes.append(home_result)
#     else:
#         home_or_away = "away"
#         match_outcomes.append(-home_result)

#     pagerank = onet.get_pagerank(match_OPTA, team=home_or_away)
#     print(match_id, pagerank)
#     all_pageranks[match_id] = pagerank

#     p_ids.extend(pagerank.keys())

# x = [str(match_id) for match_id in all_copenhagen_match_ids]
# player_ids = list(set(p_ids))
# ys = {p_id: [all_pageranks.get(match_id).get(p_id) for match_id in all_copenhagen_match_ids] for p_id in player_ids}

# color_digits = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9', 'A', 'B', 'C', 'D', 'E', 'F']

# fig, axes = plt.subplots(len(player_ids) + 1, 1, sharex='col')
# for i, p_id in enumerate(player_ids):
#     color = '#' + ''.join([random.choice(color_digits) for _ in range(6)])
#     axes[i].plot(x, ys[p_id], color=color, label="{}".format(p_id))
# axes[-1].plot(x, match_outcomes, color='red', label="outcomes")
# plt.xticks(rotation='vertical')
# plt.legend(loc="lower right", frameon=False)
# plt.show()

# PLOT AND SAVE ALL WEIGHTED PASSING NETWORKS
# for match_id in all_copenhagen_match_ids:
#     fname = str(match_id)
#     match_OPTA = opta.read_OPTA_f7(fpath, fname)
#     match_OPTA = opta.read_OPTA_f24(fpath, fname, match_OPTA)
#     home_or_away = "home"
#     home_team_id = onet.get_team(match_OPTA, team="home").team_id
#     if home_team_id != copenhagen_team_id:
#         home_or_away = "away"
#     print(onet.find_player_triplets(match_OPTA, team=home_or_away, exclude_subs=True))
#     onet.map_weighted_passing_network(match_OPTA, team=home_or_away, exclude_subs=True, use_triplets=True, block=True)
#     # plt.savefig("weighted_networks_nosubs_triplets/{}_weighted_network.png".format(fname), format='png')
#     plt.clf()

# ovis.plot_all_shots(match_OPTA, plotly=False)
# ovis.make_expG_timeline(match_OPTA)
# # ovis.plot_defensive_actions(team,[match_OPTA],include_tackles=True,include_intercept=True)

# ovis.plot_all_passes(match_OPTA)
# ovis.plot_passing_network(match_OPTA, relative_positioning=True, display_passes=True, weighting="regular")
# ovis.ball_movie(match_OPTA, relative_positioning=False, team="away")
# ovis.get_player_positions(match_OPTA, relative_positioning=True, team="home", weighting="regular", show_determiners=True)
# ovis.find_player_triplets(match_OPTA, relative_positioning=False, team="home", weighting="regular")

# sample_games = [984456, 984457, 984458, 984459, 984460, 984461, 984462, 984463, 984464]
# sample_games = [984455]
# # # fails 984462 and 984464
# for m_id in sample_games:
#     try:
#         fname = str(m_id)
#         match_OPTA = opta.read_OPTA_f7(fpath, fname)
#         match_OPTA = opta.read_OPTA_f24(fpath, fname, match_OPTA)
#         ovis.plot_passing_network(match_OPTA, relative_positioning=True, team="home", display_passes=True, weighting="regular", wait=False)
#         plt.savefig('{}_network_H_relative.png'.format(m_id), format='png')

#         ovis.plot_passing_network(match_OPTA, relative_positioning=True, team="away", display_passes=True, weighting="regular", wait=False)
#         plt.savefig('{}_network_A_relative.png'.format(m_id), format='png')

#         ovis.plot_passing_network(match_OPTA, relative_positioning=False, team="home", display_passes=True, weighting="regular", wait=False)
#         plt.savefig('{}_network_H_average.png'.format(m_id), format='png')

#         ovis.plot_passing_network(match_OPTA, relative_positioning=False, team="away", display_passes=True, weighting="regular", wait=False)
#         plt.savefig('{}_network_A_average.png'.format(m_id), format='png')
#     except KeyError:
#         print("failed {}".format(m_id))

