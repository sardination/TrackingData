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

copenhagen_formations = formations.read_formations_from_csv('../copenhagen_formations.csv', copenhagen_team_id)
copenhagen_formations = {formation.match_id: formation for formation in copenhagen_formations}

matches = {}
copenhagen_team_objects = {}
copenhagen_home_away = {}
pass_maps = {}

for match_id in all_copenhagen_match_ids:
    fname = str(match_id)
    match_OPTA = opta.read_OPTA_f7(fpath, fname)
    match_OPTA = opta.read_OPTA_f24(fpath, fname, match_OPTA)
    matches[match_id] = match_OPTA

    if match_OPTA.hometeam.team_id == copenhagen_team_id:
        copenhagen_team_objects[match_id] = match_OPTA.hometeam
        copenhagen_home_away[match_id] = "home"
    else:
        copenhagen_team_objects[match_id] = match_OPTA.awayteam
        copenhagen_home_away[match_id] = "away"

    pass_maps[match_id] = onet.get_all_pass_destinations(
        matches[match_id],
        team=copenhagen_home_away[match_id],
        exclude_subs=False,
        half=0
    )

# Find most popular triplets
triplet_count = {}
top_5_triplet_count = {}
for match_id, match in matches.items():
    team_object = copenhagen_team_objects[match_id]
    home_or_away = copenhagen_home_away[match_id]
    pass_map = onet.get_all_pass_destinations(match, team=home_or_away, exclude_subs=False, half=0)

    role_mappings, role_pass_map = onet.convert_pass_map_to_roles(team_object, pass_map)
    triplet_list_by_id = onet.find_player_triplets_by_team(team_object, half=0) # full match
    triplet_list = []
    for triplet, num_passes in triplet_list_by_id:
        new_triplet = []
        for p in triplet:
            new_triplet.append(role_mappings[p])
        triplet_list.append((tuple(sorted(new_triplet)), num_passes))

    this_match_triplets = {}
    for triplet, num_passes in triplet_list:
        try:
            triplet_count[triplet] += num_passes
        except KeyError:
            triplet_count[triplet] = num_passes

        try:
            this_match_triplets[triplet] += num_passes
        except KeyError:
            this_match_triplets[triplet] = num_passes

    for triplet, num_passes in sorted(this_match_triplets.items(), key=lambda t: -t[1])[:5]:
        try:
            top_5_triplet_count[triplet] += 1
        except KeyError:
            top_5_triplet_count[triplet] = 1

top_5_triplet_count_sorted = sorted(top_5_triplet_count.items(), key=lambda t:-t[1])
print(top_5_triplet_count_sorted)
triplet_count_sorted = sorted(triplet_count.items(), key=lambda t:-t[1])[:10]
print(triplet_count_sorted)

print()
print("------ AVERAGE FORMATION ------")
all_players = []
for formation in copenhagen_formations.values():
    all_players.extend(pass_maps[formation.match_id].keys())
all_players = list(set(all_players))
average_pass_map = {p_id: {r_id: {
                        "num_passes": 0,
                        "avg_pass_dist": 0,
                        "avg_pass_dir": 0,
                        "total_appearances": 0
                    } for r_id in all_players} for p_id in all_players}
average_role_pass_map = {p_id: {r_id: {
    "num_passes": 0,
    "avg_pass_dist": 0,
    "avg_pass_dir": 0,
    "total_appearances": 0
} for r_id in range(1, 12)} for p_id in range(1, 12)}
transfer_map = {}

for match_id, formation in copenhagen_formations.items():
    match = matches[match_id]
    team_object = copenhagen_team_objects[match_id]
    formation.add_team_object(team_object)
    formation.add_goalkeeper()
    home_or_away = copenhagen_home_away[match_id]
    pass_map = pass_maps[match_id]

    for p_id, p_dict in pass_map.items():
        for r_id, pass_info in p_dict.items():
            average_pass_map[p_id][r_id]["num_passes"] += pass_info["num_passes"]
            average_pass_map[p_id][r_id]["avg_pass_dist"] += pass_info["avg_pass_dist"]
            average_pass_map[p_id][r_id]["avg_pass_dir"] += pass_info["avg_pass_dir"]
            average_pass_map[p_id][r_id]["total_appearances"] += 1

    role_mappings, role_pass_map = onet.convert_pass_map_to_roles(team_object, pass_map)

    for p_id, p_dict, in role_pass_map.items():
        for r_id, pass_info in p_dict.items():
            average_role_pass_map[p_id][r_id]["num_passes"] += pass_info["num_passes"]
            average_role_pass_map[p_id][r_id]["avg_pass_dist"] += pass_info["avg_pass_dist"]
            average_role_pass_map[p_id][r_id]["avg_pass_dir"] += pass_info["avg_pass_dir"]
            average_role_pass_map[p_id][r_id]["total_appearances"] += 1

    # for p_id, role_id in role_mappings.items():
    #     current_role = transfer_map.get(p_id)
    #     if current_role is not None and current_role != role_id:
    #         print("Differing roles for player {}: {} and {}".format(p_id, current_role, role_id))

    #     transfer_map[p_id] = role_id

num_formations = len(copenhagen_formations.values())
for p_id in all_players:
    for r_id in all_players:
        pass_dict = average_pass_map[p_id][r_id]
        if pass_dict["total_appearances"] == 0:
            average_pass_map[p_id][r_id] = {
                "num_passes": pass_dict["num_passes"] / num_formations,
                "avg_pass_dist": 0,
                "avg_pass_dir": 0
            }
            continue
        average_pass_map[p_id][r_id] = {
            "num_passes": pass_dict["num_passes"] / num_formations,
            "avg_pass_dist": pass_dict["avg_pass_dist"] / pass_dict["total_appearances"],
            "avg_pass_dir": pass_dict["avg_pass_dir"] / pass_dict["total_appearances"]
        }

for p_id in range(1, 12):
    for r_id in range(1, 12):
        pass_dict = average_role_pass_map[p_id][r_id]
        if pass_dict["total_appearances"] == 0:
            average_pass_map[p_id][r_id] = {
                "num_passes": pass_dict["num_passes"] / num_formations,
                "avg_pass_dist": 0,
                "avg_pass_dir": 0
            }
            continue
        average_role_pass_map[p_id][r_id] = {
            "num_passes": pass_dict["num_passes"] / num_formations,
            "avg_pass_dist": pass_dict["avg_pass_dist"] / pass_dict["total_appearances"],
            "avg_pass_dir": pass_dict["avg_pass_dir"] / pass_dict["total_appearances"]
        }

average_formation = formations.average_formations(copenhagen_formations.values())
average_formation.get_formation_graph(pass_map=average_role_pass_map)
