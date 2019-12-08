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

        nx.draw_networkx_nodes(G, self.player_locations, node_size=700)
        nx.draw_networkx_labels(
            G,
            self.player_locations,
            {p_id: p_id for p_id in player_ids},
            font_size=12,
            font_family='sans-serif',
            font_color='cyan'
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
            match_id = row[0]
            formation_id = row[1]
            opp_formation_1 = row[2]
            opp_formation_2 = row[3]
            player_locations = {}
            for i in range(4, len(row), 3):
                p_id = int(row[i])
                x = float(row[i + 1])
                y = float(row[i + 2])
                player_locations[p_id] = (x, y)

            formations.append(Formation(match_id, formation_id, opp_formation_1, opp_formation_2, player_locations))

    return formations