import OPTA_weighted_networks as onet

import csv
from itertools import combinations
import matplotlib.pyplot as plt
import networkx as nx

class Formation:
    def __init__(self, match_id, team_id, formation_id, opp_formation_1, opp_formation_2, player_locations=None, player_positions=None):
        """
        `player_locations` should be a dictionary of the (x,y) coordinates of each player indexed by player ID
        `player_positions` should be a list of player IDs in order of position as given in f24.xml
        """
        self.match_id = match_id
        self.team_id = team_id
        self.formation_id = formation_id
        self.opp_formation_1 = opp_formation_1
        self.opp_formation_2 = opp_formation_2
        self.player_locations = player_locations

        self.goalkeeper = None
        self.team_object = None

        csv_formations = {
            '1': [(-10,0), (-7,-7), (-7,7), (-5,-12), (-5,12), (0,-5), (0,5), (10,-10), (10,10), (15,0)],
            '2': [(-10,0), (-7,-7), (-7,7), (-5,-12), (-5,12), (0,0), (5,-7), (5,7), (15,-5), (15,5)],
            '3': [(-10,0), (-7,-7), (-7,7), (-5,-12), (-5,12), (0,-5), (0,5), (5,-7), (5,7), (7,0)],
            '4': [(-10,0), (-7,-7), (-7,7), (-5,-12), (-5,12), (0,-5), (0,5), (5,0), (10,-7), (10,7)],
            '5': [(-7,-6), (-7,6), (-5,-12), (-5,12), (0,-5), (0,5), (5,-10), (5,10), (10,-3), (10,3)],
            '6': [(-7,-6), (-7,6), (-5,-12), (-5,12), (-2,0), (0,-5), (0,5), (5,0), (10,-6), (10,6)],
            '7': [(-5,-7), (-5,0), (-5,7), (-2,-12), (-2,12), (0,-5), (0,5), (5,-7), (5,7), (7,0)],
            '8': [(-7,-5), (-7,5), (-5,-10), (-5,10), (-2,0), (2,0), (5,-3), (5,3), (7,-3), (7,3)],
            '9': [(-7,-5), (-7,5), (-5,-12), (-5,12), (-2,0), (2,-7), (2,7), (7,-10), (7,0), (7,10)],
            '10': [(-7,-6), (-7,6), (-5,-12), (-5,12), (-2,0), (2,-6), (2,6), (5,-12), (5,12), (7,0)],
            '11': [(-7,-5), (-7,5), (-5,-10), (-5,10), (0,0), (5,-12), (5,-6), (5,6), (5,12), (10,0)],
            '12': [(-7,-6), (-7,6), (-5,-12), (-5,12), (0,-6), (0,6), (5,-12), (5,12), (10,-5), (10,5)],
            '13': [(-7,0), (-5,-10), (-5,10), (-2,0), (2,-12), (2,0), (2,12), (5,-5), (5,0), (5,5)],
            '14': [(-7,0), (-5,-10), (-5,10), (0,-5), (0,5), (5,-12), (5,0), (5,12), (7,-6), (7,6)],
            '15': [(-7,0), (-5,-10), (-5,10), (0,-5), (0,5), (2,-12), (2,12), (5,-10), (5,0), (5,10)],
            '16': [(-7,0), (-5,-10), (-5,10), (0,0), (2,-12), (2,12), (5,-6), (5,6), (10,-5), (10,5)],
            '17': [(-5,-7), (-5,7), (0,-10), (0,-5), (0,5), (0,10), (5,-5), (5,5), (10,-5), (10,5)],
            '18': [(-5,-7), (-5,7), (-2,0), (0,-12), (0,-7), (0,7), (0,12), (5,-10), (5,0), (5,10)],
            '19': [(-5,-7), (-5,7), (-2,-12), (-2,12), (0,-5), (0,5), (5,-10), (5,10), (7,-2), (7,2)],
            '20': [(-5,-7), (-5,7), (-2,-10), (-2,10),(0,-5), (0,5), (5,-7), (5,7), (7,-5), (7,5)]
        }

        if self.player_locations is None:
            if player_positions is None:
                raise("Need either player positions or player locations")
            # TODO: assign player positions based on formation ID
            self.player_locations = {}
            formation_locations = csv_formations[self.formation_id]
            for i, p_id in enumerate(player_positions[1:]):
                self.player_locations[p_id] = (formation_locations[i][0] * 1.5, formation_locations[i][1] * 1.2)

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

    def add_substitute(self, original_player, substitute_player, replace=False):
        """
        Add the substitute to the formation graph, located near, but not replacing, the node of the
        original player
        """
        original_location = self.player_locations[original_player]
        if not replace:
            y = 45
            if original_location[0] < 0:
                y = -45
            self.player_locations[substitute_player] = (original_location[0], y)
        else:
            self.player_locations.pop(original_player)
            self.player_locations[substitute_player] = original_location

    def get_formation_graph(self, pass_map=None):
        G = nx.Graph()
        player_ids = self.player_locations.keys()

        edge_widths = None
        if pass_map is not None:
            for p_id, r_id in combinations(player_ids, 2):
                passes_out = pass_map.get(p_id)
                if passes_out is not None:
                    passes_out = passes_out.get(r_id)
                passes_out = passes_out["num_passes"] if passes_out is not None else 0

                passes_in = pass_map.get(r_id)
                if passes_in is not None:
                    passes_in = passes_in.get(p_id)
                passes_in = passes_in["num_passes"] if passes_in is not None else 0

                total_passes = passes_out + passes_in

                G.add_edge(p_id, r_id, weight=total_passes)

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


def copy_formation(formation):
    player_locations = {p_id: location for p_id, location in formation.player_locations.items()}

    new_formation = Formation(
        formation.match_id,
        formation.team_id,
        formation.formation_id,
        formation.opp_formation_1,
        formation.opp_formation_2,
        player_locations=player_locations
    )

    new_formation.team_object = formation.team_object
    new_formation.goalkeeper = formation.goalkeeper

    return new_formation


def read_formations_from_csv(csv_filename, team_id):
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

            formations.append(Formation(
                match_id,
                team_id,
                formation_id,
                opp_formation_1,
                opp_formation_2,
                player_locations=player_locations
            ))

    return formations
