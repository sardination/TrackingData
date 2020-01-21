import formations
import OPTA as opta
import OPTA_weighted_networks as onet

import networkx as nx

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


copenhagen_formations = formations.read_formations_from_csv('../copenhagen_formations.csv')

all_copenhagen_match_ids = [984567]

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

    # for period in [0,1,2]:
    for period in [1]:
        pass_map = onet.get_all_pass_destinations(match_OPTA, team=home_or_away, exclude_subs=False, half=period)
        # TODO: ^^ fix connectedness by using substitutes for the appropriate players within the formation
        # graph = formation.get_formation_graph(pass_map=pass_map, directed=True)

        graph = nx.Graph()
        mapped_players = pass_map.keys()
        new_ids = {}
        reverse_key = {}
        for new_id, p_id in enumerate(mapped_players):
            new_ids[p_id] = [new_id, 100 + new_id]
            reverse_key[new_id] = p_id
            reverse_key[100 + new_id] = p_id
            graph.add_node(new_id) # new_id is outgoing, 100 + new_id is incoming
            graph.add_node(100 + new_id)

        for p_id in mapped_players:
            for r_id in mapped_players:
                pass_info = pass_map[p_id][r_id]

                sender = new_ids[p_id][0]
                receiver = new_ids[r_id][1]
                weight = pass_info["num_passes"]
                if weight > 0:
                    # print("{} --{}--> {}".format(sender, weight, receiver))
                    graph.add_edge(sender, receiver, weight=weight**3)  # TODO: adjust weight to work in relation

        # CENTRALITY MEASUREMENTS
        edge_betweenness = nx.edge_current_flow_betweenness_centrality(graph, weight='weight')
        betweenness = nx.current_flow_betweenness_centrality(graph, weight='weight')
        centrality = nx.current_flow_closeness_centrality(graph, weight='weight')
        # TODO: ^^ check whether weight is distance or connection strength
        # TODO: transfer the idea of centrality and betweenness to a directed graph
        #   => what is the equivalent undirected graph format for a directed graph?
        #   => perhaps create an "incoming" and "outgoing" node for each single node and connect those edges

        # print(graph.edges())

        print("EDGE BETWEENNESS")
        for key, value in sorted(edge_betweenness.items(), key=lambda t:-t[1]):
            # print("{}: {}".format(key, value))
            sender = reverse_key.get(min(key))
            receiver = reverse_key.get(max(key))
            print("{} -- {} --> {}: {}".format(sender, pass_map[sender][receiver]['num_passes'], receiver, value))

        print()
        print("BETWEENNESS")
        for key, value in sorted(betweenness.items(), key=lambda t:-t[1]):
            # print("{}: {}".format(key, value))
            player = reverse_key.get(key)
            print("{}: {}".format(player, value))

        print()
        print("CENTRALITY")
        for key, value in sorted(centrality.items(), key=lambda t:-t[1]):
            # print("{}: {}".format(key, value))
            player = reverse_key.get(key)
            print("{}: {}".format(player, value))

        # print("EDGE BETWEENNESS: {}".format(edge_betweenness))
        # print("BETWEENNESS: {}".format(betweenness))
        # print("CENTRALITY: {}".format(centrality))
        print()
        print()

        formation.get_formation_graph(pass_map)

