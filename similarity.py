import centrality
import formations
import OPTA as opta
import OPTA_weighted_networks as onet

import numpy as np
import random


def get_bitstrings(match, team_id, bit_ordering=None):
    """
    Return bitstrings for nodes and edges based on XML-designated formation positions (13 bits)
    If last bit is 1, then node. If last bit is 0, then edge.
    """

    home_or_away = "home"
    home_team = onet.get_team(match, team="home")
    away_team = onet.get_team(match, team="away")
    if home_team.team_id != team_id:
        home_or_away = "away"
    team_object = onet.get_team(match, team=home_or_away)

    involved_players = []
    positions = []
    player_positions = {}
    on_pitch_players = []

    on_player = None
    off_player = None
    for e in team_object.events:
        if e.type_id == 34:
            for qual in e.qualifiers:
                if qual.qual_id == 30: # involved players
                    involved_players = [int(p_id) for p_id in qual.value.split(", ")]
                elif qual.qual_id == 131: # formation of players (0 if not involved)
                    positions = [int(pos) for pos in qual.value.split(", ")]

                if involved_players != [] and positions != []:
                    player_positions = {pos: p_id for p_id, pos in zip(involved_players, positions) if pos != 0}
                    on_pitch_players = [p_id for pos, p_id in sorted(player_positions.items(), key=lambda t:t[0]) if pos != 0]
                    break

        elif e.is_substitution:
            if e.sub_direction == "on":
                on_player = e.player_id
            elif e.sub_direction == "off":
                off_player = e.player_id

            if on_player is not None and off_player is not None:
                position = on_pitch_players.index(off_player)
                on_pitch_players[position] = on_player
                pos_key = position
                while player_positions.get(pos_key) is not None:
                    pos_key += 11
                player_positions[pos_key] = on_player

                on_player = None
                off_player = None

    node_bits = 6
    player_bits = {}
    for pos, p_id in player_positions.items():
        player_bits[p_id] = "{0:b}".format(pos)
        player_bits[p_id] = "0" * (node_bits - len(player_bits[p_id])) + player_bits[p_id]

    edge_bits = {}
    for p_pos, p_id in player_positions.items():
        outgoing_edge_numbers = {}
        for r_pos, r_id in player_positions.items():
            outgoing_edge_numbers[r_id] = player_bits[p_id] + player_bits[r_id] + "0"
        edge_bits[p_id] = outgoing_edge_numbers

    for p_id in player_bits.keys():
        player_bits[p_id] = player_bits[p_id] + ("0" * node_bits) + "1"

    if bit_ordering is not None:
        player_bits = {p_id: ''.join([list(b)[ind] for ind in bit_ordering]) for p_id, b in player_bits.items()}
        edge_bits = {p_id:
            {r_id:
                ''.join([list(b)[ind] for ind in bit_ordering])
                for r_id, b in p_dict.items()
            }
            for p_id, p_dict in edge_bits.items()
        }

    return player_bits, edge_bits


def get_graph_fingerprint(match, team_id, bit_ordering=None):
    """
    Get PageRank of each node and use edge weights to sum and determine graph fingerprint
    """
    total_bits = 13

    home_or_away = "home"
    home_team = onet.get_team(match, team="home")
    away_team = onet.get_team(match, team="away")
    if home_team.team_id != team_id:
        home_or_away = "away"
    team_object = onet.get_team(match, team=home_or_away)

    node_bitstrings, edge_bitstrings = get_bitstrings(match, team_id, bit_ordering=bit_ordering)
    node_bitstrings = {p_id: np.array([-1 if c == "0" else 1 for c in list(b)]) for p_id, b in node_bitstrings.items()}
    edge_bitstrings = {p_id:
        {r_id:
            np.array([-1 if c == "0" else 1 for c in list(b)])
            for r_id, b in b_dict.items()
        }
        for p_id, b_dict in edge_bitstrings.items()
    }

    node_weights = onet.get_pagerank(match_OPTA, team=home_or_away)
    node_weights = {n_id: node_weights[n_id] if n_id in node_weights.keys() else 0 for n_id in node_bitstrings.keys()}
    pass_map = onet.get_all_pass_destinations(match_OPTA, team=home_or_away, exclude_subs=False)
    edge_weights = {p_id: {r_id: 0 for r_id in node_bitstrings.keys()} for p_id in node_bitstrings.keys()}

    for p_id in node_bitstrings.keys():
        p_outgoing_passes = pass_map.get(p_id)
        if p_outgoing_passes is None:
            continue

        total_outdegree = sum([d['num_passes'] for d in p_outgoing_passes.values()])
        if total_outdegree == 0:
            continue

        for r_id in node_bitstrings.keys():
            p_r_passes = p_outgoing_passes.get(r_id)
            if p_r_passes is None:
                continue
            edge_weights[p_id][r_id] = node_weights[p_id] * float(p_r_passes['num_passes']) / total_outdegree

    fingerprint_summation = np.array([0.0] * total_bits)
    for n, b in node_bitstrings.items():
        fingerprint_summation += b * node_weights[n]

    for p_id, b_dict in edge_bitstrings.items():
        for r_id, b in b_dict.items():
            fingerprint_summation += b * edge_weights[p_id][r_id]

    fingerprint = fingerprint_summation > 0

    return fingerprint.astype(int)


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

matches = {}
home_or_away = {}
team_objects = {}
for match_id in all_copenhagen_match_ids:
    fname = str(match_id)
    match_OPTA = opta.read_OPTA_f7(fpath, fname)
    match_OPTA = opta.read_OPTA_f24(fpath, fname, match_OPTA)

    matches[match_id] = match_OPTA

    home_team = onet.get_team(match_OPTA, team="home")
    away_team = onet.get_team(match_OPTA, team="away")
    home_or_away[match_id] = "home"
    team_objects[match_id] = home_team
    if home_team.team_id != copenhagen_team_id:
        home_or_away[match_id] = "away"
        team_objects[match_id] = away_team

copenhagen_formations = formations.read_formations_from_csv('../copenhagen_formations.csv', copenhagen_team_id)
formations = {formation.match_id: formation for formation in copenhagen_formations}

num_bits = 13
bit_ordering = list(range(num_bits))
random.shuffle(bit_ordering)

if False:
    print("------ FINGERPRINTS ------")
    fingerprints = {}
    for match_id in all_copenhagen_match_ids:
        match_OPTA = matches[match_id]
        fingerprints[match_id] = get_graph_fingerprint(match_OPTA, copenhagen_team_id, bit_ordering=bit_ordering)
        print("Match {}: {}".format(match_id, fingerprints[match_id]))

print()

if True:
    print("------ CENTRALITY (BETWEENNESS) ORDERING ------")
    for match_id in all_copenhagen_match_ids:
        match_OPTA = matches[match_id]
        team_object = team_objects[match_id]
        formation = formations[match_id]

        pass_map = onet.get_all_pass_destinations(
            match_OPTA,
            team=home_or_away[match_id],
            exclude_subs=False,
            half=0 # full game
        )
        player_times = team_object.get_on_pitch_periods()
        graphs = centrality.get_directed_graphs(
            pass_map,
            player_times,
            team_object,
            role_grouped=True
        )

        betweenness = centrality.current_flow_betweenness_directed(
            graphs['scaled_graph'],
            start_node=1 # goalkeeper role
        )
        print("Match {}, Opposing Formation {}/{}:\t {}".format(
            match_id,
            formation.opp_formation_1,
            formation.opp_formation_2,
            [r_id for r_id, _ in sorted(betweenness.items(), key=lambda t:-t[1])]
        ))

