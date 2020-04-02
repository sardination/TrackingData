import matplotlib.pyplot as plt
import networkx as nx

clustering_demo = nx.DiGraph()

types = [
    [("u", "v"), ("v", "w"), ("w", "u")],
    [("u", "w"), ("w", "v"), ("v", "u")],
    [("u", "v"), ("u", "w"), ("v", "w")],
    [("u", "v"), ("u", "w"), ("w", "v")],
    [("v", "u"), ("w", "u"), ("v", "w")],
    [("v", "u"), ("w", "u"), ("w", "v")],
    [("u", "v"), ("w", "u"), ("w", "v")],
    [("u", "w"), ("v", "u"), ("v", "w")]
]

types = [
    [("u", "v"), ("v", "u"), ("u", "w")],
    [("u", "v"), ("v", "u"), ("w", "u")],
    [("u", "w"), ("w", "u"), ("v", "u")],
    [("u", "w"), ("w", "u"), ("v", "u")],
]

positions = {}
colors = {}
labels = {}
u = 0

u_x = 0
u_y = 10
v_x = 10
v_y = 15
w_x = 10
w_y = 5

for i, type in enumerate(types):
    node_dict = {
        "u": u,
        "v": u + 1,
        "w": u + 2
    }

    positions[u] = (u_x, u_y)
    positions[u + 1] = (v_x, v_y)
    positions[u + 2] = (w_x, w_y)

    colors[u] = "#aed6f1"
    colors[u + 1] = "#f9e79f"
    colors[u + 2] = "#f9e79f"

    labels[u] = "u"
    labels[u + 1] = "v"
    labels[u + 2] = "w"

    u_y = -u_y
    temp = v_y
    v_y = -w_y
    w_y = -temp
    if i % 2 == 1:
        u_x += 20
        v_x += 20
        w_x += 20

    for edge in type:
        clustering_demo.add_edge(node_dict[edge[0]], node_dict[edge[1]])

    u += 3

nx.draw_networkx_edges(
    clustering_demo,
    positions
)
nx.draw_networkx_nodes(
    clustering_demo,
    positions,
    node_color = [colors[node] for node in clustering_demo.nodes()]
)
nx.draw_networkx_labels(
    clustering_demo,
    positions,
    labels,
    font_size=12,
    font_family='sans-serif',
    font_color='black'
)
plt.axis('off')
plt.show()

