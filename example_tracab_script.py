# -*- coding: utf-8 -*-
"""
Created on Thu Mar  7 16:57:45 2019

@author: laurieshaw
"""

import Tracab as tracab
import Tracking_Visuals as vis
import numpy as np
import matplotlib.pyplot as plt

fpath='/PATH/TO/YOUR/TRACAB/DATA/DIRECTORY/' # path to directory of Tracab data
fname = "Brighton and Hove AlbionBournemouth2018-12-22T15,00,00Z.txt.g987762" # filename of Tracab match

# read frames, match meta data, and data for individual players
frames_tb, match_tb, team1_players, team0_players = tracab.read_tracab_match_data(fpath,fname,verbose=True)
# frames is a list of the individual match snapshots (positions, velocities)
# match contains some metadata (pitch dimensions, etc)
# team1_players is a dictionary of the home team players (containing arrays of their positions/velocities over the match)
# team0_players is a dictionary of the away team players (containing arrays of their positions/velocities over the match)

# plot the pitch, players and ball in a single frame
fig,ax = vis.plot_frame(frames_tb[1000],match_tb,include_player_velocities=True,include_ball_velocities=False)

# get all frames between the 19th and 21st minute in the first half
tstart = (1,19)
tend = (1,21)
frames_in_segment = vis.get_frames_between_timestamps(frames_tb,match_tb,tstart,tend)

# plot the pitch over several frames (frame rate is determined by the 'pause' parameter. This is mostly useful for debugging
# vis.plot_frames(frames_in_segment,match_tb,pause=0.01,include_player_velocities=True,include_ball_velocities=False)

# even bettermake a movie of a list of frames and save it in fpath
vis.save_match_clip(frames_in_segment,match_tb,fpath=fpath,fname='my_test_movie',include_player_velocities=False) 

# make a plot of a player 2's position (home team) over the first half
# it shows you how to access the positions/velocities of a given player over time
fig,ax = vis.plot_pitch(match_tb) # plot pitch
px = np.array( [f.pos_x for f in team1_players[2].frame_targets] )
py = np.array( [f.pos_y for f in team1_players[2].frame_targets] )
t = np.array(  team1_players[2].frame_timestamps )
flast = vis.find_framenum_at_timestamp(frames_tb,match_tb,2,0) # first frame of second half
ax.plot( px[0:flast],py[0:flast],'r.')

# make a timeseries plot of player 2's velocity (x and y components) and speed over the first half
vx = np.array( [f.vx for f in team1_players[2].frame_targets] )
vy = np.array( [f.vy for f in team1_players[2].frame_targets] )
fig,ax = plt.subplots()
ax.plot( t[0:flast], vx[0:flast], 'r' )
ax.plot( t[0:flast], vy[0:flast], 'b' )

# make a histogram of player 2's total speed over the first half
fig,ax = plt.subplots()
vtot = np.array( [f.speed_filter for f in team1_players[2].frame_targets if f.speed_filter >= 0] ) # need to remove nans
ax.hist(vtot[0:flast],np.linspace(0,10,20))


