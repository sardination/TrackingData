import formations
import OPTA as opta
import OPTA_weighted_networks as onet


def split_by_wins(matches, team_id):
    """
    Return dict of lists keyed by win, loss, or tie

    Args:
        matches (dict): keyed by match_id
        team_id (int): team id

    Returns:
        sorted_matches, scores (dict, dict): keyed by match_id. first is list of
            matches and second is tuple of score
    """

    sorted_matches = {
        "wins": [],
        "losses": [],
        "ties": []
    }

    scores = {}

    for match_id, match in matches.items():
        this_team_score = 0
        other_team_score = 0
        if match.hometeam.team_id == team_id:
            this_team_score = match.homegoals
            other_team_score = match.awaygoals
        elif match.awayteam.team_id == team_id:
            this_team_score = match.awaygoals
            other_team_score = match.homegoals
        else:
            continue

        scores[match_id] = (this_team_score, other_team_score)

        if this_team_score > other_team_score:
            sorted_matches["wins"].append(match_id)
        elif this_team_score < other_team_score:
            sorted_matches["losses"].append(match_id)
        else:
            sorted_matches["ties"].append(match_id)

    return sorted_matches, scores


def split_by_home(matches, team_id):
    """
    Return dict of lists keyed by home or away

    Args:
        matches (dict): keyed by match_id
        team_id (int): team id
    """

    sorted_matches = {
        "home": [],
        "away": []
    }

    for match_id, match in matches.items():
        if match.hometeam.team_id == team_id:
            sorted_matches["home"].append(match_id)
        elif match.awayteam.team_id == team_id:
            sorted_matches["away"].append(match_id)

    return sorted_matches


def split_by_opposing_formation(formations):
    """
    Args:
        formations (dict): dictionary of Formation objects keyed by match id

    Return:
        first_half, second_half (dict, dict): keyed by formation number and has match id value lists
    """

    first_half = {}
    second_half = {}

    for match_id, formation in formations.items():
        try:
            first_half[formation.opp_formation_1].append(match_id)
        except KeyError:
            first_half[formation.opp_formation_1] = [match_id]

        try:
            second_half[formation.opp_formation_2].append(match_id)
        except KeyError:
            second_half[formation.opp_formation_2] = [match_id]

    return first_half, second_half


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

copenhagen_formations = formations.read_formations_from_csv('../copenhagen_formations.csv', copenhagen_team_id)
copenhagen_formations = {formation.match_id: formation for formation in copenhagen_formations}

matches = {}
pass_maps = {}
first_half_pass_maps = {}
second_half_pass_maps = {}
for match_id in all_copenhagen_match_ids:
    fname = str(match_id)
    match_OPTA = opta.read_OPTA_f7(fpath, fname)
    match_OPTA = opta.read_OPTA_f24(fpath, fname, match_OPTA)
    matches[match_id] = match_OPTA

    if match_OPTA.hometeam.team_id == copenhagen_team_id:
        copenhagen_formations[match_id].add_team_object(match_OPTA.hometeam)
        pass_maps[match_id] = onet.get_all_pass_destinations(match_OPTA, team="home")
        first_half_pass_maps[match_id] = onet.get_all_pass_destinations(match_OPTA, team="home", half=1)
        second_half_pass_maps[match_id] = onet.get_all_pass_destinations(match_OPTA, team="home", half=2)
    else:
        copenhagen_formations[match_id].add_team_object(match_OPTA.awayteam)
        pass_maps[match_id] = onet.get_all_pass_destinations(match_OPTA, team="away")
        first_half_pass_maps[match_id] = onet.get_all_pass_destinations(match_OPTA, team="away", half=1)
        second_half_pass_maps[match_id] = onet.get_all_pass_destinations(match_OPTA, team="away", half=2)

    copenhagen_formations[match_id].add_goalkeeper()

if False:
    win_or_loss_dict, scores = split_by_wins(matches, copenhagen_team_id)
    for match_id in win_or_loss_dict["losses"]:
        formation = copenhagen_formations[match_id]
        print(scores[match_id])
        formation.get_formation_graph_by_role(pass_maps[match_id])


if False:
    home_or_away_dict = split_by_home(matches, copenhagen_team_id)
    for match_id in home_or_away_dict["away"]:
        formation = copenhagen_formations[match_id]
        formation.get_formation_graph_by_role(pass_maps[match_id])


if True:
    first_half, second_half = split_by_opposing_formation(copenhagen_formations)
    formation_groups = [(1, 2, 3, 15), (9, 11), (12,)]

    for group in formation_groups:
        print(group)
        for formation_id in group:
            for match_id in first_half.get(str(formation_id), []):
                formation = copenhagen_formations[match_id]
                print(formation.opp_formation_1)
                formation.get_formation_graph_by_role(first_half_pass_maps[match_id])
            for match_id in second_half.get(str(formation_id), []):
                formation = copenhagen_formations[match_id]
                print(formation.opp_formation_2)
                formation.get_formation_graph_by_role(second_half_pass_maps[match_id])


