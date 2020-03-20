import pandas as pd
from matplotlib import pyplot as plt
import seaborn as sns
import numpy as np
sns.set_style('whitegrid')

data = pd.read_csv('stats_together_data.csv', delimiter=';')
data.reindex(index=data.index[::-1])

# print(data)
# ax = sns.lineplot(x="region", y="aandeel", hue="process",
#                   data=data, palette='deep')
# # plt.show()
#
# ax = sns.violinplot(x="process", y="region", data=data, bw=0.2)

# plt.show()

# ax.show()

sns.set(style="whitegrid", rc={"axes.facecolor": (0, 0, 0, 0)})

# Create the data
rs = np.random.RandomState(1979)
x = rs.randn(500)
g = np.tile(list("ABCDEFGHIJ"), 50)
df = pd.DataFrame(dict(x=x, g=g))
print(df)
m = df.g.map(ord)
# df["x"] += m
print(df)
df = data

# Initialize the FacetGrid object
pal = sns.cubehelix_palette(10, rot=-.25, light=.7)
g = sns.FacetGrid(df, row="process", hue="process", aspect=10, height=0.6, palette=pal)

# Draw the densities in a few steps
g.map(sns.lineplot, "region", "aandeel", clip_on=False, alpha=1, lw=1.5)
g.map(plt.fill_between, "region", "aandeel")
g.map(sns.lineplot, "region", "aandeel", clip_on=False, color="w", lw=2)
g.map(plt.axhline, y=0, lw=1, clip_on=False)


# Define and use a simple function to label the plot in axes coordinates
def label(x, color, label):
    ax = plt.gca()
    ax.text(0, .2, label, fontweight="bold", color=color,
            ha="left", va="center", transform=ax.transAxes)


g.map(label, "region")

# Set the subplots to overlap
g.fig.subplots_adjust(hspace=-.25)

# Remove axes details that don't play well with overlap
g.set_titles("")
g.set(yticks=[])
g.set(xticks=df.region[0::1])
g.despine(bottom=True, left=True)

plt.show()
