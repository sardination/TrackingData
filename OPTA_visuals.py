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


def get_player_positions(match_OPTA, relative_positioning=True, team="home", weighting="regular"):
    """
    Fills in the x, y, and cov of each player object for the specified team

    Args:
        match_OPTA (OPTAmatch)
        relative_positioning (bool): whether we want average or relative positioning
        team (string): team to get player locations for
    """
    team_object = match_OPTA.hometeam if team == "home" else match_OPTA.awayteam

    events_raw = [e for e in team_object.events if e.is_pass or e.is_shot or e.is_substitution]
    xfact = match_OPTA.fPitchXSizeMeters*100
    yfact = match_OPTA.fPitchYSizeMeters*100

    player_objects = {p.id: p for p in team_object.players}

    # dictionary of the sum of outgoing pass vectors from each player to each other player
    player_vectors = {}

    # dictionary of np arrays of (x,y) locations
    player_locations = {}

    last_pass = None
    exclude_players = []
    for e in events_raw:
        if e.is_substitution:
            if e.sub_direction == "on":
                exclude_players.append(e.player_id)
                print(player_objects[e.player_id])
            continue
        # Record player location of pass/shot originator
        if player_locations.get(e.player_id) is not None:
            if e.is_shot:
                if weighting != "defensive":
                    player_locations[e.player_id] = np.append(
                        player_locations[e.player_id],
                        [[e.x, e.y]],
                        axis=0
                    )
            elif weighting == "regular" or weighting in e.pass_types:
                player_locations[e.player_id] = np.append(
                    player_locations[e.player_id],
                    [[e.pass_start[0], e.pass_start[1]]],
                    axis=0
                )
        else:
            if e.is_shot:
                if weighting != "defensive":
                    player_locations[e.player_id] = np.array([[e.x, e.y]])
            elif weighting == "regular" or weighting in e.pass_types:
                player_locations[e.player_id] = np.array([[e.pass_start[0], e.pass_start[1]]])

        # Record player location of pass target if the last pass was completed and this is the next action
        if last_pass is not None:
            if team_object.player_map[last_pass.player_id].pass_destinations.get(e.player_id):
                team_object.player_map[last_pass.player_id].pass_destinations[e.player_id] += 1
            else:
                team_object.player_map[last_pass.player_id].pass_destinations[e.player_id] = 1

            if player_locations.get(e.player_id) is not None:
                player_locations[e.player_id] = np.append(
                    player_locations[e.player_id],
                    [[last_pass.pass_end[0], last_pass.pass_end[1]]],
                    axis=0
                )
            else:
                player_locations[e.player_id] = np.array([[last_pass.pass_end[0], last_pass.pass_end[1]]])

            # sum outgoing vectors for every player
            if player_vectors.get(last_pass.player_id) is None:
                player_vectors[last_pass.player_id] = {}
            if player_vectors[last_pass.player_id].get(e.player_id) is None:
                player_vectors[last_pass.player_id][e.player_id] = np.array([0.0, 0.0])
            player_vectors[last_pass.player_id][e.player_id] += np.array(last_pass.pass_end) - np.array(last_pass.pass_start)

        if e.is_pass and e.outcome == 1 and (weighting == "regular" or weighting in e.pass_types):
            last_pass = e
        else:
            last_pass = None

    # factor locations to plot positions
    for player_id, _ in player_locations.items():
        player_locations[player_id] = player_locations[player_id] * [xfact, yfact]

    mapped_players = [p for p in match_OPTA.hometeam.players if player_locations.get(p.id) is not None and p.id not in exclude_players]
    outgoing_passes = {p.id: sum([d_num for p_id, d_num in p.pass_destinations.items()]) for p in mapped_players}
    incoming_passes = {p.id: 0 for p in mapped_players}

    for r_p in mapped_players:
        for s_p in mapped_players:
            incoming_passes[r_p.id] += s_p.pass_destinations.get(r_p) if s_p.pass_destinations.get(r_p) is not None else 0

    if relative_positioning:
        # sort players by outgoing passes and get max outgoing pass player
        top_passers = sorted(
            [p for p in mapped_players],
            key=lambda x:-(max(outgoing_passes[x.id], incoming_passes[x.id]))
        )
        top_passer = top_passers[0]
        player_loc_mean = np.mean(
            player_locations[top_passer.id],
            axis=0
        )
        top_passer.x = player_loc_mean[0]
        top_passer.y = player_loc_mean[1]

        while len(top_passers) > 1:
            top_passers.remove(top_passer)

            # players receiving passes from top_passer
            top_receivers_from_current = [(p_id, n) for p_id, n in sorted(
                [(r,n) for r,n in top_passer.pass_destinations.items()],
                key=lambda x:-x[1]
            )]

            # players passing to top_passer
            top_passers_to_current = [(p_id, n) for p_id, n in sorted(
                [(p.id, p.pass_destinations.get(top_passer.id)) for p in mapped_players if p.pass_destinations.get(top_passer.id) is not None],
                key=lambda x:-x[1]
            )]

            next_passer = None
            is_receiver = False

            top_num_passes = 0
            for receiver_id, n in top_receivers_from_current:
                receiver = player_objects[receiver_id]
                if receiver_id not in exclude_players and receiver in top_passers:
                    next_passer = receiver
                    top_num_passes = n
                    break

            for passer_id, n in top_passers_to_current:
                passer = player_objects[passer_id]
                if passer_id not in exclude_players and passer in top_passers:
                    if n > top_num_passes:
                        next_passer = passer
                        top_num_passes = n
                        is_receiver = True
                    break

            if next_passer is not None:
                top_receivers_from_next = [(p_id, n) for p_id, n in sorted(
                    [(r,n) for r,n in next_passer.pass_destinations.items()],
                    key=lambda x:-x[1]
                )]

                top_passers_to_next = [(p_id, n) for p_id, n in sorted(
                    [(p.id, p.pass_destinations.get(next_passer.id)) for p in mapped_players if p.pass_destinations.get(next_passer.id) is not None],
                    key=lambda x:-x[1]
                )]

                top_num_passes = 0
                for receiver_id, n in top_receivers_from_next:
                    receiver = player_objects[receiver_id]
                    if receiver_id not in exclude_players and receiver not in top_passers:
                        top_passer = receiver
                        top_num_passes = n
                        is_receiver = True
                        break
                for passer_id, n in top_passers_to_next:
                    passer = player_objects[passer_id]
                    if passer_id not in exclude_players and passer not in top_passers:
                        if n > top_num_passes:
                            top_passer = passer
                            top_num_passes = n
                            is_receiver = False
                        break

                if is_receiver:
                    average_pass_vector = -np.array(player_vectors[next_passer.id][top_passer.id]) / next_passer.pass_destinations[top_passer.id]
                else:
                    average_pass_vector = np.array(player_vectors[top_passer.id][next_passer.id]) / top_passer.pass_destinations[next_passer.id]
                next_passer.x = top_passer.x + average_pass_vector[0] * xfact
                next_passer.y = top_passer.y + average_pass_vector[1] * yfact
            else:
                next_passer = top_passers[0]
                player_loc_mean = np.mean(
                    player_locations[next_passer.id],
                    axis=0
                )
                next_passer.x = player_loc_mean[0]
                next_passer.y = player_loc_mean[1]

            top_passer = next_passer


    for player in team_object.players:
        player_id = player.id
        if player not in mapped_players:
            continue

        # Calculate mean and covariance of player locations and graph bivariate normal ellipse of player position

        # if not using relative positioning vectors, set player x and y values using means
        if not relative_positioning:
            player_loc_mean = np.mean(
                player_locations[player_id],
                axis=0
            )
            player.x = player_loc_mean[0]
            player.y = player_loc_mean[1]

        player.cov = np.cov(
            player_locations[player_id][:,0],
            player_locations[player_id][:,1]
        )

    return mapped_players


def plot_passing_network(match_OPTA, weighting="regular", relative_positioning=True, display_passes=True):
    """
    Plot the passing networks of the entire match, displaying player movement as bivariate normal
    ellipses and arrow weights directly corresponding to the number of passes executed

    TODO:
    - account for subs
    - allow different weighting schema

    Args:
        match_OPTA (OPTAmatch): match OPTA information

    Kwargs:
        weighting (string): type of pass network. Choices include:
            regular - all passes included and weighted
            offensive - weight offensive passes but not defensive
            defensive - weight defensive passes but not offensive
            lateral - weight passes with minimal progression in either direction on the field
            forwards - weight passes in the offensive direction
            backwards - weight passes in the defensive direction
        relative_positioning (bool): if True, player positions on the diagram should be relative
            in terms of formation rather than exact position average
    """

    fig, ax = vis.plot_pitch(match_OPTA)
    # some passes may be completed and followed by a shot instead of another pass
    home_events_raw = [e for e in match_OPTA.hometeam.events if e.is_pass or e.is_shot or e.is_substitution]
    away_events_raw = [e for e in match_OPTA.awayteam.events if e.is_pass or e.is_shot or e.is_substitution]
    xfact = match_OPTA.fPitchXSizeMeters*100
    yfact = match_OPTA.fPitchYSizeMeters*100

    home_mapped_players = get_player_positions(
        match_OPTA,
        relative_positioning=relative_positioning,
        team="home",
        weighting=weighting
    )

    for player in home_mapped_players:
        shrink_factor = 0.25
        fig, ax, pt = utils.plot_bivariate_normal(
            [player.x, player.y],
            player.cov * shrink_factor**2,
            figax=(fig, ax)
        )
        ax.annotate(
            match_OPTA.hometeam.player_map[player.id].lastname,
            (player.x, player.y)
        )

    if display_passes:
        # Plot network of passes with arrows
        for player in match_OPTA.hometeam.players:
            # if player in exclude_players:
            if player not in home_mapped_players:
                continue
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
                # if dest_player in exclude_players:
                if dest_player not in home_mapped_players:
                    continue
                arrow = patches.FancyArrowPatch(
                    (player.x, player.y),
                    (dest_player.x, dest_player.y),
                    connectionstyle="arc3,rad=.1",
                    color='r',
                    arrowstyle='Simple,tail_width=0.5,head_width=4,head_length=8',
                    linewidth=num_passes*0.8,
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
