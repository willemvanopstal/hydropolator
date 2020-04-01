import pandas as pd
import matplotlib as mpl
from matplotlib import pyplot as plt
import matplotlib.font_manager as fm
import matplotlib.ticker as ticker
import seaborn as sns
import numpy as np


# https://stackoverflow.com/a/7728665
rrPath = '/Users/Bonny/Documents/Thesis/Roboto/Roboto-Regular.ttf'
robotoRegularFont_title = fm.FontProperties(
    fname='/Users/Bonny/Documents/Thesis/Roboto/Roboto-Medium.ttf', size=12)
robotoRegularFont_legend = fm.FontProperties(fname=rrPath, size=7)
robotoRegularFont_axislabel = fm.FontProperties(fname=rrPath, size=10)
robotoRegularFont_ticks = fm.FontProperties(fname=rrPath, size=6)

trackerData = "stats_data_tracker6.csv"

data = pd.read_csv(trackerData, delimiter=';')

# filter data stats
# 0           0        conflicting_iso_vertices    209
# 1           0           conflicting_triangles    219
# 2           0  extended_conflicting_triangles   1078
# 3           0              vertices_to_smooth    832
# 4           0                updated_vertices    377
# 5           0      conflicting_sharp_vertices      0
# 6           0       conflicting_spur_vertices     89
# 7           0      conflicting_gully_vertices    120
# 8           0     conflicting_sharp_triangles      0
# 9           0      conflicting_spur_triangles    108
# 10          0     conflicting_gully_triangles    149
statsToKeep = ['conflicting_iso_vertices',
               'vertices_to_smooth', 'updated_vertices']
individualsToKeep = ['conflicting_sharp_vertices', 'conflicting_spur_vertices', 'conflicting_gully_vertices',
                     'conflicting_sharp_triangles', 'conflicting_spur_triangles', 'conflicting_gully_triangles',
                     'conflicting_iso_vertices', 'conflicting_triangles']
individualsToKeep = ['conflicting_sharp_vertices',
                     'conflicting_spur_vertices', 'conflicting_gully_vertices']

individual_data = data[data['stat'].isin(individualsToKeep)]

data = data[data['stat'].isin(statsToKeep)]


print(data)

####################################
# PROGRESS
####################################
plt.figure(1)

sns.set_style('whitegrid')
sns.set_context('paper', rc={"grid.linewidth": 0.2})

dfs = dict(tuple(data.groupby("stat")))
listdfs = [x for x in dfs]
ax = sns.lineplot(x="iteration", y="counter", hue="stat",
                  data=data, palette='colorblind', lw=1)
# ax.set(xlabel='region index', ylabel='portion [%]')
ax.set_xlabel('iteration', fontproperties=robotoRegularFont_axislabel)
ax.set_ylabel('count', fontproperties=robotoRegularFont_axislabel)

sns.despine()

# ax.lines[len(listdfs)-1].set_linestyle(":")
# ax.lines[len(listdfs)-1].set_linewidth(1)
# leg = ax.legend()
# leg_lines = leg.get_lines()
# leg_lines[len(listdfs)].set_linestyle(":")

# dfs = dict(tuple(data.groupby("stat")))
# handles, labels = ax.get_legend_handles_labels()
# print(handles)
# for i, df in enumerate(labels[1:]):
#     print(df)
#     alphaVal = 0.2
#     if df == "original":
#         alphaVal = 0.01
#     plt.fill_between("region", 0, "aandeel", data=dfs[df], alpha=alphaVal, color=pal[i])


plt.ylim(bottom=0)
plt.xlim(left=0)
plt.xticks(data.iteration[0::1], fontproperties=robotoRegularFont_ticks)
ax.xaxis.set_major_locator(ticker.MultipleLocator(5))
plt.yticks(fontproperties=robotoRegularFont_ticks)
ax.set_title("Conflicts and smoothened vertices", fontproperties=robotoRegularFont_title)
plt.legend(prop=robotoRegularFont_legend)


# fig = plt.gcf()
# fig.set_size_inches(14/2.54, 10/2.54)
# fig.savefig('iteration_tracker.pdf', dpi=100, tranparent=True)

# plt.show()


####################################
# INDIVIDUAL
####################################
plt.figure(2)

sns.set_style('whitegrid')
sns.set_context('paper', rc={"grid.linewidth": 0.2})
pal = sns.color_palette("Set2")

dfs = dict(tuple(individual_data.groupby("stat")))
listdfs = [x for x in dfs]
ax = sns.lineplot(x="iteration", y="counter", hue="stat",
                  data=individual_data, palette="Set2", lw=1, hue_order=listdfs)
# ax.set(xlabel='region index', ylabel='portion [%]')
ax.set_xlabel('iteration', fontproperties=robotoRegularFont_axislabel)
ax.set_ylabel('count', fontproperties=robotoRegularFont_axislabel)

sns.despine()

# ax.lines[len(listdfs)-1].set_linestyle(":")
# ax.lines[len(listdfs)-1].set_linewidth(1)
# leg = ax.legend()
# leg_lines = leg.get_lines()
# leg_lines[len(listdfs)].set_linestyle(":")

# dfs = dict(tuple(data.groupby("stat")))
# handles, labels = ax.get_legend_handles_labels()
# print(handles)
# for i, df in enumerate(labels[1:]):
#     print(df)
#     alphaVal = 0.2
#     if df == "original":
#         alphaVal = 0.01
#     plt.fill_between("region", 0, "aandeel", data=dfs[df], alpha=alphaVal, color=pal[i])


plt.ylim(bottom=0)
plt.xlim(left=0)
plt.xticks(individual_data.iteration[0::1], fontproperties=robotoRegularFont_ticks)
ax.xaxis.set_major_locator(ticker.MultipleLocator(5))
plt.yticks(fontproperties=robotoRegularFont_ticks)
ax.set_title("Conflicts and smoothened vertices", fontproperties=robotoRegularFont_title)
plt.legend(prop=robotoRegularFont_legend)


# fig = plt.gcf()
# fig.set_size_inches(14/2.54, 10/2.54)
# fig.savefig('iteration_tracker_individual.pdf', dpi=100, tranparent=True)

# plt.show()


####################################
# INDIVIDUAL STACKED
####################################
plt.figure(3)

sns.set_style('whitegrid')
sns.set_context('paper', rc={"grid.linewidth": 0.2})
pal = sns.color_palette("Set2")

dfs = dict(tuple(individual_data.groupby("stat")))
listdfs = [x for x in dfs]
print(listdfs)

# ax = sns.stackplot(x="iteration", y="count", hue="stat",
#                    data=individual_data, palette="Set2", lw=1)

iters = individual_data.iteration[individual_data.stat == listdfs[0]]
yValues = []
for stat in listdfs:
    yValues.append(list(individual_data.counter[individual_data.stat == stat]))

plt.stackplot(iters, yValues, labels=listdfs, colors=pal)
ax = plt.gca()

# ax.set(xlabel='region index', ylabel='portion [%]')
ax.set_xlabel('iteration', fontproperties=robotoRegularFont_axislabel)
ax.set_ylabel('counter', fontproperties=robotoRegularFont_axislabel)

sns.despine()

# ax.lines[len(listdfs)-1].set_linestyle(":")
# ax.lines[len(listdfs)-1].set_linewidth(1)
# leg = ax.legend()
# leg_lines = leg.get_lines()
# leg_lines[len(listdfs)].set_linestyle(":")

# dfs = dict(tuple(data.groupby("stat")))
# handles, labels = ax.get_legend_handles_labels()
# print(handles)
# for i, df in enumerate(labels[1:]):
#     print(df)
#     alphaVal = 0.2
#     if df == "original":
#         alphaVal = 0.01
#     plt.fill_between("region", 0, "aandeel", data=dfs[df], alpha=alphaVal, color=pal[i])


plt.ylim(bottom=0)
plt.xlim(left=0)
plt.xticks(individual_data.iteration[0::1], fontproperties=robotoRegularFont_ticks)
ax.xaxis.set_major_locator(ticker.MultipleLocator(5))
plt.yticks(fontproperties=robotoRegularFont_ticks)
ax.set_title("Conflicting iso vertices per metric", fontproperties=robotoRegularFont_title)
plt.legend(prop=robotoRegularFont_legend)


# fig = plt.gcf()
# fig.set_size_inches(14/2.54, 10/2.54)
# fig.savefig('iteration_tracker_individual.pdf', dpi=100, tranparent=True)

plt.show()

'''
####################################
# DEPARE CHANGE
####################################
# print(data)
plt.figure(2)

data = data.drop(data[data.process == 'original'].index)


sns.set_style('whitegrid')
sns.set_context('paper', rc={"grid.linewidth": 0.2})
pal = sns.color_palette("Set2")

ax = sns.lineplot(x="region", y="aandeel_diff", hue="process",
                  data=data, palette="Set2", lw=1)
# ax.set(xlabel='region index', ylabel='abs change in portion [%]')
ax.set_xlabel('region index', fontproperties=robotoRegularFont_axislabel)
ax.set_ylabel('abs change in portion [%]', fontproperties=robotoRegularFont_axislabel)

ax.lines[len(listdfs)-1].set_linestyle(":")
ax.lines[len(listdfs)-1].set_linewidth(0)
dfs = dict(tuple(data.groupby("process")))
handles, labels = ax.get_legend_handles_labels()
for i, df in enumerate(labels[1:]):
    if df == 'process':
        continue
    alphaVal = 0.2
    if df == "original":
        alphaVal = 0.00
    plt.fill_between("region", 0, "aandeel_diff", data=dfs[df], alpha=alphaVal, color=pal[i])

plt.xlim(left=0)
# plt.xticks(data.region[0::1])
plt.xticks(data.region[0::1], fontproperties=robotoRegularFont_ticks)
plt.yticks(fontproperties=robotoRegularFont_ticks)
ax.set_title("Morfology changes", fontproperties=robotoRegularFont_title)
plt.legend(prop=robotoRegularFont_legend)
sns.despine()


fig = plt.gcf()
fig.set_size_inches(14/2.54, 10/2.54)
fig.savefig('changes_depare.pdf', dpi=100, transparent=True)
# plt.show()


####################################
# DEPARE TOGETHER SUBS
####################################

data = pd.read_csv(depareTogetherDataFile, delimiter=';')

data['aandeel_diff'] = 0.0
for i in range(1, len(data) + 1):
    indexAandeel = data.columns.get_loc('aandeel')
    indexRegion = data.columns.get_loc('region')
    indexDiff = data.columns.get_loc('aandeel_diff')
    regionVal = data.iat[i-1, indexRegion]
    currentVal = data.iat[i-1, indexAandeel]
    originalValue = data.loc[(data['process'] == 'original') &
                             (data['region'] == regionVal), 'aandeel'].values[0]
    diffAandeel = currentVal - originalValue
    data.iat[i-1, indexDiff] = diffAandeel

# print(data)

fig = plt.figure(3)
fig.subplots_adjust(hspace=0.5)
plt.subplot(2, 1, 1)

sns.set_style('whitegrid')
sns.set_context('paper', rc={"grid.linewidth": 0.2})
pal = sns.color_palette("Set2")
sns.despine()

dfs = dict(tuple(data.groupby("process")))
listdfs = [x for x in dfs]
ax = sns.lineplot(x="region", y="aandeel", hue="process",
                  data=data, palette="Set2", lw=1)
ax.set(xlabel='region index', ylabel='portion [%]')
ax.set_xlabel('region index', fontproperties=robotoRegularFont_axislabel)
ax.set_ylabel('portion [%]', fontproperties=robotoRegularFont_axislabel)


ax.lines[len(listdfs)-1].set_linestyle(":")
ax.lines[len(listdfs)-1].set_linewidth(1)
leg = ax.legend()
leg_lines = leg.get_lines()
leg_lines[len(listdfs)].set_linestyle(":")
dfs = dict(tuple(data.groupby("process")))
handles, labels = ax.get_legend_handles_labels()
for i, df in enumerate(labels[1:]):
    alphaVal = 0.2
    if df == "original":
        alphaVal = 0.01
    plt.fill_between("region", 0, "aandeel", data=dfs[df], alpha=alphaVal, color=pal[i])

plt.ylim(bottom=0)
plt.xlim(left=0)
plt.xticks(data.region[0::1], fontproperties=robotoRegularFont_ticks)
plt.yticks(fontproperties=robotoRegularFont_ticks)
ax.set_title("Morfology histogram", fontproperties=robotoRegularFont_title)
plt.legend(prop=robotoRegularFont_legend)

plt.subplot(2, 1, 2)

data = data.drop(data[data.process == 'original'].index)


sns.set_style('whitegrid')
sns.set_context('paper', rc={"grid.linewidth": 0.2})
pal = sns.color_palette("Set2")
sns.despine()

ax = sns.lineplot(x="region", y="aandeel_diff", hue="process",
                  data=data, palette="Set2", lw=1)
# ax.set(xlabel='region index', ylabel='abs change in portion [%]')
ax.set_xlabel('region index', fontproperties=robotoRegularFont_axislabel)
ax.set_ylabel('abs change in portion [%]', fontproperties=robotoRegularFont_axislabel)

ax.lines[len(listdfs)-1].set_linestyle(":")
ax.lines[len(listdfs)-1].set_linewidth(0)
dfs = dict(tuple(data.groupby("process")))
handles, labels = ax.get_legend_handles_labels()
for i, df in enumerate(labels[1:]):
    if df == 'process':
        continue
    alphaVal = 0.2
    if df == "original":
        alphaVal = 0.00
    plt.fill_between("region", 0, "aandeel_diff", data=dfs[df], alpha=alphaVal, color=pal[i])

plt.xlim(left=0)
plt.xticks(data.region[0::1], fontproperties=robotoRegularFont_ticks)
plt.yticks(fontproperties=robotoRegularFont_ticks)
ax.set_title("Morfology changes", fontproperties=robotoRegularFont_title)
plt.legend(prop=robotoRegularFont_legend)

fig = plt.gcf()
fig.set_size_inches(14/2.54, 16/2.54)
fig.savefig('together_depare.pdf', dpi=100, transparent=True)

####################################
# DEPARE RIDGE PLOT
####################################
plt.figure(4)

sns.set(style="whitegrid", rc={"axes.facecolor": (0, 0, 0, 0)})
sns.set_context('paper', rc={"grid.linewidth": 0.2})

df = pd.read_csv(depareTogetherDataFile, delimiter=';')
df.loc[df["aandeel"] == 0, "aandeel"] = np.nan

# Initialize the FacetGrid object
pal = sns.color_palette("Set2")
g = sns.FacetGrid(df, row="process", hue="process", aspect=10, height=0.6, palette=pal)

# Draw the densities in a few steps
g.map(sns.lineplot, "region", "aandeel", clip_on=False, alpha=1, lw=0)
g.map(plt.fill_between, "region", "aandeel", interpolate=True, alpha=0.6)
# g.map(sns.lineplot, "region", "aandeel", clip_on=False, color="w", lw=1.5)


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

plt.xlabel('region index', fontproperties=robotoRegularFont_axislabel)
# g.set_ylabel('abs change in portion [%]', fontproperties=robotoRegularFont_axislabel)
g.set(yticks=[])
g.set(xticks=df.region[0::1])
plt.xticks(df.region[0::1], fontproperties=robotoRegularFont_ticks)
g.despine(bottom=True, left=True)
plt.subplots_adjust(top=0.92)
g.fig.suptitle("Morfology histograms", fontproperties=robotoRegularFont_title)


# plt.show()
fig = plt.gcf()
fig.set_size_inches(14/2.54, 8/2.54)
fig.savefig('ridge_depare.pdf', dpi=100, transparent=True)
'''
