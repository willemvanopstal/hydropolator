import pandas as pd
from matplotlib import pyplot as plt
import seaborn as sns
import numpy as np

depareTogetherDataFile = "stats_together_data_ang.csv"

data = pd.read_csv(depareTogetherDataFile, delimiter=';')
data['interval'] = data['interval'].astype('str')


# data['aandeel_diff'] = 0.0
# for i in range(1, len(data) + 1):
#     indexAandeel = data.columns.get_loc('aandeel')
#     indexRegion = data.columns.get_loc('region')
#     indexDiff = data.columns.get_loc('aandeel_diff')
#     regionVal = data.iat[i-1, indexRegion]
#     currentVal = data.iat[i-1, indexAandeel]
#     # print(data.iat[i-1, indexRegion])
#     # print('\nregion: {} aandeel: {}'.format(regionVal, currentVal))
#     originalValue = data.loc[(data['process'] == 'original') &
#                              (data['region'] == regionVal), 'aandeel'].values[0]
#     # print('original aandeel: {}'.format(originalValue))
#     diffAandeel = currentVal - originalValue
#     # print(diffAandeel)
#     data.iat[i-1, indexDiff] = diffAandeel
#
# # for processName in dfs:
# #     print(processName)
# #
# #     data.loc[data["process"] == 'original']
# #     # diffName = processName + '_diff'
# #     # data[diffName] = data[processName] - data['original']
print(data)

####################################
# ABS HISTOGRAM
####################################
fig = plt.figure(1)

sns.set_style('whitegrid')
sns.set_context('paper', rc={"grid.linewidth": 0.2})
pal = sns.color_palette("Set2")

dfs = dict(tuple(data.groupby("process")))
# print(dfs)
listdfs = [x for x in dfs]
ax = sns.lineplot(x="intervalindex", y="aandeel", hue="process",
                  data=data, palette="Set2", lw=1)
ax.set(xlabel='interval of change [m]', ylabel='number of changes')

sns.despine()

ax.lines[len(listdfs)-1].set_linestyle(":")
ax.lines[len(listdfs)-1].set_linewidth(1)
leg = ax.legend()
leg_lines = leg.get_lines()
leg_lines[len(listdfs)].set_linestyle(":")

dfs = dict(tuple(data.groupby("process")))
print(data.interval.unique())
intervalNames = data.interval.unique()
# print(dfs)
# listdfs = [x for x in dfs]
handles, labels = ax.get_legend_handles_labels()
print(handles)
print(labels[1:])
for i, df in enumerate(labels[1:]):
    print("filling: ", df)
    print(dfs[df])
    # print(df)
    # print(pal[i])
    alphaVal = 0.2
    if df == "original":
        alphaVal = 0.01
    plt.fill_between("intervalindex", -1, "aandeel", data=dfs[df], alpha=alphaVal, color=pal[i])


# plt.fill_between("region", "aandeel", data=data,
#                  alpha=0.4, color="r")
fig.subplots_adjust(bottom=0.25)  # or whatever
plt.ylim(bottom=0)
# ax.set_xlim(20, None)
plt.xlim(left=0)
plt.xticks(data.intervalindex[0::1], rotation=90, fontsize='x-small')
ax.set_xticklabels(intervalNames)

ax.set_title("Absolute changes histogram")

# plt.show()
fig = plt.gcf()
fig.set_size_inches(14/2.54, 10/2.54)
fig.savefig('hist_ang.pdf', dpi=100)

# plt.show()

# ####################################
# # DEPARE CHANGE
# ####################################
# # print(data)
# plt.figure(2)
#
# data = data.drop(data[data.process == 'original'].index)
#
#
# sns.set_style('whitegrid')
# sns.set_context('paper', rc={"grid.linewidth": 0.2})
# pal = sns.color_palette("Set2")
#
# # data = pd.read_csv('stats_together_data.csv', delimiter=';')
# # dfs = dict(tuple(data.groupby("process")))
# # print(dfs)
# # listdfs = [x for x in dfs]
# ax = sns.lineplot(x="region", y="aandeel_diff", hue="process",
#                   data=data, palette="Set2", lw=1)
# ax.set(xlabel='region index', ylabel='abs change in portion [%]')
#
#
# ax.lines[len(listdfs)-1].set_linestyle(":")
# ax.lines[len(listdfs)-1].set_linewidth(0)
# dfs = dict(tuple(data.groupby("process")))
# # print(dfs)
# # listdfs = [x for x in dfs]
# handles, labels = ax.get_legend_handles_labels()
# # print(labels[1:])
# for i, df in enumerate(labels[1:]):
#     if df == 'process':
#         continue
#     # print(df)
#     # print(pal[i])
#     alphaVal = 0.2
#     if df == "original":
#         alphaVal = 0.00
#     plt.fill_between("region", 0, "aandeel_diff", data=dfs[df], alpha=alphaVal, color=pal[i])
#
#
# # plt.fill_between("region", "aandeel", data=data,
# #                  alpha=0.4, color="r")
# # plt.ylim(bottom=0)
# plt.xlim(left=0)
# plt.xticks(data.region[0::1])
# ax.set_title("Morfology changes")
# sns.despine()
#
#
# fig = plt.gcf()
# fig.set_size_inches(14/2.54, 10/2.54)
# fig.savefig('depare_changes.pdf', dpi=100)
# # plt.show()
#
#
# ####################################
# # DEPARE TOGETHER SUBS
# ####################################
#
# data = pd.read_csv(depareTogetherDataFile, delimiter=';')
#
# data['aandeel_diff'] = 0.0
# for i in range(1, len(data) + 1):
#     indexAandeel = data.columns.get_loc('aandeel')
#     indexRegion = data.columns.get_loc('region')
#     indexDiff = data.columns.get_loc('aandeel_diff')
#     regionVal = data.iat[i-1, indexRegion]
#     currentVal = data.iat[i-1, indexAandeel]
#     # print(data.iat[i-1, indexRegion])
#     # print('\nregion: {} aandeel: {}'.format(regionVal, currentVal))
#     originalValue = data.loc[(data['process'] == 'original') &
#                              (data['region'] == regionVal), 'aandeel'].values[0]
#     # print('original aandeel: {}'.format(originalValue))
#     diffAandeel = currentVal - originalValue
#     # print(diffAandeel)
#     data.iat[i-1, indexDiff] = diffAandeel
#
# # for processName in dfs:
# #     print(processName)
# #
# #     data.loc[data["process"] == 'original']
# #     # diffName = processName + '_diff'
# #     # data[diffName] = data[processName] - data['original']
# print(data)
#
# fig = plt.figure(3)
# fig.subplots_adjust(hspace=0.5)
# plt.subplot(2, 1, 1)
#
# sns.set_style('whitegrid')
# sns.set_context('paper', rc={"grid.linewidth": 0.2})
# pal = sns.color_palette("Set2")
# sns.despine()
#
# dfs = dict(tuple(data.groupby("process")))
# # print(dfs)
# listdfs = [x for x in dfs]
# ax = sns.lineplot(x="region", y="aandeel", hue="process",
#                   data=data, palette="Set2", lw=1)
# ax.set(xlabel='region index', ylabel='portion [%]')
#
#
# ax.lines[len(listdfs)-1].set_linestyle(":")
# ax.lines[len(listdfs)-1].set_linewidth(1)
# leg = ax.legend()
# leg_lines = leg.get_lines()
# leg_lines[len(listdfs)].set_linestyle(":")
# dfs = dict(tuple(data.groupby("process")))
# # print(dfs)
# # listdfs = [x for x in dfs]
# handles, labels = ax.get_legend_handles_labels()
# # print(labels[1:])
# for i, df in enumerate(labels[1:]):
#     # print(df)
#     # print(pal[i])
#     alphaVal = 0.2
#     if df == "original":
#         alphaVal = 0.01
#     plt.fill_between("region", 0, "aandeel", data=dfs[df], alpha=alphaVal, color=pal[i])
#
#
# # plt.fill_between("region", "aandeel", data=data,
# #                  alpha=0.4, color="r")
# plt.ylim(bottom=0)
# plt.xlim(left=0)
# plt.xticks(data.region[0::1])
# ax.set_title("Morfology histogram")
#
# plt.subplot(2, 1, 2)
#
# data = data.drop(data[data.process == 'original'].index)
#
#
# sns.set_style('whitegrid')
# sns.set_context('paper', rc={"grid.linewidth": 0.2})
# pal = sns.color_palette("Set2")
# sns.despine()
#
# # data = pd.read_csv('stats_together_data.csv', delimiter=';')
# # dfs = dict(tuple(data.groupby("process")))
# # print(dfs)
# # listdfs = [x for x in dfs]
# ax = sns.lineplot(x="region", y="aandeel_diff", hue="process",
#                   data=data, palette="Set2", lw=1)
# ax.set(xlabel='region index', ylabel='abs change in portion [%]')
#
#
# ax.lines[len(listdfs)-1].set_linestyle(":")
# ax.lines[len(listdfs)-1].set_linewidth(0)
# dfs = dict(tuple(data.groupby("process")))
# # print(dfs)
# # listdfs = [x for x in dfs]
# handles, labels = ax.get_legend_handles_labels()
# # print(labels[1:])
# for i, df in enumerate(labels[1:]):
#     if df == 'process':
#         continue
#     # print(df)
#     # print(pal[i])
#     alphaVal = 0.2
#     if df == "original":
#         alphaVal = 0.00
#     plt.fill_between("region", 0, "aandeel_diff", data=dfs[df], alpha=alphaVal, color=pal[i])
#
#
# # plt.fill_between("region", "aandeel", data=data,
# #                  alpha=0.4, color="r")
# # plt.ylim(bottom=0)
# plt.xlim(left=0)
# plt.xticks(data.region[0::1])
# ax.set_title("Morfology changes")
#
# fig = plt.gcf()
# fig.set_size_inches(14/2.54, 16/2.54)
# fig.savefig('depare_together.pdf', dpi=100)
'''
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
g.set(yticks=[])
g.set(xticks=df.region[0::1])
g.despine(bottom=True, left=True)

# plt.show()
fig = plt.gcf()
fig.set_size_inches(14/2.54, 10/2.54)
fig.savefig('depare_ridge.pdf', dpi=100)
'''
