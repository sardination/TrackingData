import centrality
import OPTA as opta
import OPTA_weighted_networks as onet

import matplotlib.colors as mpl_colors
import matplotlib.pyplot as plt
import numpy as np

offense = [9, 10]
midfield = [4, 7, 8, 11]
defense = [2, 3, 5, 6]

def plot_match_to_average_pagerank(average_pageranks, match, team="home", match_id=None):
    match_pageranks = onet.get_pagerank(
        match,
        team=team,
        role_grouped=True
    )

    players = average_pageranks.keys()
    x = [average_pageranks[p] for p in players]
    y = [match_pageranks[p] for p in players]


    fig, ax = plt.subplots()
    ax.set_xlabel("Average Match PageRank")
    ax.set_ylabel("Match {} PageRank".format(match_id))
    ax.set_title("Match {} vs Average PageRank".format(match_id))
    ax.set_xlim([0.085, 0.098])
    ax.set_ylim([0.085, 0.098])

    # draw center line
    line_x_vals = [
        min(set(x).union(set(y))),
        max(set(x).union(set(y)))
    ]
    line_y_vals = line_x_vals
    plt.plot(line_x_vals, line_y_vals, '--', color='r')

    colors = []
    for i, p_id in enumerate(players):
        if p_id in offense:
            colors.append('#28b463')
        elif p_id in midfield:
            colors.append('#f4d03f')
        elif p_id in defense:
            colors.append('#ec7063')
        else:
            colors.append('#85c1e9')

    ax.scatter(x, y, c=colors)
    for i, p_id in enumerate(players):
        ax.annotate(p_id, (x[i], y[i]))

    plt.show()

def plot_closeness_vs_betweenness_from_pass_map(pass_map, title="Average Match"):
    # graphs = centrality.get_directed_graphs(
    #     pass_map,
    #     player_times,
    #     team_object,
    #     role_grouped=True,
    #     period=half
    # )

    graph = centrality.get_directed_graph_without_times(pass_map)

    betweenness = centrality.current_flow_betweenness_directed(
        graph,
        start_node=1
    )

    closeness = centrality.current_flow_closeness_directed(
        graph,
        start_node=1
    )

    players = graph.nodes()
    x = [closeness[p] for p in players]
    y = [betweenness[p] for p in players]


    fig, ax = plt.subplots()
    ax.set_xlabel("closeness")
    ax.set_ylabel("betweenness")
    ax.set_title(title)
    ax.set_xlim([0, 3])
    ax.set_ylim([0, 0.8])

    colors = []
    for i, p_id in enumerate(players):
        if p_id in offense:
            colors.append('#28b463')
        elif p_id in midfield:
            colors.append('#f4d03f')
        elif p_id in defense:
            colors.append('#ec7063')
        else:
            colors.append('#85c1e9')

    ax.scatter(x, y, c=colors)
    for i, p_id in enumerate(players):
        ax.annotate(p_id, (x[i], y[i]))

    plt.show()


def plot_closeness_vs_betweenness(match_OPTA, team_id, match_id=None, half=0):
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
    pass_map = onet.get_all_pass_destinations(match_OPTA, team=home_or_away, exclude_subs=False, half=half)

    graphs = centrality.get_directed_graphs(
        pass_map,
        player_times,
        team_object,
        role_grouped=True,
        period=half
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
    title = "Match {} Team {}".format(match_id, team_id)
    if half != 0:
        title = "{} - Half {}".format(title, half)
    ax.set_title(title)
    ax.set_xlim([0, 3])
    ax.set_ylim([0, 0.8])

    colors = []
    for i, p_id in enumerate(players):
        if p_id in offense:
            colors.append('#28b463')
        elif p_id in midfield:
            colors.append('#f4d03f')
        elif p_id in defense:
            colors.append('#ec7063')
        else:
            colors.append('#85c1e9')

    ax.scatter(x, y, c=colors)
    for i, p_id in enumerate(players):
        ax.annotate(p_id, (x[i], y[i]))

    plt.show()


def plot_cross_match_centrality_by_pass_maps(pass_maps, metric="closeness"):
    allowed_metrics = {
        "closeness": centrality.current_flow_closeness_directed,
        "betweenness": centrality.current_flow_betweenness_directed
    }
    metric_function = allowed_metrics.get(metric)
    if metric_function is None:
        raise("Unallowed metric")

    map_ids = list(pass_maps.keys())[:2]
    if len(map_ids) != 2:
        raise("Fewer than two matches passed in")

    metric_results = {}

    players = set()
    for map_id in map_ids:
        graph = centrality.get_directed_graph_without_times(pass_maps[map_id])
        players = players.union(set(graph.nodes()))

        metric_results[map_id] = metric_function(
            graph,
            start_node=1
        )

    players = list(players)

    x = [metric_results[map_ids[0]].get(p) if p in metric_results[map_ids[0]].keys() else 0 for p in players]
    y = [metric_results[map_ids[1]].get(p) if p in metric_results[map_ids[1]].keys() else 0 for p in players]

    fig, ax = plt.subplots()
    ax.set_xlabel("Match {} {}".format(
        map_ids[0],
        metric
    ))
    ax.set_ylabel("Match {} {}".format(
        map_ids[1],
        metric
    ))
    ax.set_title("{} vs {} {}".format(map_ids[0], map_ids[1], metric))

    if metric == "closeness":
        ax.set_xlim([0, 3])
        ax.set_ylim([0, 3])
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

    colors = []
    for i, p_id in enumerate(players):
        if p_id in offense:
            colors.append('#28b463')
        elif p_id in midfield:
            colors.append('#f4d03f')
        elif p_id in defense:
            colors.append('#ec7063')
        else:
            colors.append('#85c1e9')

    ax.scatter(x, y, c=colors)
    for i, p_id in enumerate(players):
        ax.annotate(p_id, (x[i], y[i]))

    plt.show()


def plot_cross_match_centrality(matches, team_id, metric="closeness"):
    """
    Plot one centrality measure of two matches against each other on
    opposing axes.

    Args:
        matches (dict): keyed by match_id, values are matchOPTA objects
        team_id (int): ID for the team in question
    Kwargs:
        metric (string): the metric used for the match-to-match comparison
    """

    allowed_metrics = {
        "closeness": centrality.current_flow_closeness_directed,
        "betweenness": centrality.current_flow_betweenness_directed,
        "pagerank": onet.get_pagerank
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

        if metric != "pagerank":
            metric_results[match_id] = metric_function(
                graphs['scaled_graph'],
                start_node=1
            )
        else:
            metric_results[match_id] = metric_function(
                match_OPTA,
                team=home_or_away,
                role_grouped=True
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
        ax.set_xlim([0, 3])
        ax.set_ylim([0, 3])
    elif metric == "betweenness":
        ax.set_xlim([0, 0.8])
        ax.set_ylim([0, 0.8])
    elif metric == "pagerank":
        ax.set_xlim([0.085, 0.098])
        ax.set_ylim([0.085, 0.098])

    # draw center line
    line_x_vals = [
        min(set(x).union(set(y))),
        max(set(x).union(set(y)))
    ]
    line_y_vals = line_x_vals
    plt.plot(line_x_vals, line_y_vals, '--', color='r')

    colors = []
    for i, p_id in enumerate(players):
        if p_id in offense:
            colors.append('#28b463')
        elif p_id in midfield:
            colors.append('#f4d03f')
        elif p_id in defense:
            colors.append('#ec7063')
        else:
            colors.append('#85c1e9')

    ax.scatter(x, y, c=colors)
    for i, p_id in enumerate(players):
        ax.annotate(p_id, (x[i], y[i]))

    plt.show()


def plot_cross_half_centrality(match, team_id, metric="closeness"):
    """
    Plot one centrality measure of two matches against each other on
    opposing axes.

    Args:
        matches (matchOPTA): match to evaluate centrality measures
        team_id (int): ID for the team in question
    Kwargs:
        metric (string): the metric used for the match-to-match comparison
    """

    allowed_metrics = {
        "closeness": centrality.current_flow_closeness_directed,
        "betweenness": centrality.current_flow_betweenness_directed,
        "pagerank": onet.get_pagerank
    }
    metric_function = allowed_metrics.get(metric)
    if metric_function is None:
        raise("Unallowed metric")

    metric_results = {}

    players = set()
    for half in [0,1]:
        team_object = match.team_map.get(team_id)
        if team_object is None:
            raise("Team not in match")

        home_or_away = "home" if team_object == match.hometeam else "away"

        player_times = team_object.get_on_pitch_periods()

        pass_map = onet.get_all_pass_destinations(match, team=home_or_away, exclude_subs=False, half=half)

        graphs = centrality.get_directed_graphs(
            pass_map,
            player_times,
            team_object,
            role_grouped=True,
            period=half
        )
        players = players.union(set(graphs['scaled_graph'].nodes()))

        if metric != "pagerank":
            metric_results[half] = metric_function(
                graphs['scaled_graph'],
                start_node=1
            )
        else:
            metric_results[half] = metric_function(
                match_OPTA,
                team=home_or_away,
                half=half,
                role_grouped=True
            )
            print(metric_results[half])

    players = list(players)

    x = [metric_results[0].get(p) if p in metric_results[0].keys() else 0 for p in players]
    y = [metric_results[1].get(p) if p in metric_results[1].keys() else 0 for p in players]

    fig, ax = plt.subplots()
    ax.set_xlabel("First Half {}".format(metric))
    ax.set_ylabel("Second Half {}".format(metric))
    ax.set_title("Team {}".format(team_id))

    if metric == "closeness":
        ax.set_xlim([0, 3])
        ax.set_ylim([0, 3])
    elif metric == "betweenness":
        ax.set_xlim([0, 0.8])
        ax.set_ylim([0, 0.8])
    elif metric == "pagerank":
        ax.set_xlim([0.085, 0.098])
        ax.set_ylim([0.085, 0.098])

    # draw center line
    line_x_vals = [
        min(set(x).union(set(y))),
        max(set(x).union(set(y)))
    ]
    line_y_vals = line_x_vals
    plt.plot(line_x_vals, line_y_vals, '--', color='r')

    colors = []
    for i, p_id in enumerate(players):
        if p_id in offense:
            colors.append('#28b463')
        elif p_id in midfield:
            colors.append('#f4d03f')
        elif p_id in defense:
            colors.append('#ec7063')
        else:
            colors.append('#85c1e9')

    ax.scatter(x, y, c=colors)
    for i, p_id in enumerate(players):
        ax.annotate(p_id, (x[i], y[i]))

    plt.show()


def adjacency_heatmap(match, team_id, half=0):
    """
    Heatmap of normalized edge weights between players.
    Edge weights are normalized across all matches, not
    just within a single match.
    """
    team_object = match.team_map.get(team_id)
    if team_object is None:
        raise("Team not in match")
    home_or_away = "home" if team_object == match.hometeam else "away"

    pass_map = onet.get_all_pass_destinations(match, team=home_or_away, exclude_subs=False, half=half)
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
    # all_copenhagen_match_ids = [984528]

    matches = {}

    for match_id in all_copenhagen_match_ids:
        fname = str(match_id)
        match_OPTA = opta.read_OPTA_f7(fpath, fname)
        match_OPTA = opta.read_OPTA_f24(fpath, fname, match_OPTA)
        matches[match_id] = match_OPTA

    # for match_id in all_copenhagen_match_ids:
    #     for half in [0,1,2]:
    #         adjacency_heatmap(matches[match_id], copenhagen_team_id, half=half)
    # for match_id in all_copenhagen_match_ids:
    #     for half in [0,1,2]:
    #         plot_closeness_vs_betweenness(matches[match_id], copenhagen_team_id, match_id=match_id, half=half)
    # plot_cross_half_centrality(list(matches.values())[0], copenhagen_team_id)
    # plot_cross_half_centrality(list(matches.values())[0], copenhagen_team_id, metric="betweenness")
    # plot_cross_half_centrality(list(matches.values())[0], copenhagen_team_id, metric="pagerank")

    for match_id in all_copenhagen_match_ids:
        plot_closeness_vs_betweenness(matches[match_id], copenhagen_team_id, match_id = match_id)
    for match_id in all_copenhagen_match_ids:
        adjacency_heatmap(matches[match_id], copenhagen_team_id)

    plot_cross_match_centrality(matches, copenhagen_team_id)
    plot_cross_match_centrality(matches, copenhagen_team_id, metric="betweenness")
    plot_cross_match_centrality(matches, copenhagen_team_id, metric="pagerank")
