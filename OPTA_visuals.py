# -*- coding: utf-8 -*-
"""
Created on Tue Aug 13 17:08:14 2019

@author: laurieshaw
"""

import OPTA as opta
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import chart_studio.plotly as py
import chart_studio.tools as tls
import Tracking_Visuals as vis
import data_utils as utils


def get_all_matches():
    # get all matches in a range (for testing)
    ids = np.arange(984455, 984635)
    # fpath = "/Users/laurieshaw/Documents/Football/Data/TrackingData/Tracab/SuperLiga/All/"
    fpath = "../OPTA/"
    matches = []
    for i in ids:
        try:
            match_OPTA = opta.read_OPTA_f7(fpath, str(i))
            match_OPTA = opta.read_OPTA_f24(fpath, str(i), match_OPTA)
            matches.append(match_OPTA)
            print(i)
        except:
            print("error in %d" % (i))
    return matches


def plot_passing_network(match_OPTA):
    """
    Plot the passing networks of the entire match, displaying player movement as bivariate normal
    ellipses and arrow weights directly corresponding to the number of passes executed

    TODO:
    - account for subs
    - allow different weighting schema

    Args:
        match_OPTA (OPTAmatch): match OPTA information

    Kwargs:

    """

    fig, ax = vis.plot_pitch(match_OPTA)
    # some passes may be completed and followed by a shot instead of another pass
    home_events_raw = [e for e in match_OPTA.hometeam.events if e.is_pass or e.is_shot]
    away_events_raw = [e for e in match_OPTA.awayteam.events if e.is_pass or e.is_shot]
    xfact = match_OPTA.fPitchXSizeMeters*100
    yfact = match_OPTA.fPitchYSizeMeters*100

    # dictionary of np arrays of (x,y) locations
    home_player_locations = {}
    away_player_locations = {}

    last_pass = None
    for p in home_events_raw:
        # Record player location of pass/shot originator
        if home_player_locations.get(p.player_id) is not None:
            if p.is_shot:
                home_player_locations[p.player_id] = np.append(
                    home_player_locations[p.player_id],
                    [[p.x, p.y]],
                    axis=0
                )
            else:
                home_player_locations[p.player_id] = np.append(
                    home_player_locations[p.player_id],
                    [[p.pass_start[0], p.pass_start[1]]],
                    axis=0
                )
        else:
            if p.is_shot:
                home_player_locations[p.player_id] = np.array([[p.x, p.y]])
            else:
                home_player_locations[p.player_id] = np.array([[p.pass_start[0], p.pass_start[1]]])

        # Record player location of pass target if the last pass was completed and this is the next action
        if last_pass is not None:
            if match_OPTA.hometeam.player_map[last_pass.player_id].pass_destinations.get(p.player_id):
                match_OPTA.hometeam.player_map[last_pass.player_id].pass_destinations[p.player_id] += 1
            else:
                match_OPTA.hometeam.player_map[last_pass.player_id].pass_destinations[p.player_id] = 1

            home_player_locations[p.player_id] = np.append(
                home_player_locations[p.player_id],
                [[last_pass.pass_end[0], last_pass.pass_end[1]]],
                axis=0
            )

        if p.is_pass and p.outcome == 1:
            last_pass = p
        else:
            last_pass = None

    for player in match_OPTA.hometeam.players:
        player_id = player.id
        location_sum = home_player_locations.get(player_id)
        if location_sum is None:
            continue

        home_player_locations[player_id] = home_player_locations[player_id] * [xfact, yfact]

        # Calculate mean and covariance of player locations and graph bivariate normal ellipse of player position
        player_loc_mean = np.mean(
            home_player_locations[player_id],
            axis=0
        )
        player.x = player_loc_mean[0]
        player.y = player_loc_mean[1]

        player_loc_cov = np.cov(
            home_player_locations[player_id][:,0],
            home_player_locations[player_id][:,1]
        )

        shrink_factor = 0.25
        fig, ax, pt = utils.plot_bivariate_normal(
            player_loc_mean,
            player_loc_cov * shrink_factor**2,
            figax=(fig, ax)
        )
        ax.annotate(
            match_OPTA.hometeam.player_map[player_id].lastname,
            (player_loc_mean[0], player_loc_mean[1])
        )

    # Plot network of passes with arrows
    for player in match_OPTA.hometeam.players:
        for dest_player_id, num_passes in player.pass_destinations.items():
            dest_player = match_OPTA.hometeam.player_map[dest_player_id]
            # ax.arrow(
            #     player.x,
            #     player.y,
            #     (dest_player.x - player.x),
            #     (dest_player.y - player.y),
            #     color='r',
            #     length_includes_head=True,
            #     # head_width=0.08*xfact,
            #     # head_length=0.00002*yfact,
            #     width = num_passes * 10
            # )
            arrow = patches.FancyArrowPatch(
                (player.x, player.y),
                (dest_player.x, dest_player.y),
                connectionstyle="arc3,rad=.1",
                color='r',
                arrowstyle='Simple,tail_width=0.5,head_width=4,head_length=8',
                linewidth=num_passes,
            )
            ax.add_artist(arrow)

    match_string = '%s %d vs %d %s' % (
        match_OPTA.hometeam.teamname,
        match_OPTA.homegoals,
        match_OPTA.awaygoals,
        match_OPTA.awayteam.teamname
    )
    plt.title(match_string, fontsize=16, y=1.0)
    plt.waitforbuttonpress(0)

    return fig, ax


def plot_all_passes(match_OPTA):
    fig, ax = vis.plot_pitch(match_OPTA)
    home_passes = [e for e in match_OPTA.hometeam.events if e.is_pass]
    away_passes = [e for e in match_OPTA.awayteam.events if e.is_pass]
    xfact = match_OPTA.fPitchXSizeMeters*100
    yfact = match_OPTA.fPitchYSizeMeters*100

    for p in home_passes:
        ax.arrow(
            p.pass_start[0]*xfact,
            p.pass_start[1]*yfact,
            (p.pass_end[0] - p.pass_start[0])*xfact,
            (p.pass_end[1] - p.pass_start[1])*yfact,
            color='b',
            length_includes_head=True,
            head_width=0.08*xfact,
            head_length=0.00002*yfact
        )

    for p in away_passes:
        ax.arrow(
            p.pass_start[0]*xfact,
            p.pass_start[1]*yfact,
            (p.pass_end[0] - p.pass_start[0])*xfact,
            (p.pass_end[1] - p.pass_start[1])*yfact,
            color='r',
            length_includes_head=True,
            head_width=0.08*xfact,
            head_length=0.00002*yfact
        )

    match_string = '%s %d vs %d %s' % (
        match_OPTA.hometeam.teamname,
        match_OPTA.homegoals,
        match_OPTA.awaygoals,
        match_OPTA.awayteam.teamname
    )

    plt.title(match_string, fontsize=16, y=1.0)
    plt.waitforbuttonpress(0)

    return fig, ax


def xG_calibration_plots(matches, caley_type=[1, 2, 3, 4, 5, 6], bins=np.linspace(0, 1, 11)):
    # poal probability in bins of xG
    shots = []
    for match in matches:
        shots = shots + [e for e in match.hometeam.events if e.is_shot] + \
            [e for e in match.awayteam.events if e.is_shot]
    xG_caley = [shot for shot in shots if shot.caley_types in caley_type]
    xG_caley2 = [shot for shot in shots if shot.caley_types2 in caley_type]
    xG_total_caley = np.sum([s.expG_caley for s in xG_caley])
    xG_total_caley2 = np.sum([s.expG_caley2 for s in xG_caley2])
    G_total = np.sum([s.is_goal for s in xG_caley])
    G_total2 = np.sum([s.is_goal for s in xG_caley2])
    print("xG_caley1: %1.2f, xG: %1.2f, goals = %d, %d" %
          (xG_total_caley, xG_total_caley2, G_total, G_total2))
    binned_xG_caley = np.zeros(shape=len(bins)-1)
    binned_xG_caley2 = np.zeros(shape=len(bins)-1)
    pgoal_caley = np.zeros(shape=len(bins)-1)
    pgoal_caley2 = np.zeros(shape=len(bins)-1)
    n_caley = np.zeros(shape=len(bins)-1)
    for i, b in enumerate(bins[:-1]):
        binned_xG_caley[i] = np.mean(
            [s.expG_caley for s in xG_caley if s.expG_caley >= b and s.expG_caley <= bins[i+1]])
        binned_xG_caley2[i] = np.mean(
            [s.expG_caley2 for s in xG_caley2 if s.expG_caley2 >= b and s.expG_caley2 <= bins[i+1]])
        pgoal_caley[i] = np.mean(
            [s.is_goal for s in xG_caley if s.expG_caley >= b and s.expG_caley <= bins[i+1]])
        pgoal_caley2[i] = np.mean(
            [s.is_goal for s in xG_caley2 if s.expG_caley2 >= b and s.expG_caley2 <= bins[i+1]])
        n_caley[i] = float(
            len([s for s in xG_caley if s.expG_caley >= b and s.expG_caley <= bins[i+1]]))
    fig, ax = plt.subplots()
    std = np.sqrt(pgoal_caley2*(1-pgoal_caley2)/n_caley)

    ax.errorbar(binned_xG_caley2, pgoal_caley2, 2*std)
    ax.plot(binned_xG_caley, pgoal_caley, 'r')
    ax.plot([0, 1], [0, 1], 'k--')
    plt.waitforbuttonpress(0)


def plot_all_shots(match_OPTA, plotly=False):
    def symbols(x): return 'd' if x == 'Goal' else 'o'
    fig, ax = vis.plot_pitch(match_OPTA)
    homeshots = [e for e in match_OPTA.hometeam.events if e.is_shot]
    awayshots = [e for e in match_OPTA.awayteam.events if e.is_shot]
    xfact = match_OPTA.fPitchXSizeMeters*100
    yfact = match_OPTA.fPitchYSizeMeters*100
    descriptors = {}
    count = 0
    for shot in homeshots:
        descriptors[str(count)] = shot.shot_descriptor
        ax.plot(shot.x*xfact, shot.y*yfact, 'r'+symbols(shot.description),
                alpha=0.6, markersize=20*np.sqrt(shot.expG_caley), label=count)
        count += 1
    for shot in awayshots:
        descriptors[str(count)] = shot.shot_descriptor
        ax.plot(-1*shot.x*xfact, -1*shot.y*yfact, 'b'+symbols(shot.description),
                alpha=0.6, markersize=20*np.sqrt(shot.expG_caley), label=count)
        count += 1
    home_xG = np.sum([s.expG_caley2 for s in homeshots])
    away_xG = np.sum([s.expG_caley2 for s in awayshots])
    match_string = '%s %d (%1.1f) vs (%1.1f) %d %s' % (match_OPTA.hometeam.teamname,
                                                       match_OPTA.homegoals, home_xG, away_xG, match_OPTA.awaygoals, match_OPTA.awayteam.teamname)
    # ax.text(-75*len(match_string),match_OPTA.fPitchYSizeMeters*50+500,match_string,fontsize=20)

    if plotly:
        plt.title(match_string, fontsize=20, y=0.95)
        plotly_fig = tls.mpl_to_plotly(fig)
        for d in plotly_fig.data:
            if d['name'] in descriptors.keys():
                d['text'] = descriptors[d['name']]
                d['hoverinfo'] = 'text'
            else:
                d['name'] = ""
                d['hoverinfo'] = 'name'

        plotly_fig['layout']['titlefont'].update(
            {'color': 'black', 'size': 20, 'family': 'monospace'})
        plotly_fig['layout']['xaxis'].update(
            {'ticks': '', 'showticklabels': False})
        plotly_fig['layout']['yaxis'].update(
            {'ticks': '', 'showticklabels': False})
        #url = py.plot(plotly_fig, filename = 'Aalborg-match-analysis')
        plt.waitforbuttonpress(0)
        return plotly_fig
    else:
        plt.title(match_string, fontsize=16, y=1.0)
        plt.waitforbuttonpress(0)
        return fig, ax


def make_expG_timeline(match_OPTA):
    fig, ax = plt.subplots()
    homeshots = [e for e in match_OPTA.hometeam.events if e.is_shot]
    awayshots = [e for e in match_OPTA.awayteam.events if e.is_shot]
    homeshots = sorted(homeshots, key=lambda x: x.time)
    awayshots = sorted(awayshots, key=lambda x: x.time)
    homeshot_expG = [s.expG_caley2 for s in homeshots]
    awayshot_expG = [s.expG_caley2 for s in awayshots]
    home_xG = np.sum(homeshot_expG)
    away_xG = np.sum(awayshot_expG)
    homeshot_time = [s.time for s in homeshots]
    awayshot_time = [s.time for s in awayshots]
    homegoal_times = [s.time for s in homeshots if s.is_goal]
    awaygoal_times = [s.time for s in awayshots if s.is_goal]
    homegoal_xG_totals = [np.sum(
        [s.expG_caley2 for s in homeshots if s.time <= t]) for t in homegoal_times]
    awaygoal_xG_totals = [np.sum(
        [s.expG_caley2 for s in awayshots if s.time <= t]) for t in awaygoal_times]
    # for step chart
    homeshot_time = [0] + homeshot_time + [match_OPTA.total_match_time]
    awayshot_time = [0] + awayshot_time + [match_OPTA.total_match_time]
    homeshot_expG = [0] + homeshot_expG + [0.0]
    awayshot_expG = [0] + awayshot_expG + [0.0]
    plt.step(homeshot_time, np.cumsum(homeshot_expG), 'r', where='post')
    plt.step(awayshot_time, np.cumsum(awayshot_expG), 'b', where='post')
    ax.set_xticks(np.arange(0, 100, 10))
    ax.xaxis.grid(alpha=0.5)
    ax.yaxis.grid(alpha=0.5)
    match_string = '%s %d (%1.1f) vs (%1.1f) %d %s' % (match_OPTA.hometeam.teamname,
                                                       match_OPTA.homegoals, home_xG, away_xG, match_OPTA.awaygoals, match_OPTA.awayteam.teamname)
    fig.suptitle(match_string, fontsize=16, y=0.95)
    ax.set_xlim(0, match_OPTA.total_match_time)
    ymax = np.ceil([max(home_xG, away_xG)])
    ax.set_ylim(0, ymax)
    ax.text(match_OPTA.total_match_time+1, home_xG,
            match_OPTA.hometeam.teamname, color='r')
    ax.text(match_OPTA.total_match_time+1, away_xG,
            match_OPTA.awayteam.teamname, color='b')
    ax.set_ylabel('Cummulative xG', fontsize=14)
    ax.set_xlabel('Match time', fontsize=14)
    print(homegoal_times, homegoal_xG_totals)
    ax.plot(homegoal_times, homegoal_xG_totals, 'ro')
    ax.plot(awaygoal_times, awaygoal_xG_totals, 'bo')
    # add goal scorers
    home_scorers = ['Goal (' + str(s.player_name) +
                    ')' for s in homeshots if s.is_goal]
    away_scorers = ['Goal (' + str(s.player_name) +
                    ')' for s in awayshots if s.is_goal]
    if len(home_scorers) > 0:
        [ax.text(t-0.2, x, n, horizontalalignment='right', fontsize=8, color='r')
         for t, x, n in zip(homegoal_times, homegoal_xG_totals, home_scorers)]
    if len(away_scorers) > 0:
        [ax.text(t-0.2, x, n, horizontalalignment='right', fontsize=8, color='b')
         for t, x, n in zip(awaygoal_times, awaygoal_xG_totals, away_scorers)]

    plt.waitforbuttonpress(0)


def plot_defensive_actions(team, all_matches, include_tackles=True, include_intercept=True):
    match_OPTA = all_matches[0]
    # tackles won and retained posession
    team_events = []
    for match in all_matches:
        if match.hometeam.teamname == team:
            team_events += match.hometeam.events
        elif match.awayteam.teamname == team:
            team_events += match.awayteam.events
    tackle_won = [e for e in team_events if e.type_id ==
                  7 and e.outcome == 1 and 167 not in e.qual_id_list]
    # interceptions
    intercepts = [e for e in team_events if e.type_id == 8]
    fig, ax = vis.plot_pitch(all_matches[0])
    xfact = match_OPTA.fPitchXSizeMeters*100
    yfact = match_OPTA.fPitchYSizeMeters*100
    count = 0
    # tackles
    if include_tackles:
        for tackle in tackle_won:
            ax.plot(tackle.x*xfact, tackle.y*yfact, 'rd',
                    alpha=0.6, markersize=10, label=count)
            count += 1
    if include_intercept:
        for intercept in intercepts:
            ax.plot(intercept.x*xfact, intercept.y*yfact, 'rs',
                    alpha=0.6, markersize=10, label=count)
            count += 1
    #match_string = '%s %d (%1.1f) vs (%1.1f) %d %s' % (match_OPTA.hometeam.teamname,match_OPTA.homegoals,home_xG,away_xG,match_OPTA.awaygoals,match_OPTA.awayteam.teamname)
    #plt.title( match_string, fontsize=16, y=1.0 )
    plt.waitforbuttonpress(0)


def Generate_Tracab_Chance_Videos(match_OPTA, match_tb, frames_tb):
    t_init_buf = 0.5
    t_end_buf = 0.1
    match_end = frames_tb[-1].timestamp
    all_shots = [e for e in match_OPTA.hometeam.events if e.is_shot] + \
        [e for e in match_OPTA.awayteam.events if e.is_shot]
    for shot in all_shots:
        print(shot)
        tstart = (shot.period_id, max(0.0, shot.time -
                                      45*(shot.period_id-1) - t_init_buf))
        tend = (shot.period_id, min(match_end, shot.time -
                                    45*(shot.period_id-1) + t_end_buf))
        frames_in_segment = vis.get_frames_between_timestamps(
            frames_tb, match_tb, tstart, tend)
        vis.save_match_clip(frames_in_segment, match_tb, fpath=match_OPTA.fpath+'/chances/',
                            fname=shot.shot_id, include_player_velocities=False, description=shot.shot_descriptor)
