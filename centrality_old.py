        # TODO: transfer the idea of centrality and betweenness to a directed graph
        #   => what is the equivalent undirected graph format for a directed graph?
        #   => perhaps create an "incoming" and "outgoing" node for each single node and connect those edges
        # THE BELOW IMPLEMENTATION IS NOT EQUIVALENT
        # graph = nx.Graph()
        # mapped_players = pass_map.keys()
        # new_ids = {}
        # reverse_key = {}
        # for new_id, p_id in enumerate(mapped_players):
        #     new_ids[p_id] = [new_id, 100 + new_id]
        #     reverse_key[new_id] = p_id
        #     reverse_key[100 + new_id] = p_id
        #     graph.add_node(new_id) # new_id is outgoing, 100 + new_id is incoming
        #     graph.add_node(100 + new_id)

        # for p_id in mapped_players:
        #     for r_id in mapped_players:
        #         pass_info = pass_map[p_id][r_id]

        #         sender = new_ids[p_id][0]
        #         receiver = new_ids[r_id][1]
        #         weight = pass_info["num_passes"]
        #         if weight > 0:
        #             # print("{} --{}--> {}".format(sender, weight, receiver))
        #             # graph.add_edge(sender, receiver, weight=weight**2)  # TODO: adjust weight to work in relation
        #             graph.add_edge(sender, receiver, weight=weight)

        # CENTRALITY MEASUREMENTS
        # edge_betweenness = nx.edge_current_flow_betweenness_centrality(graph, weight='weight')
        # betweenness = nx.current_flow_betweenness_centrality(graph, weight='weight')
        # closeness = nx.current_flow_closeness_centrality(graph, weight='weight')
        # DONE: ^^ check whether weight is distance or connection strength
        #       -> connection strength (inversing yields completely incorrect results)

        # print(graph.edges())

        ### THE FOLLOWING MEASURES ONLY WORK FOR UNDIRECTED NETWORKS

        # print("EDGE BETWEENNESS")
        # for key, value in sorted(edge_betweenness.items(), key=lambda t:-t[1]):
        #     # print("{}: {}".format(key, value))
        #     sender = reverse_key.get(min(key))
        #     receiver = reverse_key.get(max(key))
        #     print("{} -- {} --> {}: {}".format(sender, pass_map[sender][receiver]['num_passes'], receiver, value))

        # print()
        # print("BETWEENNESS")
        # for key, value in sorted(betweenness.items(), key=lambda t:-t[1]):
        #     # print("{}: {}".format(key, value))
        #     player = reverse_key.get(key)
        #     print("{}: {}".format(player, value))

        # print()
        # print("CLOSENESS")
        # for key, value in sorted(closeness.items(), key=lambda t:-t[1]):
        #     # print("{}: {}".format(key, value))
        #     player = reverse_key.get(key)
        #     print("{}: {}".format(player, value))

        # print("EDGE BETWEENNESS: {}".format(edge_betweenness))
        # print("BETWEENNESS: {}".format(betweenness))
        # print("CLOSENESS: {}".format(closeness))
        # print()
        # print()