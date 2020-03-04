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

matches = {}
copenhagen_team_objects = {}
copenhagen_home_away = {}

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


