import similarity

f1 = [8, 5, 2, 4, 6, 3, 11, 7, 10, 1, 9]
f2 = [2, 3, 6, 4, 5, 11, 8, 7, 10, 9, 1]

print(similarity.swap_distance(f1, f2))

f1 = [8, 5, 6, 4, 2, 3, 11, 7, 10, 1, 9]
f2 = [6, 3, 4, 2, 8, 5, 11, 7, 10, 1, 9]

print(similarity.swap_distance(f1, f2))

f1 = [5, 8, 6, 2, 4, 11, 3, 10, 1, 7, 9]
f2 = [8, 5, 2, 6, 7, 11, 3, 1, 10, 4, 9]

print(similarity.swap_distance(f1, f2))

f1 = [2, 4, 3, 6, 5, 7, 9, 8, 11, 10, 1]
f2 = [3, 6, 4, 2, 11, 5, 10, 1, 7, 8, 9]

print(similarity.swap_distance(f1, f2))