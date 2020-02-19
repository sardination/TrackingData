import centrality
import OPTA as opta
import OPTA_weighted_networks as onet

import matplotlib.pyplot as plt


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


        fig,ax = plt.subplots()
        ax.set_xlabel("closeness")
        ax.set_ylabel("betweenness")
        ax.set_title("Match {} Team {}".format(match_id, team_id))

        ax.scatter(x, y)
        for i, p_id in enumerate(players):
            ax.annotate(p_id, (x[i], y[i]))

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

    for match_id in all_copenhagen_match_ids:
        fname = str(match_id)
        match_OPTA = opta.read_OPTA_f7(fpath, fname)
        match_OPTA = opta.read_OPTA_f24(fpath, fname, match_OPTA)

        plot_closeness_vs_betweenness(match_OPTA, copenhagen_team_id, match_id = match_id)


