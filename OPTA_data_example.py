# -*- coding: utf-8 -*-
import OPTA_visuals as ovis
import OPTA_weighted_networks as onet
import OPTA as opta
import pickle
import matplotlib.pyplot as plt
import numpy as np
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
team = 'Copenhagen'
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

match_OPTA = opta.read_OPTA_f7(fpath, fname)
match_OPTA = opta.read_OPTA_f24(fpath, fname, match_OPTA)

onet.map_weighted_passing_network(match_OPTA, team="home", exclude_subs=False, use_triplets=False)

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

