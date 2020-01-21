import OPTA_weighted_networks as onet

import csv
import matplotlib.pyplot as plt
import networkx as nx

class Formation:
    def __init__(self, match_id, formation_id, opp_formation_1, opp_formation_2, player_locations):
        self.match_id = match_id
        self.formation_id = formation_id
        self.opp_formation_1 = opp_formation_1
        self.opp_formation_2 = opp_formation_2
        self.player_locations = player_locations
        self.goalkeeper = None

        self.team_object = None

    def add_team_object(self, team_object):
        self.team_object = team_object

    def add_goalkeeper(self, goalkeeper_id=None):
        if goalkeeper_id is None:
            if self.team_object is None:
                raise("Need either goalkeeper id or team object")
            else:
                for p_id, p_obj in self.team_object.player_map.items():
                    if p_obj.position == "Goalkeeper":
                        self.goalkeeper = p_id
                        self.player_locations[p_id] = (-45, 0)
        else:
            self.goalkeeper = goalkeeper_id
            self.player_locations[goalkeeper_id] = (-45, 0)

    def add_substitute(self, original_player, substitute_player):
        """
        Add the substitute to the formation graph, located near, but not replacing, the node of the
        original player
        """
        original_location = self.player_locations[original_player]
        y = 45
        if original_location[0] < 0:
            y = -45
        self.player_locations[substitute_player] = (original_location[0], y)

    def get_formation_graph(self, pass_map=None):
        G = nx.Graph()
        player_ids = self.player_locations.keys()

        edge_widths = None
        if pass_map is not None:
            for p_id in player_ids:
                passes_out = pass_map.get(p_id)
                if passes_out is None:
                    continue
                for r_id in player_ids:
                    pass_info = passes_out.get(r_id)
                    if pass_info is None:
                        continue
                    G.add_edge(p_id, r_id, weight=pass_info["num_passes"])

            edge_widths = [G[u][v]['weight'] for u,v in G.edges()]
            max_width = max(edge_widths)
            max_thickness = 3
            edge_widths = [(w / max_width) * max_thickness for w in edge_widths]

        for p_id in player_ids:
            G.add_node(p_id)

        # reflect clustering coefficient in node size
        clustering_coeffs = onet.get_clustering_coefficients(pass_map.keys(), pass_map, weighted=True)
        max_clustering_coeff = max(clustering_coeffs.values()) ** 3 # ^ 3 to exaggerate effect
        max_node_size = 1200
        node_sizes = [(clustering_coeffs[n] ** 3 / max_clustering_coeff) * max_node_size if clustering_coeffs.get(n) is not None else 0
            for n in G.nodes()]
        # TODO: accommodate this for subs

        nx.draw_networkx_nodes(
            G,
            self.player_locations,
            node_size=node_sizes,
            node_color='blue'
        )
        nx.draw_networkx_labels(
            G,
            self.player_locations,
            {p_id: p_id for p_id in player_ids},
            font_size=12,
            font_family='sans-serif',
            font_color='red'
        )
        if pass_map is not None:
            nx.draw_networkx_edges(G, self.player_locations, width=edge_widths)

        plt.axis('off')
        plt.show()
        return G


def read_formations_from_csv(csv_filename):
    """
    Read CSV file with formation information and return list of Formation objects

    Args:
        csv_filename (string): path to formation CSV file
    """

    formations = []

    with open(csv_filename, 'r') as csvfile:
        csvreader = csv.reader(csvfile)
        headers = next(csvreader)

        for row in csvreader:
            match_id = int(row[0])
            formation_id = row[1]
            opp_formation_1 = row[2]
            opp_formation_2 = row[3]
            player_locations = {}
            for i in range(4, len(row), 3):
                p_id = int(row[i])
                # flip representation to have attacking direction right-ward (goalie on left side)
                x = -float(row[i + 1])
                y = -float(row[i + 2])
                player_locations[p_id] = (x, y)

            formations.append(Formation(match_id, formation_id, opp_formation_1, opp_formation_2, player_locations))

    return formations