import pandas as pd
import matplotlib as mpl
from matplotlib import pyplot as plt
import matplotlib.font_manager as fm
import seaborn as sns
import numpy as np


# https://stackoverflow.com/a/7728665
rrPath = '/Users/Bonny/Documents/Thesis/Roboto/Roboto-Regular.ttf'
robotoRegularFont_title = fm.FontProperties(
    fname='/Users/Bonny/Documents/Thesis/Roboto/Roboto-Medium.ttf', size=12)
robotoRegularFont_legend = fm.FontProperties(fname=rrPath, size=7)
robotoRegularFont_axislabel = fm.FontProperties(fname=rrPath, size=10)
robotoRegularFont_ticks = fm.FontProperties(fname=rrPath, size=6)

depareTogetherDataFile = "stats_together_data_ang.csv"

data = pd.read_csv(depareTogetherDataFile, delimiter=';')
data['interval'] = data['interval'].astype('str')

print(data)

####################################
# ANG HISTOGRAM
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
ax.set_xlabel('angularity [rad]', fontproperties=robotoRegularFont_axislabel)
ax.set_ylabel('aandeel [%]', fontproperties=robotoRegularFont_axislabel)

sns.despine()

ax.lines[len(listdfs)-1].set_linestyle(":")
ax.lines[len(listdfs)-1].set_linewidth(1)
leg = ax.legend()
leg_lines = leg.get_lines()
leg_lines[len(listdfs)].set_linestyle(":")

dfs = dict(tuple(data.groupby("process")))
print(data.interval.unique())
intervalNames = data.interval.unique()
handles, labels = ax.get_legend_handles_labels()
print(handles)
print(labels[1:])
for i, df in enumerate(labels[1:]):
    print("filling: ", df)
    print(dfs[df])
    alphaVal = 0.2
    if df == "original":
        alphaVal = 0.01
    plt.fill_between("intervalindex", -1, "aandeel", data=dfs[df], alpha=alphaVal, color=pal[i])


fig.subplots_adjust(bottom=0.25)  # or whatever
plt.ylim(bottom=0)
plt.xlim(left=0)
plt.xticks(data.intervalindex[0::1], rotation=90, fontproperties=robotoRegularFont_ticks)
plt.yticks(fontproperties=robotoRegularFont_ticks)

ax.set_xticklabels(intervalNames)

plt.legend(prop=robotoRegularFont_legend)
ax.set_title("Angularity histogram", fontproperties=robotoRegularFont_title)

# plt.show()
fig = plt.gcf()
fig.set_size_inches(14/2.54, 10/2.54)
fig.savefig('hist_ang.pdf', dpi=100, transparent=True)

# plt.show()
