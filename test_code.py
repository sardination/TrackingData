import formations

copenhagen_formations = formations.read_formations_from_csv('../copenhagen_formations.csv')

test_f = copenhagen_formations[1]
test_f.get_formation_graph()