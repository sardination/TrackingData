import formations
import OPTA as opta
import OPTA_weighted_networks as onet


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

test_f = copenhagen_formations[1]
# test_f.get_formation_graph()

# all_copenhagen_match_ids = [984567]

# for match_id in all_copenhagen_match_ids:
for formation in copenhagen_formations:
    match_id = formation.match_id
    fname = str(match_id)
    match_OPTA = opta.read_OPTA_f7(fpath, fname)
    match_OPTA = opta.read_OPTA_f24(fpath, fname, match_OPTA)

    home_or_away = "home"
    home_team = onet.get_team(match_OPTA, team="home")
    away_team = onet.get_team(match_OPTA, team="away")
    if home_team.team_id != copenhagen_team_id:
        home_or_away = "away"

    pass_map = onet.get_all_pass_destinations(match_OPTA, team=home_or_away, exclude_subs=False)
    formation.get_formation_graph(pass_map=pass_map)
