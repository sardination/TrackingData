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

    def get_formation_graph(self, pass_map=None, transfer_map=None, show_triplets=None):
        """
        Create network graph based on pass map and formation information

        Kwargs:
            pass_map: dict of dicts with pass details
            transfer_map: dict to map player IDs to different node names (as given in pass_map)
            show_triplets: number of period (0, 1, 2) to show triplets for; None otherwise
        """

        G = nx.Graph()

        # default is to use player IDs, but transfer_map can indicate a change in labeling
        player_locations = self.player_locations
        if transfer_map is not None:
            player_locations = {}
            for player_id, new_key in transfer_map.items():
                if player_id not in self.player_locations.keys() or new_key in player_locations.keys():
                    continue
                player_locations[new_key] = self.player_locations[player_id]

        player_ids = player_locations.keys()

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

            edge_widths = {(u,v): G[u][v]['weight'] for u,v in G.edges()}
            # max_width = max(edge_widths)
            max_width = max(edge_widths.values())
            max_thickness = 3
            # edge_widths = [(w / max_width) * max_thickness for w in edge_widths]
            # normalize edge_widths the same way across networks
            static_largest_passes = 30
            # edge_widths = [(w / static_largest_passes) * max_thickness for w in edge_widths]
            edge_widths = {edge: (w / static_largest_passes) * max_thickness for edge, w in edge_widths.items()}

            nx.set_edge_attributes(
                G,
                edge_widths,
                'width'
            )
            edge_widths = [edge_widths[e] for e in G.edges()]# need to pass list into draw function

        for p_id in player_ids:
            G.add_node(p_id)

        # reflect clustering coefficient in node size
        clustering_coeffs = onet.get_clustering_coefficients(pass_map.keys(), pass_map, weighted=True)
        max_clustering_coeff = max(clustering_coeffs.values()) ** 3 # ^ 3 to exaggerate effect
        max_node_size = 1200
        # node_sizes = [(clustering_coeffs[n] ** 3 / max_clustering_coeff) * max_node_size if clustering_coeffs.get(n) is not None else 0
        #     for n in G.nodes()]
        # normalize node size the same way across networks
        static_largest_coefficient = 5 ** 3
        node_sizes = {n: (clustering_coeffs[n] ** 3 / static_largest_coefficient) * max_node_size if clustering_coeffs.get(n) is not None else 0
            for n in G.nodes()}
        # TODO: accommodate this for subs

        nx.set_node_attributes(
            G,
            player_locations,
            'pos'
        )
        nx.set_node_attributes(
            G,
            node_sizes,
            'size'
        )
        node_sizes = [node_sizes[n] for n in G.nodes()] # need to pass list into draw function

        nx.draw_networkx_nodes(
            G,
            player_locations,
            node_size=node_sizes,
            node_color='blue'
        )
        nx.draw_networkx_labels(
            G,
            player_locations,
            {p_id: p_id for p_id in player_ids},
            font_size=12,
            font_family='sans-serif',
            font_color='red'
        )

        edge_colors = {e : "black" for e in G.edges()}
        if show_triplets is not None:
            triplet_list = onet.find_player_triplets_by_team(self.team_object, half=show_triplets)
            # top n triplets
            n = 5
            use_triplets = triplet_list[-5:]
            # get color from green to yellow
            green = "00ff00"
            yellow = "001100"
            for i, t_info in enumerate(use_triplets):
                triplet, num_passes = t_info

                if transfer_map is not None:
                    new_triplet = []
                    for p in triplet:
                        new_triplet.append(transfer_map[p])
                    triplet = new_triplet

                highlight_color = onet.get_color_by_gradient(
                    float(n - i) / n,
                    low_color = green,
                    high_color = yellow
                )

                for i, p in enumerate(triplet):
                    p2_i = i + 1
                    if i == len(triplet) - 1:
                        p2_i = 0
                    pair = (triplet[i], triplet[p2_i])
                    rev_pair = (triplet[p2_i], triplet[i])

                    print(pair)

                    if pair in G.edges():
                        edge_colors[pair] = highlight_color
                    if rev_pair in G.edges():
                        edge_colors[rev_pair] = highlight_color

                print()

            nx.set_edge_attributes(
                G,
                edge_colors,
                'edge_color'
            )

        if pass_map is not None:
            nx.draw_networkx_edges(
                G,
                player_locations,
                width=edge_widths,
                edge_color=[edge_colors[e] for e in G.edges()]
            )

        plt.axis('off')
        plt.show()
        return G


    def get_formation_graph_by_role(self, pass_map, show_triplets=None):
        """
        Display formation by role rather than player ID. Combine substitutes with
        their target players into one role node.
        """

        role_mappings, role_pass_map = onet.convert_pass_map_to_roles(self.team_object, pass_map)

        return self.get_formation_graph(
            pass_map=role_pass_map,
            transfer_map=role_mappings,
            show_triplets=show_triplets
        )


    def get_formation_difference_graph(self, this_pass_map, other_formation, other_pass_map):
        """
        Creates a difference graph between this formation and `other_formation`.
        This really only makes sense for role graphs, as players change from match
        to match.

        If this formation has a thicker edge than `other_formation`, the difference
        edge will be green, and red if otherwise. The thickness will represent the
        size of the difference.

        Likewise, if this formation has a larger node than `other_formation`, the difference
        node will be green, and red if otherwise. The size will represent the size of the
        difference.

        TODO: does direction of passes matter?
        """

        this_formation_graph = self.get_formation_graph_by_role(this_pass_map)
        other_formation_graph = other_formation.get_formation_graph_by_role(other_pass_map)

        difference_graph = nx.Graph()

        this_nodes = set(this_formation_graph.nodes())
        other_nodes = set(other_formation_graph.nodes())

        this_node_sizes = nx.get_node_attributes(this_formation_graph, 'size')
        other_node_sizes = nx.get_node_attributes(other_formation_graph, 'size')

        this_node_locations = nx.get_node_attributes(this_formation_graph, 'pos')
        other_node_locations = nx.get_node_attributes(other_formation_graph, 'pos')

        # gets node difference colors and sizes
        node_sizes = {}
        node_locations = {}
        for node in this_nodes.difference(other_nodes):
            difference_graph.add_node(node)
            node_sizes[node] = this_node_sizes[node]
            node_locations[node] = this_node_locations[node]

        for node in other_nodes.difference(this_nodes):
            difference_graph.add_node(node)
            node_sizes[node] = -other_node_sizes[node]
            node_locations[node] = other_node_locations[node]

        for node in this_nodes.intersection(other_nodes):
            difference_graph.add_node(node)
            node_sizes[node] = this_node_sizes[node] - other_node_sizes[node]
            node_locations[node] = this_node_locations[node]

        node_colors = {node: 'red' if size < 0 else 'green' for node, size in node_sizes.items()}
        node_sizes = {node: abs(size) for node, size in node_sizes.items()}

        # get edge difference colors and sizes
        edge_widths = {source: {dest: 0 for dest in difference_graph.nodes()} for source in difference_graph.nodes()}
        edge_colors = {source: {dest: None for dest in difference_graph.nodes()} for source in difference_graph.nodes()}

        for source in difference_graph.nodes():
            for dest in difference_graph.nodes():
                this_width = 0
                other_width = 0
                if (source, dest) in this_formation_graph.edges():
                    this_width = this_formation_graph[source][dest]['width']
                if (source, dest) in other_formation_graph.edges():
                    other_width = other_formation_graph[source][dest]['width']
                diff_width = this_width - other_width
                edge_widths[source][dest] = abs(diff_width)
                edge_colors[source][dest] = 'red' if diff_width < 0 else 'green'

                difference_graph.add_edge(source, dest, weight=abs(diff_width))

        nx.draw_networkx_nodes(
            difference_graph,
            node_locations,
            node_size=[node_sizes[node] for node in difference_graph.nodes()],
            node_color=[node_colors[node] for node in difference_graph.nodes()]
        )
        nx.draw_networkx_labels(
            difference_graph,
            node_locations,
            {node:node for node in difference_graph.nodes()},
            font_size=12,
            font_family='sans-serif',
            font_color='black'
        )

        nx.draw_networkx_edges(
            difference_graph,
            node_locations,
            width=[edge_widths[u][v] for u,v in difference_graph.edges()],
            edge_color=[edge_colors[u][v] for u,v in difference_graph.edges()]
        )

        plt.axis('off')
        plt.show()
        return difference_graph


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
