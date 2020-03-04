import centrality
import OPTA as opta
import OPTA_weighted_networks as onet

import matplotlib.colors as mpl_colors
import matplotlib.pyplot as plt
import numpy as np


def plot_closeness_vs_betweenness(match_OPTA, team_id, match_id=None):
    """
    For a single team in a single match, closeness on the x-axis
    and betweenness on the y-axis
    """

    team_object = match_OPTA.team_map.get(team_id)
    if team_object is None:
        print("Team not in match")
        return
    home_or_away = "home" if team_object == match_OPTA.hometeam else "away"

    player_times = team_object.get_on_pitch_periods()

    # role_grouped = True
    # for period in [0, 1, 2]:
    for period in [0]:
        pass_map = onet.get_all_pass_destinations(match_OPTA, team=home_or_away, exclude_subs=False, half=period)

        graphs = centrality.get_directed_graphs(
            pass_map,
            player_times,
            team_object,
            role_grouped=True,
            period=period
        )

        betweenness = centrality.current_flow_betweenness_directed(
            graphs['scaled_graph'],
            start_node=1
        )

        closeness = centrality.current_flow_closeness_directed(
            graphs['scaled_graph'],
            start_node=1
        )

        players = graphs['scaled_graph'].nodes()
        x = [closeness[p] for p in players]
        y = [betweenness[p] for p in players]


        fig, ax = plt.subplots()
        ax.set_xlabel("closeness")
        ax.set_ylabel("betweenness")
        ax.set_title("Match {} Team {}".format(match_id, team_id))
        ax.set_xlim([1, 3])
        ax.set_ylim([0, 0.8])

        ax.scatter(x, y)
        for i, p_id in enumerate(players):
            ax.annotate(p_id, (x[i], y[i]))

        plt.show()


def plot_cross_match_centrality(matches, team_id, metric="closeness"):
    """
    Plot one centrality measure of two matches against each other on
    opposing axes.

    Args:
        matches (dict): keyed by match_id, values are matchOPTA objects
        team_id (int): ID for the team in questions
    Kwargs:
        metric (string): the metric used for the match-to-match comparison
    """

    allowed_metrics = {
        "closeness": centrality.current_flow_closeness_directed,
        "betweenness": centrality.current_flow_betweenness_directed
    }
    metric_function = allowed_metrics.get(metric)
    if metric_function is None:
        raise("Unallowed metric")

    match_ids = list(matches.keys())[:2]
    if len(match_ids) != 2:
        raise("Fewer than two matches passed in")

    metric_results = {}

    players = set()
    for match_id in match_ids:
        match_OPTA = matches[match_id]

        team_object = match_OPTA.team_map.get(team_id)
        if team_object is None:
            raise("Team not in match")

        home_or_away = "home" if team_object == match_OPTA.hometeam else "away"

        player_times = team_object.get_on_pitch_periods()

        pass_map = onet.get_all_pass_destinations(match_OPTA, team=home_or_away, exclude_subs=False, half=0)

        graphs = centrality.get_directed_graphs(
            pass_map,
            player_times,
            team_object,
            role_grouped=True,
            period=0
        )
        players = players.union(set(graphs['scaled_graph'].nodes()))

        metric_results[match_id] = metric_function(
            graphs['scaled_graph'],
            start_node=1
        )

    players = list(players)

    x = [metric_results[match_ids[0]].get(p) if p in metric_results[match_ids[0]].keys() else 0 for p in players]
    y = [metric_results[match_ids[1]].get(p) if p in metric_results[match_ids[1]].keys() else 0 for p in players]

    fig, ax = plt.subplots()
    ax.set_xlabel("Match {} {}".format(
        match_ids[0],
        metric
    ))
    ax.set_ylabel("Match {} {}".format(
        match_ids[1],
        metric
    ))
    ax.set_title("Team {}".format(team_id))

    if metric == "closeness":
        ax.set_xlim([1, 3])
        ax.set_ylim([1, 3])
    elif metric == "betweenness":
        ax.set_xlim([0, 0.8])
        ax.set_ylim([0, 0.8])

    # draw center line
    line_x_vals = [
        min(set(x).union(set(y))),
        max(set(x).union(set(y)))
    ]
    line_y_vals = line_x_vals
    plt.plot(line_x_vals, line_y_vals, '--', color='r')

    ax.scatter(x, y)
    for i, p_id in enumerate(players):
        ax.annotate(p_id, (x[i], y[i]))

    plt.show()


def adjacency_heatmap(match, team_id):
    """
    Heatmap of normalized edge weights between players.
    Edge weights are normalized across all matches, not
    just within a single match.
    """
    team_object = match.team_map.get(team_id)
    if team_object is None:
        raise("Team not in match")
    home_or_away = "home" if team_object == match.hometeam else "away"

    pass_map = onet.get_all_pass_destinations(match, team=home_or_away, exclude_subs=False, half=0)
    role_mappings, role_pass_map = onet.convert_pass_map_to_roles(team_object, pass_map)

    weighted_adjacency_matrix = np.array(onet.get_weighted_adjacency_matrix(
        sorted(list(set(role_mappings.values()))),
        role_pass_map
    ))

    # TODO: heatmap weights by role vs role
    fig, ax = plt.subplots()
    plt.imshow(
        weighted_adjacency_matrix,
        cmap='hot',
        interpolation='nearest',
        norm=mpl_colors.Normalize(vmin=0, vmax=30)
    )
    plt.show()


if __name__ == "__main__":
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

    all_copenhagen_match_ids = [984574, 984459]

    matches = {}

    for match_id in all_copenhagen_match_ids:
        fname = str(match_id)
        match_OPTA = opta.read_OPTA_f7(fpath, fname)
        match_OPTA = opta.read_OPTA_f24(fpath, fname, match_OPTA)
        matches[match_id] = match_OPTA

    for match_id in all_copenhagen_match_ids:
        plot_closeness_vs_betweenness(matches[match_id], copenhagen_team_id, match_id = match_id)
    for match_id in all_copenhagen_match_ids:
        adjacency_heatmap(matches[match_id], copenhagen_team_id)

    plot_cross_match_centrality(matches, copenhagen_team_id)
    plot_cross_match_centrality(matches, copenhagen_team_id, metric="betweenness")

