#    Copyright (C) 2020  Willem van Opstal
#    willemvanopstal@home.nl
#
#    This file is part of Hydropolator
#    'Safe depth contour generalisation for navigational charts'
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
#    Last modified: april 14th 2020


from ElevationDict import ElevationDict
from BendDetector import BendDetector
from Aggregator import Aggregator

import startin

from decimal import *
import math
import networkx as nx
from matplotlib import cm, colors, path
import matplotlib.pyplot as plt
import numpy as np
import os
from datetime import datetime
import shapefile
import bisect
import pickle
from tabulate import tabulate
from random import uniform
import subprocess
import colorama
colorama.init()


class Hydropolator:

    debugBool = False

    xMin = 10e20
    yMin = 10e20
    zMin = 10e20
    xMax = -10e20
    yMax = -10e20
    zMax = -10e20

    pointCount = 0
    pointQueue = []

    # triangulation = Delaunay_triangulation_2()
    triangulation = startin.DT()
    vertexCount = 0
    vertices = None
    vertexDict = ElevationDict()
    triangles = None
    insertions = []

    # Graph
    # trGraph = TriangleRegionGraph()
    graph = {'nodes': {}, 'edges': {}, 'shallowestNodes': set(), 'deepestNodes': set()}
    triangleInventory = dict()
    nrNodes = 0
    nrEdges = 0
    availableNodeIds = set()
    unfinishedDeep = set()
    unfinishedShallow = set()
    nodeQueue = set()

    # isobaths
    isoType = 'standard'
    standardSeries = [0, 1, 2, 5, 8, 10, 15, 20, 25, 30, 35, 40, 45, 50, 100, 200]
    meterSeries = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14,
                   15, 16, 17, 18, 19, 20, 25, 30, 35, 40, 45, 50, 100, 200]
    hdSeries = range(0, 100)
    # testingSeries = [0, 2, 4, 6, 8, 10, 12, 15, 20, 25, 30, 35, 40, 45, 50]
    # testingSeries = [float(value/2) for value in range(0, 100, 1)]
    testingSeries = [0, 2, 5, 8, 10, 15, 20, 28, 30, 35, 40, 45, 50]
    noaaSeries = [0, 1.8, 3.6, 5.4, 9.1, 18.2, 27.4, 36.5, 45.7, 54.8, 73]
    # testingSeries = [0, 5, 10, 15, 20, 25, 50]
    isobathValues = []
    regions = []
    triangleRegions = []
    triangleRegionDict = {}
    regionNodes = {}

    depare_areas = []
    statistics = {'iterations': 0,
                  'depare_areas': [],
                  'sharp_points': [],
                  'abs_change': [],
                  'min_change': [],
                  'iso_seg_lengths': [],
                  'iter_tracker': []}

    projectName = None
    initDate = None
    modifiedDate = None

    errors = []

    def __init__(self):
        self.license_header()
        return

    # ====================================== #
    #
    #   Miscellaneous
    #
    # ====================================== #

    def ___MISC___(self):
        # placeholder for Atom symbol-tree-view
        pass

    def now(self):
        return datetime.now().strftime("%Y%m%d_%H%M%S")

    def set_crs(self, epsgCode):

        self.epsg = epsgCode
        self.srsString = subprocess.check_output(
            'gdalsrsinfo -o wkt "EPSG:{}"'.format(self.epsg), shell=True)

    def license_header(self):

        self.msg('''
Hydropolator: 'Safe depth contour generalisation for navigational charts'
Copyright (C) 2020  Willem van Opstal    <willemvanopstal-a-home.nl>

This program comes with ABSOLUTELY NO WARRANTY.
This is free software, and you are welcome to redistribute it under
certain conditions; see the LICENSE file for details.\n''', 'misc')

    # def warranty(self):
    #     print()
    #
    # def conditions(self):
    #     print()

    # ====================================== #
    #
    #   Messaging / Notifications
    #
    # ====================================== #

    def ___MESSAGING___(self):
        # placeholder for Atom symbol-tree-view
        pass

    def msg(self, string, type):
        if type == 'warning':
            colColor = colorama.Fore.RED
        elif type == 'info':
            colColor = colorama.Fore.YELLOW  # + colorama.Style.DIM
        elif type == 'infoheader':
            colColor = colorama.Fore.YELLOW + colorama.Style.BRIGHT
        elif type == 'header':
            colColor = colorama.Fore.GREEN
        elif type == 'misc':
            colColor = colorama.Fore.BLUE

        print(colColor + string + colorama.Style.RESET_ALL)

    def debug(self, message):
        if self.debugBool:
            print(message)

    def print_errors(self):
        if len(self.errors):
            self.msg('\nErrors produced:', 'warning')
            for i, error in enumerate(self.errors):
                print(i, error)
        else:
            self.msg('No errors produced', 'info')

    def summarize_project(self):
        self.msg('> project summary', 'header')
        print('initialisation: {}'.format(self.initDate))
        print('modified: {}'.format(self.modifiedDate))
        print('pointCount: {}'.format(self.pointCount))
        print('bounds: {}'.format(self.bounds()))
        print('vertices: {}'.format(self.vertexCount))
        print('isoType: {}'.format(self.isoType))

    def print_graph(self):
        self.msg('\n======GRAPH======', 'header')
        self.msg('NODES', 'header')
        # print('\n======GRAPH======\nNODES')
        for nodeId in self.graph['nodes'].keys():
            # print(nodeId, self.graph['nodes'][nodeId])
            print('id: ', nodeId, 'interval: ', self.graph['nodes'][nodeId]['region'], 'triangles: ', len(self.graph['nodes'][nodeId]['triangles']), 'deepNeighbors: ', (self.graph['nodes'][nodeId]['deepNeighbors']), 'shallowNeighbors: ', (self.graph['nodes'][nodeId]['shallowNeighbors']), '\ncurrent: ',
                  len(self.graph['nodes'][nodeId]['currentQueue']), 'deep: ', len(
                      self.graph['nodes'][nodeId]['deepQueue']), 'shallow: ', len(self.graph['nodes'][nodeId]['shallowQueue']))
        self.msg('\nEDGES', 'header')
        for edgeId in self.graph['edges'].keys():
            print('id: ', edgeId, self.graph['edges'][edgeId]['edge'],
                  'value: ', self.graph['edges'][edgeId]['value'], 'closed: ', self.graph['edges'][edgeId]['closed'])
            # print(edgeId, self.graph['edges'][edgeId])

        self.msg('\nREGIONS', 'header')
        for region in self.regionNodes.keys():
            print(region, self.regionNodes[region])

    def make_multilayer_graph_pymnet(self):
        try:
            import pymnet
        except:
            return

        net = pymnet.MultiplexNetwork(couplings='categorical', fullyInterconnected=False)

        for edgeId in self.graph['edges'].keys():
            edge = self.graph['edges'][edgeId]['edge']
            shallowNode = edge[0]
            deepNode = edge[1]
            shallowValue = self.get_interval_from_node(shallowNode)
            deepValue = self.get_interval_from_node(deepNode)

            net[shallowNode, 'shallowValue'][deepNode, 'deepValue'] = 1

        fig = pymnet.draw(net, show=True, layerPadding=0.2)

    def make_multilayer_graph(self, interactive=False):
        G = nx.Graph()
        for edge in self.graph['edges'].keys():
            # print(edge)
            edgingNodes = self.graph['edges'][edge]['edge']
            # print(edge, edgingNodes)
            G.add_edge(edgingNodes[0], edgingNodes[1])

        cmap = cm.get_cmap('Spectral')
        norm = colors.Normalize(vmin=0, vmax=len(self.regions))

        nodelabels = {}
        colorLabels = []
        edgeColors = []
        for node in G.nodes():
            regionInterval = self.regions[int(self.graph['nodes'][node]['region'])]
            label = '{}-{}\n{}'.format(regionInterval[0], regionInterval[1], node)
            color = cmap(norm(int(self.graph['nodes'][node]['region'])))

            # print(self.graph['nodes'][node]['classification'])

            if self.graph['nodes'][node]['classification'] == 'peak':
                edgeColors.append('red')
            elif self.graph['nodes'][node]['classification'] == 'pit':
                edgeColors.append('blue')
            else:
                edgeColors.append(color)

            colorLabels.append(color)
            nodelabels[node] = label

        # pos = nx.kamada_kawai_layout(G)
        # top = nx.bipartite.sets(G)[0]
        # pos = nx.planar_layout(G)

        # newPos = {}
        # existingPos = dict()
        # for node, nodeData in G.nodes(data=True):
        #     # print(node)
        #     # print(self.get_interval_from_node(node))
        #     yPos = -1 * float(self.get_interval_from_node(node))
        #
        #     if yPos in existingPos:
        #         xPos = existingPos[yPos] + 1.0
        #     else:
        #         xPos = 0.0
        #     existingPos[yPos] = xPos
        #     newPos[node] = [xPos, yPos]

        edgePos = {}
        existingPos = {}
        edges = list(G.edges())
        # print('edges---', edges)

        curNode = edges[0][0]
        nodeQueue = [curNode]
        xPos, yPos = 0.0, -1*float(self.get_interval_from_node(curNode))
        existingPos[yPos] = xPos
        edgePos[curNode] = [xPos, yPos]

        while len(edges) > 0:

            found = False
            for edge in edges:
                # print(edge, nodeQueue)
                if edge[0] == nodeQueue[0]:
                    curNode = edge[1]
                    yPos = -1 * float(self.get_interval_from_node(curNode))
                    if yPos in existingPos:
                        xPos = existingPos[yPos] + 1.0
                    else:
                        xPos = 0.0
                    existingPos[yPos] = xPos
                    if curNode not in edgePos:
                        edgePos[curNode] = [xPos, yPos]
                    found = edge
                    nodeQueue.append(curNode)
                    break

                elif edge[1] == nodeQueue[0]:
                    curNode = edge[0]
                    yPos = -1 * float(self.get_interval_from_node(curNode))
                    if yPos in existingPos:
                        xPos = existingPos[yPos] + 1.0
                    else:
                        xPos = 0.0
                    existingPos[yPos] = xPos
                    if curNode not in edgePos:
                        edgePos[curNode] = [xPos, yPos]
                    found = edge
                    nodeQueue.append(curNode)
                    break

            if found is False:
                nodeQueue = nodeQueue[1:]
            else:
                edges.remove(edge)

        # print(pos)
        # print(newPos)
        # print(G.edges())
        # pos = newPos
        pos = edgePos
        nx.draw(G, pos, node_color=colorLabels, edgecolors=edgeColors,
                font_size=16, with_labels=False)
        # for p in pos:  # raise text positions
        #     pos[p][1] += 0.07
        nx.draw_networkx_labels(G, pos, nodelabels, font_size=6)
        # plt.show()

        regionGraphName = 'regiongraph_{}.pdf'.format(self.now())
        regionGraphFile = os.path.join(os.getcwd(), 'projects', self.projectName, regionGraphName)
        # plt.savefig(regionGraphFile)

        if interactive:

            yChanges = []

            accepted = False
            print("type 'y' if accepted")
            while not accepted:
                plt.cla()
                nx.draw(G, pos, node_color=colorLabels, edgecolors=edgeColors,
                        font_size=16, with_labels=False)
                nx.draw_networkx_labels(G, pos, nodelabels, font_size=6)

                plt.ion()
                plt.show()

                yChange = input('nodeId, yChange: ')

                if yChange == 'y':
                    accepted = True
                    break
                else:
                    # yChanges.append(yChange)
                    try:
                        if len(yChange.split(',')) == 2:
                            selNode, nodeChange = yChange.split(',')
                            pos[selNode] = [pos[selNode][0]+float(nodeChange), pos[selNode][1]]
                        else:
                            nodeChange = yChange.split(',')[-1]
                            for selNode in yChange.split(',')[:-1]:
                                pos[selNode] = [pos[selNode][0]+float(nodeChange), pos[selNode][1]]
                    except:
                        print('wrong input')
                        continue

            plt.cla()
            nx.draw(G, pos, node_color=colorLabels, edgecolors=edgeColors,
                    font_size=16, with_labels=False)
            nx.draw_networkx_labels(G, pos, nodelabels, font_size=6)
            plt.savefig(regionGraphFile)

            # for yChange in yChanges:
            #     print(yChange.split(','))

    def make_network_graph(self):
        G = nx.Graph()
        for edge in self.graph['edges'].keys():
            # print(edge)
            edgingNodes = self.graph['edges'][edge]['edge']
            # print(edge, edgingNodes)
            G.add_edge(edgingNodes[0], edgingNodes[1])

        cmap = cm.get_cmap('Spectral')
        norm = colors.Normalize(vmin=0, vmax=len(self.regions))

        nodelabels = {}
        colorLabels = []
        edgeColors = []
        for node in G.nodes():
            regionInterval = self.regions[int(self.graph['nodes'][node]['region'])]
            label = '{}-{}\n{}'.format(regionInterval[0], regionInterval[1], node)
            color = cmap(norm(int(self.graph['nodes'][node]['region'])))

            # print(self.graph['nodes'][node]['classification'])

            if self.graph['nodes'][node]['classification'] == 'peak':
                edgeColors.append('red')
            elif self.graph['nodes'][node]['classification'] == 'pit':
                edgeColors.append('blue')
            else:
                edgeColors.append(color)

            colorLabels.append(color)
            nodelabels[node] = label

        pos = nx.kamada_kawai_layout(G)
        # top = nx.bipartite.sets(G)[0]
        # pos = nx.planar_layout(G)
        print(pos)
        nx.draw(G, pos, node_color=colorLabels, edgecolors=edgeColors,
                font_size=16, with_labels=False)
        # for p in pos:  # raise text positions
        #     pos[p][1] += 0.07
        nx.draw_networkx_labels(G, pos, nodelabels, font_size=6)
        # plt.show()

        regionGraphName = 'regiongraph_{}.pdf'.format(self.now())
        regionGraphFile = os.path.join(os.getcwd(), 'projects', self.projectName, regionGraphName)
        plt.savefig(regionGraphFile)

    def print_peaks_pits(self):

        peaks = self.peaks
        pits = self.pits

        self.msg('\nPEAKS (minimum {} m2)'.format(peaks['threshold']), 'header')
        header = ['nodeId', 'closed', 'fullArea', 'bArea', 'conflict', 'contours']
        peakRows = []

        for peakId in peaks.keys():
            if peakId == 'threshold':
                continue
            peak = peaks[peakId]
            conflicting = False
            if peak['conflictBool'] == 1:
                conflicting = "\033[1;31m{}\033[0m".format(True)
            elif peak['conflictBool'] == 2:
                conflicting = "\033[1;31m{}\033[0m".format(True)

            contours = ','.join(peak['edges'])
            peakRows.append([peakId, peak['closed'], peak['fullArea'],
                             peak['boundaryArea'], conflicting, contours])

        print(tabulate(peakRows, headers=header))

        self.msg('\nPITS (minimum {} m2)'.format(pits['threshold']), 'header')
        pitRows = []

        for pitId in pits.keys():
            if pitId == 'threshold':
                continue
            pit = pits[pitId]
            conflicting = False
            if pit['conflictBool'] == 1:
                conflicting = "\033[1;31m{}\033[0m".format(True)
            elif pit['conflictBool'] == 2:
                conflicting = "\033[1;33m{}\033[0m".format(True)
            contours = ','.join(pit['edges'])
            pitRows.append([pitId, pit['closed'], pit['fullArea'],
                            pit['boundaryArea'], conflicting, contours])

        print(tabulate(pitRows, headers=header))

    # ====================================== #
    #
    #   Project Management
    #
    # ====================================== #

    def ___PROJECT___(self):
        # placeholder for Atom symbol-tree-view
        pass

    def init_project(self, projectName):
        cwd = os.getcwd()
        projectDir = os.path.join(cwd, 'projects', projectName)
        print('project directory: ', projectDir)

        if not os.path.exists(projectDir):
            os.mkdir(projectDir)
            self.projectName = projectName
            self.initDate = self.now()
            self.modifiedDate = self.now()
            # self.write_metafile()
            return '> new project created'
        else:
            return '> project already exists, choose another name or load the project with -project'

    def load_project(self, projectName):
        cwd = os.getcwd()
        projectDir = os.path.join(cwd, 'projects', projectName)
        print('project directory: ', projectDir)

        if os.path.exists(projectDir):
            self.projectName = projectName
            self.load_metafile()
            self.generate_regions()
            self.load_triangulation()
            # self.load_trGraph()
            return True
        else:
            print('> project does not exist, load another or initialise a new project with -init')

    def write_metafile(self):
        self.msg('> writing metafile...', 'info')
        self.summarize_project()
        metaFile = os.path.join(os.getcwd(), 'projects', self.projectName, 'metafile')
        with open(metaFile, 'w') as mf:
            mf.write('projectName\t{}\n'.format(self.projectName))
            mf.write('initialisation\t{}\n'.format(self.initDate))
            mf.write('modified\t{}\n'.format(self.modifiedDate))
            mf.write('pointCount\t{}\n'.format(self.pointCount))
            mf.write('bounds\t{}\n'.format(self.bounds()))
            mf.write('vertices\t{}\n'.format(self.vertexCount))
            mf.write('isoType\t{}\n'.format(self.isoType))
            mf.write('nrNodes\t{}\n'.format(self.nrNodes))
            mf.write('nrEdges\t{}\n'.format(self.nrEdges))
        self.msg('> metafile written to file', 'info')

    def load_metafile(self):
        self.msg('> loading metafile...', 'info')
        metaFile = os.path.join(os.getcwd(), 'projects', self.projectName, 'metafile')
        with open(metaFile) as mf:
            for line in mf.readlines():
                if line.split('\t')[0] == 'initialisation':
                    self.initDate = line.split('\t')[1].strip()
                elif line.split('\t')[0] == 'projectName':
                    self.projectName = line.split('\t')[1].strip()
                elif line.split('\t')[0] == 'modified':
                    self.modifiedDate = line.split('\t')[1].strip()
                elif line.split('\t')[0] == 'pointCount':
                    self.pointCount = int(line.split('\t')[1])
                # elif line.split('\t')[0] == 'nrNodes':
                #     self.nrNodes = int(line.split('\t')[1])
                # elif line.split('\t')[0] == 'nrEdges':
                #     self.nrEdges = int(line.split('\t')[1])
                elif line.split('\t')[0] == 'vertices':
                    self.vertexCount = int(line.split('\t')[1].strip())
                elif line.split('\t')[0] == 'isoType':
                    self.isoType = line.split('\t')[1].strip()
                elif line.split('\t')[0] == 'bounds':
                    self.xMin, self.xMax, self.yMin, self.yMax, self.zMin, self.zMax = self.parse_bounds(line.split('\t')[
                        1])
        self.msg('> metafile loaded from file', 'info')

    def save_trGraph(self):
        self.msg('> saving triangle region graph...', 'info')
        graphFile = os.path.join(os.getcwd(), 'projects', self.projectName, 'triangleRegionGraph')

        with open(graphFile, 'wb') as gf:
            pickle.dump(self.graph, gf, protocol=pickle.HIGHEST_PROTOCOL)

        self.msg('> triangle region graph saved to file', 'info')

    def load_trGraph(self):
        self.msg('> loading triangle region graph...', 'info')
        graphFile = os.path.join(os.getcwd(), 'projects', self.projectName, 'triangleRegionGraph')

        with open(graphFile, 'rb') as gf:
            self.graph = pickle.load(gf)
        self.msg('> loaded triangle region graph', 'info')

    def save_triangulation(self):
        self.msg('> saving triangulation to file...', 'info')
        triFile = os.path.join(os.getcwd(), 'projects', self.projectName, 'triangulationVertices')
        trackerFile = os.path.join(os.getcwd(), 'projects',
                                   self.projectName, 'triangulationTracker')
        elevationFile = os.path.join(os.getcwd(), 'projects', self.projectName, 'vertexElevations')

        with open(triFile, 'w') as tf:
            for vertex in self.vertices[1:]:
                tf.write('{};{};{}\n'.format(vertex[0], vertex[1], vertex[2]))
        with open(trackerFile, 'w') as trf:
            trf.write('totalVertices\t{}\n'.format(self.vertexCount))
            for insertion in self.insertions:
                trf.write('{}\n'.format(insertion))
        with open(elevationFile, 'wb') as ef:
            pickle.dump(self.vertexDict, ef, protocol=pickle.HIGHEST_PROTOCOL)

        self.msg('> triangulation saved to file', 'info')

    def load_triangulation(self):
        self.msg('> loading triangulation from file...', 'info')
        triFile = os.path.join(os.getcwd(), 'projects', self.projectName, 'triangulationVertices')
        trackerFile = os.path.join(os.getcwd(), 'projects',
                                   self.projectName, 'triangulationTracker')
        elevationFile = os.path.join(os.getcwd(), 'projects', self.projectName, 'vertexElevations')

        tempInsertions = []
        with open(trackerFile) as trf:
            for line in trf.readlines()[1:]:
                tempInsertions.append(int(line))
        print('tempInsertions: ', tempInsertions)

        with open(triFile) as tf:
            insertionTracker = 0
            for insertion in tempInsertions:
                for line in tf.readlines()[insertionTracker:insertion]:
                    point = [float(value) for value in line.split(';')]
                    self.pointQueue.append(point)
                self.triangulation_insert()
                insertionTracker = insertion

        with open(elevationFile, 'rb') as ef:
            self.vertexDict = pickle.load(ef)
        self.msg('> triangulation loaded', 'info')

    def bounds(self):
        return [self.xMin, self.xMax, self.yMin, self.yMax, self.zMin, self.zMax]

    def parse_bounds(self, boundsString):
        boundsList = boundsString.strip().strip('[').strip(']').split(',')
        boundsListFloat = [float(value) for value in boundsList]
        return boundsListFloat

    def clean_files(self, minutes):
        currentTime = datetime.now()
        projectDir = os.path.join(os.getcwd(), 'projects', self.projectName)
        print(projectDir)

        filesToKeep = ['metafile', 'triangulationTracker',
                       'triangulationVertices', 'vertexElevations', 'triangleRegionGraph', '.DS_Store']
        filesToRemove = []
        for file in os.listdir(projectDir):
            if file not in filesToKeep:
                # print(file)
                dateIndicationList = file.split('.')[0].split('_')
                dateIndication = dateIndicationList[-2] + '_' + dateIndicationList[-1]
                datetimeObject = datetime.strptime(dateIndication, '%Y%m%d_%H%M%S')
                minutesDiff = (currentTime - datetimeObject).total_seconds() / 60.0

                # print(datetimeObject, currentTime, minutesDiff)
                if minutesDiff > minutes:
                    self.msg('> file: {}'.format(file), 'warning')
                    filePath = os.path.join(projectDir, file)
                    # os.remove(filePath)
                    filesToRemove.append(filePath)

        if len(filesToRemove):
            self.msg('Are you sure to remove these files?', 'warning')
            confirmation = input('Y/n')
            if confirmation == 'Y':
                for filePath in filesToRemove:
                    os.remove(filePath)
                self.msg('> {} files removed'.format(len(filesToRemove)), 'header')
            else:
                self.msg('> No files removed', 'header')
        else:
            self.msg('> No files removed', 'header')

    # ====================================== #
    #
    #   Exporting
    #
    # ====================================== #

    def ___EXPORTING___(self):
        # placeholder for Atom symbol-tree-view
        pass

    def export_triangles(self, triangleList, shpName):
        triangleShpName = 'triangles_{}_{}.shp'.format(shpName, self.now())
        triangleShpFile = os.path.join(os.getcwd(), 'projects', self.projectName, triangleShpName)
        print('triangles file: ', triangleShpFile)

        with shapefile.Writer(triangleShpFile) as wt:
            wt.field('min_depth', 'F', decimal=4)
            wt.field('max_depth', 'F', decimal=4)
            wt.field('avg_depth', 'F', decimal=4)
            for triangle in triangleList:
                geom, min, max, avg = self.polystats_from_triangle(triangle)
                # wt.poly(self.poly_from_triangle(triangle))
                # min, max, avg = 10, 10, 10  # self.minmaxavg_from_triangle(triangle)
                wt.poly([geom])
                wt.record(min, max, avg)
            self.msg('> triangles written to shapefile', 'info')

        if self.epsg:
            prjFile = triangleShpFile[:-4] + '.prj'
            with open(prjFile, 'wb') as pf:
                pf.write(self.srsString)

    def export_points(self, pointList, shpName):
        pointShpName = 'points_{}_{}.shp'.format(shpName, self.now())
        pointShpFile = os.path.join(os.getcwd(), 'projects', self.projectName, pointShpName)
        print('points file: ', pointShpFile)

        with shapefile.Writer(pointShpFile) as wp:
            # wp.field('depth', 'F', decimal=4)
            wp.field('id', 'N')
            # for point in self.triangulation.all_vertices()[1:]:
            for i, point in enumerate(pointList):  # remove the infinite vertex in startTIN
                # actualZ = self.get_z(point, idOnly=False)
                wp.point(point[0], point[1])
                wp.record(i)
            self.msg('> points written to shapefile', 'info')

        if self.epsg:
            prjFile = pointShpFile[:-4] + '.prj'
            with open(prjFile, 'wb') as pf:
                pf.write(self.srsString)

    def export_shapefile(self, shpName):
        self.msg('> exporting shapefiles...', 'info')
        pointShpName = 'points_{}_{}.shp'.format(shpName, self.now())
        triangleShpName = 'triangles_{}_{}.shp'.format(shpName, self.now())
        pointShpFile = os.path.join(os.getcwd(), 'projects', self.projectName, pointShpName)
        triangleShpFile = os.path.join(os.getcwd(), 'projects', self.projectName, triangleShpName)
        print('triangles file: ', triangleShpFile)
        print('points file: ', pointShpFile)

        with shapefile.Writer(pointShpFile) as wp:
            wp.field('depth', 'F', decimal=4)
            wp.field('id', 'N')
            wp.field('diff', 'F', decimal=4)
            wp.field('updates', 'N')
            # for point in self.triangulation.all_vertices()[1:]:
            for i, point in enumerate(self.vertices[1:]):  # remove the infinite vertex in startTIN
                actualZ = self.get_z(point, idOnly=False)
                nrUpdates = self.get_updates(point, idOnly=False)
                wp.point(point[0], point[1])
                wp.record(point[2], i, point[2]-actualZ, nrUpdates)
            self.msg('> points written to shapefile', 'info')

        if self.epsg:
            prjFile = pointShpFile[:-4] + '.prj'
            with open(prjFile, 'wb') as pf:
                pf.write(self.srsString)

        with shapefile.Writer(triangleShpFile) as wt:
            wt.field('min_depth', 'F', decimal=4)
            wt.field('max_depth', 'F', decimal=4)
            wt.field('avg_depth', 'F', decimal=4)
            for triangle in self.triangles:
                geom, min, max, avg = self.polystats_from_triangle(triangle)
                # wt.poly(self.poly_from_triangle(triangle))
                # min, max, avg = 10, 10, 10  # self.minmaxavg_from_triangle(triangle)
                wt.poly([geom])
                wt.record(min, max, avg)
            self.msg('> triangles written to shapefile', 'info')

        if self.epsg:
            prjFile = triangleShpFile[:-4] + '.prj'
            with open(prjFile, 'wb') as pf:
                pf.write(self.srsString)

    def export_region_triangles(self):
        self.msg('> exporting region triangles...', 'info')
        triangleShpName = 'region_triangles_{}.shp'.format(self.now())
        triangleShpFile = os.path.join(os.getcwd(), 'projects', self.projectName, triangleShpName)
        print('region triangles file: ', triangleShpFile)

        with shapefile.Writer(triangleShpFile) as wt:
            wt.field('region', 'N')
            for i, region in enumerate(self.triangleRegions):
                if len(region):
                    geom = []
                    for triangle in region:
                        geom.append(self.poly_from_triangle(triangle))
                    wt.poly(geom)
                    wt.record(i)

        if self.epsg:
            prjFile = triangleShpFile[:-4] + '.prj'
            with open(prjFile, 'wb') as pf:
                pf.write(self.srsString)

        self.msg('> region triangles saved to file', 'info')

    def export_all_node_triangles(self):
        self.msg('> saving all node triangles...', 'info')
        nodeList = []
        for node in self.graph['nodes'].keys():
            nodeList.append(node)
        self.export_node_triangles(nodeList)
        self.msg('> all node triangles saved', 'info')

    def export_node_triangles(self, nodeIds):
        self.msg('> saving selected region triangles...', 'info')
        triangleShpName = 'node_triangles_{}.shp'.format(self.now())
        triangleShpFile = os.path.join(os.getcwd(), 'projects', self.projectName, triangleShpName)
        print('selected node triangles file: ', triangleShpFile)

        with shapefile.Writer(triangleShpFile) as wt:
            wt.field('node', 'N')
            wt.field('region', 'N')
            wt.field('interval', 'C')
            wt.field('shallowNbs', 'C')
            wt.field('deepNbs', 'C')
            wt.field('full_area', 'F', decimal=3)
            wt.field('boundary_area', 'F', decimal=3)
            wt.field('classification', 'C')
            for node in nodeIds:
                geom = []
                for triangle in self.graph['nodes'][node]['triangles']:
                    geom.append(self.poly_from_triangle(list(triangle)))

                region = self.get_interval_from_node(node)
                interval = str(self.regions[region])
                shallowNeighbors = str(self.get_neighboring_nodes(node, 'shallow'))
                deepNeighbors = str(self.get_neighboring_nodes(node, 'deep'))
                nodeArea = self.graph['nodes'][node]['full_area']
                bArea = self.graph['nodes'][node]['boundary_area']
                classification = self.graph['nodes'][node]['classification']

                wt.poly(geom)
                wt.record(int(node), region, interval, shallowNeighbors,
                          deepNeighbors, nodeArea, bArea, classification)

        if self.epsg:
            prjFile = triangleShpFile[:-4] + '.prj'
            with open(prjFile, 'wb') as pf:
                pf.write(self.srsString)

        self.msg('> selected node triangles saved', 'info')

    def export_all_edge_triangles(self):
        self.msg('> saving all edge triangles...', 'info')
        triangleShpName = 'edge_triangles_{}.shp'.format(self.now())
        triangleShpFile = os.path.join(os.getcwd(), 'projects', self.projectName, triangleShpName)
        print('edge triangles file: ', triangleShpFile)

        with shapefile.Writer(triangleShpFile) as wt:
            wt.field('value', 'F', decimal=4)
            wt.field('id', 'N')
            for edgeId in self.graph['edges'].keys():
                geom = []
                for triangle in self.get_edge_triangles(edgeId):
                    geom.append(self.poly_from_triangle(triangle))
                wt.poly(geom)
                isoValue = self.get_edge_value(edgeId)
                wt.record(isoValue, int(edgeId))

        if self.epsg:
            prjFile = triangleShpFile[:-4] + '.prj'
            with open(prjFile, 'wb') as pf:
                pf.write(self.srsString)

        self.msg('> edge triangles saved', 'info')

    def export_all_isobaths(self):
        self.msg('> saving all isobaths...', 'info')
        lineShpName = 'isobaths_{}.shp'.format(self.now())
        lineShpFile = os.path.join(os.getcwd(), 'projects', self.projectName, lineShpName)
        print('isobaths file: ', lineShpFile)

        with shapefile.Writer(lineShpFile) as wt:
            wt.field('value', 'F', decimal=4)
            wt.field('id', 'N')
            wt.field('shallowNode', 'N')
            wt.field('deepNode', 'N')
            wt.field('iso_area', 'F', decimal=3)
            wt.field('classification', 'C')
            for edgeId in self.graph['edges'].keys():
                # geom = [[list(value) for value in self.graph['edges'][edgeId]['geom']]]
                geom = self.graph['edges'][edgeId]['geom']
                isoArea = self.graph['edges'][edgeId]['iso_area']
                shallowNode = self.graph['edges'][edgeId]['edge'][0]
                deepNode = self.graph['edges'][edgeId]['edge'][1]
                classification = ''
                if 'classification' in self.graph['edges'][edgeId]:
                    classification = self.graph['edges'][edgeId]['classification']
                # print(geom)
                # geom = []
                # print(self.graph['edges'][edgeId]['geom'])
                # for coords in self.graph['edges'][edgeId]['geom'].coords:
                #     # print(coords)
                #     geom.append(list(coords))
                # for triangle in self.get_edge_triangles(edgeId):
                #     geom.append(self.poly_from_triangle(triangle))
                wt.line([geom])
                isoValue = self.graph['edges'][edgeId]['value']
                wt.record(isoValue, int(edgeId), int(shallowNode),
                          int(deepNode), isoArea, classification)

        if self.epsg:
            prjFile = lineShpFile[:-4] + '.prj'
            with open(prjFile, 'wb') as pf:
                pf.write(self.srsString)

        self.msg('> isobaths saved', 'info')

    def export_all_angularities(self):
        pointShpName = 'angularities_{}.shp'.format(self.now())
        pointShpFile = os.path.join(os.getcwd(), 'projects', self.projectName, pointShpName)
        # print('invalid/missing isobathsegmentsPoints file: ', pointShpFile)

        with shapefile.Writer(pointShpFile) as wp:
            wp.field('angle', 'F', decimal=4)
            # wp.field('id', 'N')
            # wp.field('segment', 'C')
            # for point in self.triangulation.all_vertices()[1:]:
            for edge in self.graph['edges'].keys():
                # closed = self.graph['edges'][str(edge)]['closed']
                geom = self.graph['edges'][str(edge)]['geom']
                pointAngularities = self.graph['edges'][str(edge)]['point_angularities']

                for i in range(len(pointAngularities)):
                    point = geom[i]
                    wp.point(point[0], point[1])
                    wp.record(pointAngularities[i])

        if self.epsg:
            prjFile = pointShpFile[:-4] + '.prj'
            with open(prjFile, 'wb') as pf:
                pf.write(self.srsString)

    def export_depth_areas(self, nodeIds=[]):
        if nodeIds == []:
            nodeIds = self.graph['nodes'].keys()

        self.msg('> saving depth areas...', 'info')
        depareName = 'DEPARE_{}.shp'.format(self.now())
        depareFile = os.path.join(os.getcwd(), 'projects', self.projectName, depareName)
        print('depth areas file: ', depareFile)

        with shapefile.Writer(depareFile) as wt:
            wt.field('node', 'N')
            wt.field('region', 'N')
            wt.field('interval', 'C')
            wt.field('dep_min', 'F', decimal=3)
            wt.field('dep_max', 'F', decimal=3)

            for nodeId in nodeIds:

                node = self.graph['nodes'][nodeId]
                if not node['outer_boundary']:
                    continue

                region = self.get_interval_from_node(nodeId)
                interval = self.regions[region]

                geom = []

                # print(nodeId, node['outer_boundary'], node['holes'])

                boundaryEdge = self.graph['edges'][node['outer_boundary']]['edge']
                # print(boundaryEdge, boundaryEdge.index(nodeId))

                # check if the current node is deeper side or shallower side of the isobath
                if boundaryEdge.index(nodeId) == 1:
                    # ccw, so reverse
                    geom.append(list(reversed(self.graph['edges'][node['outer_boundary']]['geom'])))
                else:
                    # already clockwise
                    geom.append(self.graph['edges'][node['outer_boundary']]['geom'])

                for holeId in node['holes']:
                    holeEdge = self.graph['edges'][holeId]['edge']
                    if holeEdge.index(nodeId) == 0:
                        # already ccw
                        geom.append(self.graph['edges'][holeId]['geom'])
                    else:
                        geom.append(list(reversed(self.graph['edges'][holeId]['geom'])))

                wt.poly(geom)
                wt.record(int(nodeId), region, str(interval), interval[0], interval[1])

        if self.epsg:
            prjFile = depareFile[:-4] + '.prj'
            with open(prjFile, 'wb') as pf:
                pf.write(self.srsString)

        self.msg('> depth areas saved', 'info')

    def export_spur_gully_geoms(self, geom_summary):

        self.msg('> exporting spur gully triangles...', 'info')
        triangleShpName = 'spur_gully_triangles_{}.shp'.format(self.now())
        triangleShpFile = os.path.join(os.getcwd(), 'projects', self.projectName, triangleShpName)
        print('spur gully triangles file: ', triangleShpFile)

        with shapefile.Writer(triangleShpFile) as wt:
            wt.field('edgeId', 'N')
            wt.field('type', 'C')

            for edgeCollection in geom_summary:
                edgeId = int(edgeCollection[0])
                for spurPolygon in edgeCollection[1]:
                    polyType = 'spur'
                    # print(spurPolygon)

                    wt.poly(spurPolygon)
                    wt.record(edgeId, polyType)

                for gullyPolygon in edgeCollection[2]:
                    polyType = 'gully'
                    # print(spurPolygon)

                    wt.poly(gullyPolygon)
                    wt.record(edgeId, polyType)

                # print(edgeCollection[0])
                # print('spur geom: ', edgeCollection[1])

            # wt.field('region', 'N')
            # for i, region in enumerate(self.triangleRegions):
            #     if len(region):
            #         geom = []
            #         for triangle in region:
            #             geom.append(self.poly_from_triangle(triangle))
            #         wt.poly(geom)
            #         wt.record(i)

        if self.epsg:
            prjFile = triangleShpFile[:-4] + '.prj'
            with open(prjFile, 'wb') as pf:
                pf.write(self.srsString)

        self.msg('> spur gully triangles saved to file', 'info')

    def rasterize(self, resolution=100.0):
        self.msg('rasterizing..', 'header')

        rasterName = 'rasterized_{}_{}.tif'.format(resolution, self.now())
        rasterFile = os.path.join(os.getcwd(), 'projects', self.projectName, rasterName)
        tempFile = os.path.join(os.getcwd(), 'projects', self.projectName, rasterName+'.xyz')
        print('rasterfile: ', rasterFile)
        print('resolution: ', resolution)

        print(self.xMin, self.xMax)
        print(self.yMin, self.yMax)

        xStart = round(self.xMin + 0.5*resolution, 3)
        yStart = round(self.yMin + 0.5*resolution, 3)
        xCurrent, yCurrent = xStart, yStart

        nanValue = 1e6

        points = {}
        tempFileOut = open(tempFile, 'w')
        while yCurrent < self.yMax:

            xCurrent = xStart
            while xCurrent < self.xMax:

                # print('point ', xCurrent, yCurrent)
                pointLoc = (xCurrent, yCurrent)
                try:
                    pointValue = round(
                        self.triangulation.interpolate_laplace(xCurrent, yCurrent), 2)
                    # print(pointValue)
                    points[pointLoc] = pointValue
                    tempFileOut.write('{} {} {}\n'.format(xCurrent, yCurrent, pointValue))
                except:
                    # print('outside convex hull')
                    tempFileOut.write('{} {} {}\n'.format(xCurrent, yCurrent, nanValue))
                    pass

                xCurrent = round(xCurrent + resolution, 3)

            yCurrent = round(yCurrent + resolution, 3)

        tempFileOut.close()

        srs = 'EPSG:{}'.format(self.epsg)

        FNULL = open(os.devnull, 'w')
        runCommand = 'gdal_translate -a_srs {} -a_nodata {} -mo BAND_1=ELEVATION {} {}'.format(
            srs, nanValue, tempFile, rasterFile)
        # print(runCommand)
        subprocess.run(runCommand, shell=True)  # , stdout=FNULL)
        os.remove(tempFile)

    # ====================================== #
    #
    #   Point Functions
    #
    # ====================================== #

    def ___POINTS___(self):
        # placeholder for Atom symbol-tree-view
        pass

    def load_pointfile(self, pointFile, fileType, delimiter, xName='x', yName='y', dName='depth', flip=False):
        pointFilePath = os.path.normpath(os.path.join(os.getcwd(), pointFile))
        print(pointFilePath)

        if fileType == 'csv':

            with open(pointFile) as fi:

                lineNumber = 0
                for line in fi.readlines():
                    if line.startswith('\"SEP') or line.startswith('SEP'):
                        print('skipping excel separator')
                        continue
                    if lineNumber == 0:
                        headerRow = [val.strip() for val in line.split(delimiter)]
                        xPlace = headerRow.index(xName)
                        yPlace = headerRow.index(yName)
                        dPlace = headerRow.index(dName)
                        lineNumber += 1
                        continue

                    point = line.split(delimiter)

                    xValue = float(point[xPlace])
                    yValue = float(point[yPlace])
                    # randomize uniform
                    min, max = -2.4, 2.4
                    xValue = round(xValue + uniform(min, max), 3)
                    yValue = round(yValue + uniform(min, max), 3)

                    depthValue = float(point[dPlace])
                    # # offset
                    # depthValue = depthValue - 18
                    # # randomize
                    # depthValue

                    if flip:
                        point = [xValue, yValue, round(-1*depthValue, 4)]
                    elif not flip:
                        point = [xValue, yValue, round(depthValue, 4)]

                    # print(point)

                    self.check_minmax(point)
                    self.pointQueue.append(point)
                    self.pointCount += 1

        elif fileType == 'shapefile':
            print('> ShapeFile not supported yet.')

        self.triangulation_insert()

        self.modifiedDate = self.now()
        self.write_metafile()

    def load_pointfile_old(self, pointFile, fileType, delimiter, flip=False):
        pointFilePath = os.path.normpath(os.path.join(os.getcwd(), pointFile))
        print(pointFilePath)

        if fileType == 'csv':
            with open(pointFile) as fi:
                for line in fi.readlines():
                    point = line.split(delimiter)
                    if flip:
                        point = [float(point[0]), float(point[1]), round(-1*float(point[2])+18, 4)]
                    elif not flip:
                        point = [float(point[0]), float(point[1]), round(float(point[2])+18, 4)]

                    # print(point)

                    # if point[0] < 238 or point[0] > 380:
                    #     continue
                    # if point[1] < 110 or point[1] > 193:
                    #     continue

                    self.check_minmax(point)
                    self.pointQueue.append(point)
                    self.pointCount += 1

        elif fileType == 'shapefile':
            print('> ShapeFile not supported yet.')

        self.triangulation_insert()

        self.modifiedDate = self.now()
        self.write_metafile()

    def check_minmax(self, pointTuple):
        if pointTuple[0] > self.xMax:
            self.xMax = pointTuple[0]
        if pointTuple[0] < self.xMin:
            self.xMin = pointTuple[0]
        if pointTuple[1] > self.yMax:
            self.yMax = pointTuple[1]
        if pointTuple[1] < self.yMin:
            self.yMin = pointTuple[1]
        if pointTuple[2] > self.zMax:
            self.zMax = pointTuple[2]
        if pointTuple[2] < self.zMin:
            self.zMin = pointTuple[2]

    # ====================================== #
    #
    #   Triangle Functions
    #
    # ====================================== #

    def ___TRIANGLE___(self):
        # placeholder for Atom symbol-tree-view
        pass

    def poly_from_triangle(self, vertex_list):
        # vertices = self.triangulation.all_vertices()
        # vertices = self.vertices
        triPoly = []
        for vId in vertex_list:
            # triPoly.append([vertices[vId][0], vertices[vId][1]])
            triPoly.append([self.triangulation.get_point(vId)[0],
                            self.triangulation.get_point(vId)[1]])
        triPoly.append([self.triangulation.get_point(vertex_list[0])[0],
                        self.triangulation.get_point(vertex_list[0])[1]])
        return triPoly

    def polystats_from_triangle(self, vertex_list):
        # vertices = self.triangulation.all_vertices()
        triPoly = []
        elevations = []
        for vId in vertex_list:
            vertex = self.triangulation.get_point(vId)
            triPoly.append([vertex[0], vertex[1]])
            # elevations.append(vertex[2])
            elevations.append(self.get_z(vertex))
        triPoly.append([self.triangulation.get_point(vertex_list[0])[0],
                        self.triangulation.get_point(vertex_list[0])[1]])

        return triPoly, min(elevations), max(elevations), sum(elevations) / 3

    def minmaxavg_from_triangle(self, vertex_list):
        # vertices = self.triangulation.all_vertices()
        # vertices = self.vertices
        elevations = []
        for vId in vertex_list:
            elevations.append(self.get_z(self.triangulation.get_point(vId)))
        return min(elevations), max(elevations), sum(elevations) / 3

    def minmax_from_triangle(self, vertex_list):
        # vertices = self.triangulation.all_vertices()
        # vertices = self.vertices
        elevations = []
        for vId in vertex_list:
            elevations.append(self.get_z(self.triangulation.get_point(vId)))
            # elevations.append(self.triangulation.get_point(vId)[2])
            # vertex = self.triangulation.get_point(vId)
            # print('--')
            # print(vertex[2], self.vertexDict[tuple(vertex)]['z'])
        return min(elevations), max(elevations)

    def previous_minmax_from_triangle(self, vertex_list):
        # vertices = self.triangulation.all_vertices()
        # vertices = self.vertices
        elevations = []
        for vId in vertex_list:
            elevations.append(self.get_previous_z(self.triangulation.get_point(vId)))
            # elevations.append(self.triangulation.get_point(vId)[2])
            # vertex = self.triangulation.get_point(vId)
            # print('--')
            # print(vertex[2], self.vertexDict[tuple(vertex)]['z'])
        return min(elevations), max(elevations)

    def find_intervals(self, triangle, indexOnly=True):
        min, max = self.minmax_from_triangle(triangle)
        intervals = []
        for index in range(bisect.bisect_left(self.isobathValues, min), bisect.bisect_left(self.isobathValues, max) + 1):
            if indexOnly:
                intervals.append(index)
            else:
                intervals.append(self.regions[index])
        if indexOnly:
            return intervals
        else:
            return intervals

    def find_previous_intervals(self, triangle, indexOnly=True):
        min, max = self.previous_minmax_from_triangle(triangle)
        intervals = []
        for index in range(bisect.bisect_left(self.isobathValues, min), bisect.bisect_left(self.isobathValues, max) + 1):
            if indexOnly:
                intervals.append(index)
            else:
                intervals.append(self.regions[index])
        if indexOnly:
            return intervals
        else:
            return intervals

    def pseudo_triangle(self, triangle):
        # rotates the triangle_list so the smallest index is in front
        # so we can easily compare and not store duplicates
        n = triangle.index(min(triangle))
        if not n:
            return triangle
        else:
            return triangle[n:] + triangle[:n]

    # ====================================== #
    #
    #   Vertex Functions
    #
    # ====================================== #

    def ___VERTEX___(self):
        # placeholder for Atom symbol-tree-view
        pass

    def get_z(self, vertex, idOnly=False):
        # return self.vertexDict[tuple(vertex)]['z']
        if not idOnly:
            return self.vertexDict.get_z(vertex)
        else:
            parsedVertex = self.triangulation.get_point(vertex)
            return self.vertexDict.get_z(parsedVertex)

    def get_updates(self, vertex, idOnly=False):
        # return self.vertexDict[tuple(vertex)]['z']
        if not idOnly:
            return self.vertexDict.get_updates(vertex)
        else:
            parsedVertex = self.triangulation.get_point(vertex)
            return self.vertexDict.get_updates(parsedVertex)

    def get_original_z(self, vertex, idOnly=False):
        # return self.vertexDict[tuple(vertex)]['z']
        if not idOnly:
            return self.vertexDict.get_original_z(vertex)
        else:
            parsedVertex = self.triangulation.get_point(vertex)
            return self.vertexDict.get_original_z(parsedVertex)

    def get_previous_z(self, vertex, idOnly=False):
        # return self.vertexDict[tuple(vertex)]['z']
        if not idOnly:
            return self.vertexDict.get_previous_z(vertex)
        else:
            parsedVertex = self.triangulation.get_point(vertex)
            return self.vertexDict.get_previous_z(parsedVertex)

    def get_queued_z(self, vertex, idOnly=False):
        # return self.vertexDict[tuple(vertex)]['z']
        if not idOnly:
            return self.vertexDict.get_queued_z(vertex)
        else:
            parsedVertex = self.triangulation.get_point(vertex)
            return self.vertexDict.get_queued_z(parsedVertex)

    def add_vertex_to_queue(self, vertex, new_z, idOnly=False):
        # return self.vertexDict[tuple(vertex)]['z']
        if not idOnly:
            self.vertexDict.add_to_queue(vertex, new_z)
        else:
            parsedVertex = self.triangulation.get_point(vertex)
            self.vertexDict.add_to_queue(parsedVertex, new_z)

    # ====================================== #
    #
    #   Triangulation
    #
    # ====================================== #

    def ___TRIANGULATION___(self):
        # placeholder for Atom symbol-tree-view
        pass

    def triangulation_insert(self):
        prevVertexCount = self.triangulation.number_of_vertices()
        self.triangulation.insert(self.pointQueue)
        # print('pqueue: ', len(self.pointQueue))
        # print('nrvertices: ', self.triangulation.number_of_vertices())
        # print('metaVertexCount: ', prevVertexCount)
        # print('triangulated inserts: ', self.triangulation.number_of_vertices() - self.vertexCount)
        self.insertions.append(self.triangulation.number_of_vertices() - prevVertexCount)
        self.vertexCount = self.triangulation.number_of_vertices()
        self.vertices = self.triangulation.all_vertices()
        self.triangles = self.triangulation.all_triangles()

        for vertex in self.vertices:
            self.vertexDict.add_new(vertex)

        self.pointQueue = []
        print('new insertionslist: ', self.insertions)

    def adjacent_triangles(self, triangle):
        adjacentTriangles = []
        addedVertices = []

        incidentTriangles = set()
        for vId in triangle:
            for incidentTriangle in self.triangulation.incident_triangles_to_vertex(vId):
                incidentTriangles.add(tuple(self.pseudo_triangle(incidentTriangle)))

        for incidTriangle in incidentTriangles:
            if len(set(triangle).intersection(incidTriangle)) == 2:
                adjacentTriangles.append(incidTriangle)

        return adjacentTriangles

        # below is buggy, somewhere a mistake, sometimes only returning two adjacent triangles if it actually has three
        for vId in triangle:
            if len(addedVertices) == 3:
                break
            else:
                for incidentTriangle in self.triangulation.incident_triangles_to_vertex(vId):
                    if len(set(triangle).intersection(incidentTriangle)) == 2 and set(incidentTriangle).difference(triangle) not in addedVertices:
                        adjacentTriangles.append(tuple(self.pseudo_triangle(incidentTriangle)))
                        addedVertices.append(set(incidentTriangle).difference(triangle))

        return adjacentTriangles

    # ====================================== #
    #
    #   Triangle Region Graph
    #
    # ====================================== #

    def ___TRGRAPH___(self):
        # placeholder for Atom symbol-tree-view
        pass
    # --------------- #
    #   CREATION
    # --------------- #

    def generate_regions(self):
        self.msg('> generating regions-list from isoType...', 'info')
        # self.isoType = isobathSeries
        if self.isoType == 'standard':
            isobathValues = self.standardSeries
        elif self.isoType == 'meter':
            isobathValues = self.meterSeries
        elif self.isoType == 'hd':
            isobathValues = self.hdSeries
        elif self.isoType == 'testing':
            isobathValues = self.testingSeries
        elif self.isoType == 'noaa':
            isobathValues = self.noaaSeries

        regions = []
        regions.append([-1e9, isobathValues[0]])
        for i in range(len(isobathValues))[1:]:
            regions.append([isobathValues[i - 1], isobathValues[i]])
        regions.append([isobathValues[-1], 1e9])

        self.isobathValues = isobathValues
        # self.trGraph.isobathValues = isobathValues
        self.regions = regions
        # self.trGraph.regions = regions
        for i in range(len(regions)):
            self.triangleRegions.append([])
            self.triangleRegionDict[str(i)] = set()
            self.regionNodes[str(i)] = set()
        # self.trGraph.triangleRegions = self.triangleRegions

        # print(self.triangleRegions, regions, isobathValues)
        self.msg('> regions-list established', 'info')

    def add_triangle_to_interval_inventory(self, interval, triangle):
        triangle = tuple(self.pseudo_triangle(triangle))

        if triangle in self.triangleIntervalInventory:
            self.triangleIntervalInventory[triangle].add(interval)
        else:
            self.triangleIntervalInventory[triangle] = {interval}

    def is_triangle_already_indexed_in_interval(self, interval, triangle):
        triangle = tuple(self.pseudo_triangle(triangle))

        if triangle not in self.triangleIntervalInventory:
            return False

        if interval in self.triangleIntervalInventory[triangle]:
            return True
        else:
            return False

    def expand_current_node(self, currentNode, interval):

        currentQueue = self.get_queue(currentNode, 'current')
        deepNeighbors = self.get_neighboring_nodes(currentNode, 'deep')
        shallowNeighbors = self.get_neighboring_nodes(currentNode, 'shallow')

        # print('\nresolving current', currentNode)

        unresolved = True
        while unresolved:

            for triangle in currentQueue.copy():
                # print(currentNode, triangle)
                adjacentTriangles = self.adjacent_triangles(triangle)
                # print(adjacentTriangles)
                for neighbouringTriangle in adjacentTriangles:
                    if 0 not in neighbouringTriangle:
                        neighbouringIntervals = self.find_intervals(
                            neighbouringTriangle, indexOnly=True)

                        if (int(interval) in neighbouringIntervals and
                                not self.saddle_test(triangle, neighbouringTriangle, int(interval)) and
                                not self.is_triangle_already_indexed_in_interval(interval, neighbouringTriangle)):
                            self.add_triangle_to_node(neighbouringTriangle, currentNode)
                            self.add_triangle_to_interval_inventory(
                                interval, neighbouringTriangle)
                            self.add_triangle_to_queue(
                                neighbouringTriangle, currentNode, 'current')

                            for deepNeighbor in deepNeighbors:
                                self.remove_triangle_from_queue(
                                    neighbouringTriangle, deepNeighbor, 'shallow')
                            for shallowNeighbor in shallowNeighbors:
                                self.remove_triangle_from_queue(
                                    neighbouringTriangle, shallowNeighbor, 'deep')

                        if (int(interval) + 1 in neighbouringIntervals and
                                not self.is_triangle_already_indexed_in_interval(str(int(interval) + 1), neighbouringTriangle)):
                            # self.add_triangle_to_queue(
                            #     neighbouringTriangle, currentNode, 'deep')
                            alreadyInOtherShallowQueue = False
                            for deepNeighbor in deepNeighbors:
                                if self.triangle_in_queue(neighbouringTriangle, deepNeighbor, 'shallow'):
                                    alreadyInOtherShallowQueue = True
                                    self.remove_triangle_from_queue(
                                        neighbouringTriangle, deepNeighbor, 'shallow')
                            if not alreadyInOtherShallowQueue:
                                self.add_triangle_to_queue(
                                    neighbouringTriangle, currentNode, 'deep')

                        if (int(interval) - 1 in neighbouringIntervals and
                                not self.is_triangle_already_indexed_in_interval(str(int(interval) - 1), neighbouringTriangle)):
                            # self.add_triangle_to_queue(
                            #     neighbouringTriangle, currentNode, 'shallow')
                            alreadyInOtherDeepQueue = False
                            for shallowNeighbor in shallowNeighbors:
                                if self.triangle_in_queue(neighbouringTriangle, shallowNeighbor, 'deep'):
                                    alreadyInOtherDeepQueue = True
                                    self.remove_triangle_from_queue(
                                        neighbouringTriangle, shallowNeighbor, 'deep')
                            if not alreadyInOtherDeepQueue:
                                self.add_triangle_to_queue(
                                    neighbouringTriangle, currentNode, 'shallow')

                self.remove_triangle_from_queue(triangle, currentNode, 'current')

            if len(self.get_queue(currentNode, 'current')) == 0:
                # print('expanded the current queue, finished')
                unresolved = False

    def build_graph_new2(self):
        self.msg('> building new TRG...', 'info')

        self.triangleIntervalInventory = dict()

        # find a starting triangle, and for simplicity
        # make sure this only belongs to one interval
        for triangle in self.triangles:
            tri_intervals = self.find_intervals(triangle, indexOnly=True)
            if len(tri_intervals) == 1:
                triangle = tuple(self.pseudo_triangle(triangle))
                interval = str(tri_intervals[0])
                break

        currentNode = self.add_triangle_to_new_node(interval, triangle)
        self.add_triangle_to_interval_inventory(interval, triangle)
        self.add_triangle_to_queue(triangle, currentNode, 'current')
        currentQueue = {triangle}
        currentInterval = interval

        nodesToResolve = {currentNode}
        nodeToResolve = currentNode

        finished = False
        bgi = 0
        resolveCurrent = True
        while not finished:

            # if resolveCurrent:

            print('currentNode: ', currentNode, 'resolving node: ', nodeToResolve)
            self.expand_current_node(nodeToResolve, str(self.get_interval_from_node(nodeToResolve)))
            deepQueue = self.get_queue(currentNode, 'deep')
            shallowQueue = self.get_queue(currentNode, 'shallow')
            deeperInterval = str(int(currentInterval) + 1)
            shallowerInterval = str(int(currentInterval) - 1)
            print(currentNode, currentInterval, 'dq: ', len(deepQueue), 'sq: ', len(shallowQueue))

            # self.print_graph()

            if len(deepQueue) != 0:
                for triangle in deepQueue:
                    break
                if self.is_triangle_already_indexed_in_interval(deeperInterval, triangle):
                    self.remove_triangle_from_queue(triangle, currentNode, 'deep')
                    # print('ERROR DEEP')
                    continue

                deeperNode = self.add_triangle_to_new_node(deeperInterval, triangle)
                self.add_triangle_to_interval_inventory(deeperInterval, triangle)
                self.add_triangle_to_queue(triangle, deeperNode, 'current')
                nodesToResolve.add(deeperNode)
                self.remove_triangle_from_queue(triangle, currentNode, 'deep')
                self.add_new_edge(currentNode, deeperNode)
                nodeToResolve = deeperNode
            elif len(shallowQueue) != 0:
                for triangle in shallowQueue:
                    break
                if self.is_triangle_already_indexed_in_interval(shallowerInterval, triangle):
                    self.remove_triangle_from_queue(triangle, currentNode, 'shallow')
                    # print('ERROR SHALLOW')
                    continue
                shallowerNode = self.add_triangle_to_new_node(shallowerInterval, triangle)
                self.add_triangle_to_interval_inventory(shallowerInterval, triangle)
                self.add_triangle_to_queue(triangle, shallowerNode, 'current')
                nodesToResolve.add(shallowerNode)
                self.remove_triangle_from_queue(triangle, currentNode, 'shallow')
                self.add_new_edge(shallowerNode, currentNode)
                nodeToResolve = shallowerNode
            else:
                # print('passing else')
                # pass

                # print('node no queues anymore, new node selection')
                # print(nodesToResolve)
                nodesToResolve.remove(currentNode)
                for ntr in nodesToResolve:
                    break
                currentNode = ntr
                currentInterval = str(self.get_interval_from_node(currentNode))
                # print('new node: ', ntr, currentInterval)

            if len(nodesToResolve) == 0:
                # print('no unresolved nodes anymore')
                finished = True

            bgi += 0
            if bgi >= 100:
                finished = True
                print('max iteration limit exceeded')

    def build_graph_new(self):
        self.msg('> building new TRG...', 'info')

        self.triangleIntervalInventory = dict()

        # find a starting triangle, and for simplicity
        # make sure this only belongs to one interval
        for triangle in self.triangles:
            tri_intervals = self.find_intervals(triangle, indexOnly=True)
            if len(tri_intervals) == 1:
                triangle = tuple(self.pseudo_triangle(triangle))
                interval = str(tri_intervals[0])
                break

        currentNode = self.add_triangle_to_new_node(interval, triangle)
        self.add_triangle_to_interval_inventory(interval, triangle)
        self.add_triangle_to_queue(triangle, currentNode, 'current')

        nodesToResolve = set()

        finished = False
        bgi = 0
        resolveCurrent = True
        resolveDeep = False
        resolveShallow = False
        while not finished:
            # this loop should always start with:
            # currentNodeId available
            # working interval (str) available
            # currentQueue, deepQueue, shallowQueue

            deepNeighbors = self.get_neighboring_nodes(currentNode, 'deep')
            shallowNeighbors = self.get_neighboring_nodes(currentNode, 'shallow')

            if resolveCurrent:
                currentQueue = self.get_queue(currentNode, 'current')

                print('\nresolving current', currentNode)

                for triangle in currentQueue.copy():
                    # print(currentNode, triangle)
                    adjacentTriangles = self.adjacent_triangles(triangle)
                    # print(adjacentTriangles)
                    for neighbouringTriangle in adjacentTriangles:
                        if 0 not in neighbouringTriangle:
                            neighbouringIntervals = self.find_intervals(
                                neighbouringTriangle, indexOnly=True)

                            if (int(interval) in neighbouringIntervals and
                                    not self.saddle_test(triangle, neighbouringTriangle, int(interval)) and
                                    not self.is_triangle_already_indexed_in_interval(interval, neighbouringTriangle)):
                                self.add_triangle_to_node(neighbouringTriangle, currentNode)
                                self.add_triangle_to_interval_inventory(
                                    interval, neighbouringTriangle)
                                self.add_triangle_to_queue(
                                    neighbouringTriangle, currentNode, 'current')

                            if (int(interval) + 1 in neighbouringIntervals and
                                    not self.is_triangle_already_indexed_in_interval(str(int(interval) + 1), neighbouringTriangle)):
                                self.add_triangle_to_queue(
                                    neighbouringTriangle, currentNode, 'deep')

                            if (int(interval) - 1 in neighbouringIntervals and
                                    not self.is_triangle_already_indexed_in_interval(str(int(interval) - 1), neighbouringTriangle)):
                                self.add_triangle_to_queue(
                                    neighbouringTriangle, currentNode, 'shallow')

                    self.remove_triangle_from_queue(triangle, currentNode, 'current')

            elif resolveDeep:
                deepQueue = self.get_queue(currentNode, 'deep')
                # print(deepQueue)
                deeperInterval = str(int(interval) + 1)

                for triangle in deepQueue:
                    break
                deeperNode = self.add_triangle_to_new_node(deeperInterval, triangle)
                nodesToResolve.add(deeperNode)
                self.add_triangle_to_interval_inventory(deeperInterval, triangle)
                self.add_triangle_to_queue(triangle, deeperNode, 'current')
                self.add_new_edge(currentNode, deeperNode)
                # print('fd', currentNode, deeperNode)
                self.remove_triangle_from_queue(triangle, currentNode, 'deep')
                # deepIndexed = set()
                # deepTempQueue = set()
                deepTempQueue = {triangle}
                deepIndexed = {triangle}
                print('resolving deep', deeperNode)

                deepFinished = False
                while not deepFinished:

                    additions = 0
                    for triangle in deepTempQueue.copy():
                        adjacentTriangles = self.adjacent_triangles(triangle)
                        for adjacentTriangle in adjacentTriangles:
                            if (adjacentTriangle in deepQueue and
                                    adjacentTriangle not in deepIndexed):
                                deepTempQueue.add(adjacentTriangle)
                                deepIndexed.add(adjacentTriangle)
                                self.remove_triangle_from_queue(
                                    adjacentTriangle, currentNode, 'deep')
                                additions += 1
                        deepTempQueue.remove(triangle)

                    print(deepTempQueue)

                    if additions == 0:
                        deepQueue = self.get_queue(currentNode, 'deep')
                        if len(deepQueue) != 0:
                            for triangle in deepQueue:
                                break
                            print('extra deeper node')
                            # print(deepQueue)
                            deeperNode = self.add_triangle_to_new_node(deeperInterval, triangle)
                            nodesToResolve.add(deeperNode)
                            self.add_triangle_to_interval_inventory(deeperInterval, triangle)
                            self.add_triangle_to_queue(triangle, deeperNode, 'current')
                            self.add_new_edge(currentNode, deeperNode)
                            # print('ed', currentNode, deeperNode)
                            self.remove_triangle_from_queue(triangle, currentNode, 'deep')
                            # deepIndexed = set()
                            # deepTempQueue = set()
                            deepTempQueue = {triangle}
                            deepIndexed = {triangle}
                        else:
                            deepFinished = True

                print(nodesToResolve)

            elif resolveShallow:
                shallowQueue = self.get_queue(currentNode, 'shallow')
                shallowerInterval = str(int(interval) - 1)
                # print('cns', currentNode, self.get_interval_from_node(currentNode))
                # print('shallownode interval', shallowerInterval)

                for triangle in shallowQueue:
                    break
                shallowerNode = self.add_triangle_to_new_node(shallowerInterval, triangle)
                nodesToResolve.add(shallowerNode)
                self.add_triangle_to_interval_inventory(shallowerInterval, triangle)
                self.add_triangle_to_queue(triangle, shallowerNode, 'current')
                self.add_new_edge(shallowerNode, currentNode)
                # print('fs', shallowerNode, currentNode)
                self.remove_triangle_from_queue(triangle, currentNode, 'shallow')
                # deepIndexed = set()
                # deepTempQueue = set()
                shallowTempQueue = {triangle}
                shallowIndexed = {triangle}
                print('resolving shallow', shallowerNode)

                shallowFinished = False
                while not shallowFinished:

                    additions = 0
                    for triangle in shallowTempQueue.copy():
                        adjacentTriangles = self.adjacent_triangles(triangle)
                        for adjacentTriangle in adjacentTriangles:
                            if (adjacentTriangle in shallowQueue and
                                    adjacentTriangle not in shallowIndexed):
                                shallowTempQueue.add(adjacentTriangle)
                                shallowIndexed.add(adjacentTriangle)
                                self.remove_triangle_from_queue(
                                    adjacentTriangle, currentNode, 'shallow')
                                additions += 1
                        shallowTempQueue.remove(triangle)

                    if additions == 0:
                        shallowQueue = self.get_queue(currentNode, 'shallow')
                        if len(shallowQueue) != 0:
                            for triangle in shallowQueue:
                                break
                            print('extra shallow node')
                            shallowerNode = self.add_triangle_to_new_node(
                                shallowerInterval, triangle)
                            nodesToResolve.add(shallowerNode)
                            self.add_triangle_to_interval_inventory(shallowerInterval, triangle)
                            self.add_triangle_to_queue(triangle, shallowerNode, 'current')
                            self.add_new_edge(shallowerNode, currentNode)
                            # print('es', shallowerNode, currentNode)
                            self.remove_triangle_from_queue(triangle, currentNode, 'shallow')
                            # deepIndexed = set()
                            # deepTempQueue = set()
                            shallowTempQueue = {triangle}
                            shallowIndexed = {triangle}
                        else:
                            shallowFinished = True

                print(nodesToResolve)

            if (resolveCurrent and
                    len(self.get_queue(currentNode, 'current')) == 0):
                print('resolved current')
                resolveCurrent = False
                resolveDeep = True
            elif (resolveDeep and
                    len(self.get_queue(currentNode, 'deep')) == 0):
                print('resolved deep')
                resolveDeep = False
                resolveShallow = True
            elif (resolveShallow and
                    len(self.get_queue(currentNode, 'shallow')) == 0):
                print('resolved shallow')
                resolveShallow = False
                # finished = True

                for nodeToResolve in nodesToResolve:
                    break
                # print(nodeToResolve, str(self.get_interval_from_node(nodeToResolve)))

                currentNode = nodeToResolve
                nodesToResolve.discard(currentNode)
                interval = str(self.get_interval_from_node(nodeToResolve))
                resolveCurrent = True
                print('step next resolve node: ', currentNode, interval)

            bgi += 1
            if bgi >= 250:
                finished = True
                print('max iteration limit exceeded')

    def build_graph2(self):
        self.msg('> building triangle region graph...', 'info')
        self.msg('> splitting all triangles in regions...', 'info')
        # print(self.triangles)
        for triangle in self.triangles:
            if 0 not in triangle:
                intervals = self.find_intervals(triangle, indexOnly=True)
                pseudoTriangle = tuple(self.pseudo_triangle(triangle))
                for interval in intervals:
                    self.triangleRegionDict[str(interval)].add(pseudoTriangle)
        self.msg('> all triangles split in regions', 'info')

        self.msg('> splitting regions in touching nodes...', 'info')

        for interval in self.triangleRegionDict.keys():
            # print(interval)
            regionTriangles = self.triangleRegionDict[interval]
            triangleAmount = len(regionTriangles)

            if triangleAmount == 0:
                self.errors.append(
                    '{} build_graph2\tno triangles in this interval\tinterval: {}'.format(self.now(), interval))
                # print('no triangles in this region')
                continue

            indexedTriangles = set()
            queue = set()
            finished = False
            i = 0

            for triangle in regionTriangles:
                if 0 not in triangle and len(self.find_intervals(triangle)) == 1:
                    break
            indexedTriangles.add(triangle)
            currentNode = self.add_triangle_to_new_node(interval, triangle)
            queue.add(triangle)

            # for neighboringTriangle in self.adjacent_triangles(triangle):
            #     if int(interval) in self.find_intervals(neighboringTriangle):
            #         if neighboringTriangle not in indexedTriangles:
            #             if not self.saddle_test(triangle, neighboringTriangle, int(interval)):
            #                 indexedTriangles.add(neighboringTriangle)
            #                 queue.add(neighboringTriangle)
            #                 self.add_triangle_to_node(neighboringTriangle, currentNode)

            # print(queue)

            while not finished:

                # for triangle in regionTriangles.copy():
                #     break
                additions = 0
                # print(queue)
                for triangle in queue.copy():
                    for neighboringTriangle in self.adjacent_triangles(triangle):
                        # print(neighboringTriangle)
                        if 0 not in neighboringTriangle:
                            neighborIntervals = self.find_intervals(neighboringTriangle)
                            if int(interval) in neighborIntervals:
                                if neighboringTriangle not in indexedTriangles:
                                    if not self.saddle_test(triangle, neighboringTriangle, int(interval)):
                                        indexedTriangles.add(neighboringTriangle)
                                        queue.add(neighboringTriangle)
                                        self.add_triangle_to_node(neighboringTriangle, currentNode)
                                        additions += 1
                            if int(interval) + 1 in neighborIntervals:
                                self.add_triangle_to_queue(
                                    neighboringTriangle, currentNode, 'deep')
                            if int(interval) - 1 in neighborIntervals:
                                self.add_triangle_to_queue(
                                    neighboringTriangle, currentNode, 'shallow')

                    queue.remove(triangle)

                i += 0
                if len(indexedTriangles) == triangleAmount:
                    # print('all triangles in this region visited, ending')
                    finished = True
                elif i > 500:
                    self.errors.append('{} build_graph2\titeration limit exceeded on splitting in touching nodes\tinterval: {}\tcurrent node: {}'.format(self.now(),
                                                                                                                                                         interval, currentNode))
                    finished = True
                elif not additions:
                    # print('====new node====')
                    for triangle in regionTriangles.difference(indexedTriangles):
                        if 0 not in triangle and len(self.find_intervals(triangle)) == 1:
                            break
                    indexedTriangles.add(triangle)
                    # print(triangle)
                    # print('istriangle: ', self.triangulation.is_triangle(triangle))
                    # print('neighbors: ', self.adjacent_triangles(triangle))

                    existingTracker = False
                    neighboringTriangles = self.adjacent_triangles(triangle)
                    for existingNode in self.get_all_nodes_in_interval(interval):
                        if existingTracker:
                            break
                        # print('\nexistingNode: ', existingNode, interval)
                        if self.get_triangles(existingNode).intersection(triangle):
                            self.add_triangle_to_node(triangle, existingNode)
                            existingTracker = True
                        else:
                            for neighboringTriangle in neighboringTriangles:
                                # print('neighboringTriangle: ', neighboringTriangle)
                                # print(neighboringTriangle in self.get_triangles(existingNode))
                                if 0 not in neighboringTriangle:
                                    neighborIntervals = self.find_intervals(neighboringTriangle)
                                    # print('neighborIntervals: ', neighborIntervals)
                                    if int(interval) in neighborIntervals:
                                        # print('im in the interval')
                                        # if self.saddle_test(triangle, neighboringTriangle, int(interval)):
                                        #     # print('im a saddle...')
                                        if not self.saddle_test(triangle, neighboringTriangle, int(interval)):
                                            # print('im not a saddle')
                                            # print(self.get_triangles(
                                            #     existingNode).intersection(neighboringTriangle))
                                            # print(neighboringTriangle in self.get_triangles(existingNode))
                                            if neighboringTriangle in self.get_triangles(existingNode):
                                                self.add_triangle_to_node(triangle, existingNode)
                                                existingTracker = True
                                                break

                    if not existingTracker:
                        currentNode = self.add_triangle_to_new_node(interval, triangle)
                        for neighboringTriangle in self.adjacent_triangles(triangle):
                            if 0 not in neighboringTriangle:
                                neighborIntervals = self.find_intervals(neighboringTriangle)
                                if int(interval) in neighborIntervals:
                                    if neighboringTriangle not in indexedTriangles:
                                        if not self.saddle_test(triangle, neighboringTriangle, int(interval)):
                                            indexedTriangles.add(neighboringTriangle)
                                            queue.add(neighboringTriangle)
                                            self.add_triangle_to_node(
                                                neighboringTriangle, currentNode)
                                if int(interval) + 1 in neighborIntervals:
                                    self.add_triangle_to_queue(
                                        neighboringTriangle, currentNode, 'deep')
                                if int(interval) - 1 in neighborIntervals:
                                    self.add_triangle_to_queue(
                                        neighboringTriangle, currentNode, 'shallow')

                    if len(queue) == 0:
                        finished = True
                        # print(triangle)
                        # for vId in triangle:
                        #     print(self.triangulation.get_point(vId))
                        # self.msg('no queue left', 'warning')
                        self.errors.append(
                            '{} build_graph2\tno queue left\tinterval: {}\tcurrent node: {}'.format(self.now(), interval, currentNode))

            # self.add_triangle_to_new_node(interval, triangle)

        self.msg('> all regions split in adjacent triangles', 'info')

        self.establish_edges()

        self.classify_nodes()

        self.msg('> triangle region graph created', 'info')
        # self.export_all_node_triangles()
        # self.export_all_edge_triangles()

        # self.print_graph()
        pass

    def establish_edges(self):
        self.msg('> establishing edges...', 'info')

        for node in self.graph['nodes'].keys():
            nodeInterval = self.get_interval_from_node(node)
            # print('----- new node:', node, nodeInterval)

            # finished = False
            # i = 0
            # while not finished:

            deepQueue = self.get_triangles(node)
            if len(self.get_queue(node, 'deep')):
                # print('resolving deeps')
                deeperNodes = self.get_all_nodes_in_interval(nodeInterval + 1)
                # print(deeperNodes)
                for deeperNode in deeperNodes:
                    edgeIntersection = deepQueue.intersection(
                        self.get_triangles(deeperNode))
                    if len(edgeIntersection):
                        self.add_new_edge(node, deeperNode)
                        self.graph['nodes'][node]['deepQueue'].difference_update(
                            edgeIntersection)
                        self.graph['nodes'][deeperNode]['shallowQueue'].difference_update(
                            edgeIntersection)

            shallowQueue = self.get_triangles(node)
            if len(self.get_queue(node, 'shallow')):
                # print('resolving shallows')
                shallowerNodes = self.get_all_nodes_in_interval(nodeInterval - 1)
                for shallowerNode in shallowerNodes:
                    edgeIntersection = shallowQueue.intersection(
                        self.get_triangles(shallowerNode))
                    if len(edgeIntersection):
                        self.add_new_edge(shallowerNode, node)
                        self.graph['nodes'][node]['shallowQueue'].difference_update(
                            edgeIntersection)
                        self.graph['nodes'][shallowerNode]['deepQueue'].difference_update(
                            edgeIntersection)

                # i += 1
                # if len(self.get_queue(node, 'deep')) == 0 and len(self.get_queue(node, 'shallow')) == 0:
                #     print('no limit queues left')
                #     finished = True
                # if i > 10:
                #     print('iteration limit exceeded')
                #     finished = True

        self.msg('> edges established', 'info')

    def classify_peaks_pits(self, minPeak=100, minPit=100):

        self.msg('> classifying peaks and pits...', 'info')

        self.generate_depth_areas(nodeIds=[])

        peaks = {}
        pits = {}

        peaks['threshold'] = minPeak
        pits['threshold'] = minPit

        for nodeId in self.graph['nodes'].keys():
            node = self.graph['nodes'][nodeId]
            if len(node['shallowNeighbors']) == 0:
                node['classification'] = 'peak'
                edges = node['edges']
                self.compute_node_area(nodeIds=[nodeId])
                fullNodeArea = node['full_area']
                peaks[nodeId] = {}
                peaks[nodeId]['fullArea'] = fullNodeArea
                peaks[nodeId]['closed'] = True
                peaks[nodeId]['conflictBool'] = 0
                peaks[nodeId]['edges'] = edges
                # print('peak', nodeId, edges)

                # add pointers for the edges, handy for export
                for edgeId in edges:
                    self.graph['edges'][edgeId]['classification'] = 'peak'

                if node['outer_boundary']:
                    boundaryEdge = node['outer_boundary']
                    # print(boundaryEdge)
                    boundaryArea = self.graph['edges'][boundaryEdge]['iso_area']
                    peaks[nodeId]['boundaryArea'] = boundaryArea
                    if boundaryArea <= minPeak:
                        peaks[nodeId]['conflictBool'] = 1
                        for edgeId in edges:
                            self.graph['edges'][edgeId]['classification'] = 'invalid peak'

                else:
                    boundaryArea = fullNodeArea
                    peaks[nodeId]['boundaryArea'] = None
                    peaks[nodeId]['closed'] = False
                    if fullNodeArea <= minPeak:
                        peaks[nodeId]['conflictBool'] = 2
                        for edgeId in edges:
                            self.graph['edges'][edgeId]['classification'] = 'invalid (semi) peak'

                # print(fullNodeArea, boundaryArea)

            elif len(node['deepNeighbors']) == 0:
                node['classification'] = 'pit'
                edges = node['edges']
                self.compute_node_area(nodeIds=[nodeId])
                fullNodeArea = node['full_area']
                pits[nodeId] = {}
                pits[nodeId]['fullArea'] = fullNodeArea
                pits[nodeId]['closed'] = True
                pits[nodeId]['conflictBool'] = 0
                pits[nodeId]['edges'] = edges
                # print('pit', nodeId, edges)

                # add pointers for the edges, handy for export
                for edgeId in edges:
                    self.graph['edges'][edgeId]['classification'] = 'pit'

                if node['outer_boundary']:
                    boundaryEdge = node['outer_boundary']
                    # print(boundaryEdge)
                    boundaryArea = self.graph['edges'][boundaryEdge]['iso_area']
                    pits[nodeId]['boundaryArea'] = boundaryArea
                    if boundaryArea <= minPit:
                        pits[nodeId]['conflictBool'] = 1
                        for edgeId in edges:
                            self.graph['edges'][edgeId]['classification'] = 'invalid pit'
                else:
                    boundaryArea = fullNodeArea
                    pits[nodeId]['boundaryArea'] = None
                    pits[nodeId]['closed'] = False
                    if fullNodeArea <= minPit:
                        pits[nodeId]['conflictBool'] = 2
                        for edgeId in edges:
                            self.graph['edges'][edgeId]['classification'] = 'invalid (semi) pit'

                # print(fullNodeArea, boundaryArea)

        # print(peaks)
        # print(pits)

        self.peaks = peaks
        self.pits = pits

        self.msg('> peaks and pits classified', 'info')

    def classify_nodes(self):
        self.msg('> classifying nodes...', 'info')
        classifiedNodes = set()
        peakQueue = set()
        pitQueue = set()
        nrNodes = len(self.graph['nodes'].keys())

        for nodeId in self.graph['nodes'].keys():
            node = self.graph['nodes'][nodeId]
            # print(len(node['shallowNeighbors']))
            if len(node['shallowNeighbors']) == 0:
                node['classification'] = 'peak'
                peakQueue.add(nodeId)
                classifiedNodes.add(nodeId)
            elif len(node['deepNeighbors']) == 0:
                node['classification'] = 'pit'
                pitQueue.add(nodeId)
                classifiedNodes.add(nodeId)

        finished = True
        i = 0
        while not finished:
            print('============\npQ: ', peakQueue, pitQueue)

            for nodeId in peakQueue.copy():
                node = self.graph['nodes'][nodeId]
                deeperNodeIds = self.get_neighboring_nodes(nodeId, 'deep')
                print(nodeId, deeperNodeIds)
                if len(deeperNodeIds) == 1:
                    peakTracker = True
                    for deeperNodeId in deeperNodeIds:
                        for shallowerNodeId in self.get_neighboring_nodes(deeperNodeId, 'shallow'):
                            if self.graph['nodes'][shallowerNodeId]['classification'] != 'peak':
                                peakTracker = False
                        if peakTracker:
                            if len(self.get_neighboring_nodes(deeperNodeId, 'deep')) == 1:
                                self.graph['nodes'][deeperNodeId]['classification'] = 'peak'
                                peakQueue.add(deeperNodeId)
                peakQueue.remove(nodeId)

            for nodeId in pitQueue.copy():
                node = self.graph['nodes'][nodeId]
                shallowerNodeIds = self.get_neighboring_nodes(nodeId, 'shallow')
                print(nodeId, shallowerNodeIds)
                if len(shallowerNodeIds) == 1:
                    pitTracker = True
                    for shallowerNodeId in shallowerNodeIds:
                        for deeperNodeId in self.get_neighboring_nodes(shallowerNodeId, 'deep'):
                            if self.graph['nodes'][deeperNodeId]['classification'] != 'pit':
                                pitTracker = False
                        if pitTracker:
                            if len(self.get_neighboring_nodes(shallowerNodeId, 'shallow')) == 1:
                                self.graph['nodes'][shallowerNodeId]['classification'] = 'pit'
                                pitQueue.add(shallowerNodeId)
                pitQueue.remove(nodeId)

            i += 1
            if len(peakQueue) == 0 and len(pitQueue) == 0 or i > 20:
                finished = True
                print(peakQueue, pitQueue)

        self.msg('> nodes classified', 'info')

    # --------------- #
    #   UPDATING
    # --------------- #

    def remove_triangles_from_graph(self, trianglesWithInterval):

        self.print_graph()

        possibleDeletedEdges = set()
        possibleDeletedNodes = set()

        # print('updated triangles:')
        updates = 0
        deletedTriangles = 0
        for updatedTriangle in trianglesWithInterval.keys():
            deletedTriangles += 1
            pseudoTriangle = tuple(self.pseudo_triangle(updatedTriangle))
            previousIntervals = trianglesWithInterval[updatedTriangle]['previous_intervals']
            updatedIntervals = trianglesWithInterval[updatedTriangle]['updated_intervals']
            # print('----\n', updatedTriangle, previousIntervals, updatedIntervals)
            # print(self.triangleInventory[pseudoTriangle])

            for previousNode in self.triangleInventory[pseudoTriangle].copy():
                nodeId = previousNode
                nodeInterval = int(self.get_interval_from_node(nodeId))
                # print('previous node: ', nodeId, '\tinterval: ', nodeInterval)
                # print(self.triangle_in_node(pseudoTriangle, nodeId))

                self.delete_triangle_from_node(pseudoTriangle, nodeId)
                updates += 1
                possibleDeletedNodes.add(nodeId)

                if (nodeInterval - 1) in previousIntervals:
                    # print('possible shallow edge')
                    shallowNeighbors = self.get_neighboring_nodes(nodeId, 'shallow')
                    self.graph['nodes'][nodeId]['shallowNeighbors'].discard(pseudoTriangle)
                    # print(shallowNeighbors)
                    for shallowNeighbor in shallowNeighbors:
                        possibleDeletedEdges.add((shallowNeighbor, nodeId))
                    # print(nodeInterval-1)
                    # print('also in shallow queue', pseudoTriangle in self.get_queue(nodeId, 'shallow'))
                if (nodeInterval + 1) in previousIntervals:
                    # print('possible deep edge')
                    deepNeighbors = self.get_neighboring_nodes(nodeId, 'deep')
                    self.graph['nodes'][nodeId]['deepNeighbors'].discard(pseudoTriangle)
                    for deepNeighbor in deepNeighbors:
                        possibleDeletedEdges.add((nodeId, deepNeighbor))
                    # print(nodeInterval+1)
                    # print('also in deep queue', pseudoTriangle in self.get_queue(nodeId, 'deep'))

            del self.triangleInventory[pseudoTriangle]

        print('removed triangles: ', deletedTriangles, 'updates: ', updates)

        return possibleDeletedNodes, possibleDeletedEdges

    def insert_triangles_into_region_graph2(self, triangles, oldEdges):
        self.msg('inserting triangles again...', 'info')
        print('triangles to insert: ', len(triangles))

        tempTriangleRegionDict = {}

        # first grouping all new triangles in regions of equal depth
        for triangle in triangles:
            # print(triangle)
            for interval in self.find_intervals(triangle):
                if str(interval) not in tempTriangleRegionDict.keys():
                    tempTriangleRegionDict[str(interval)] = {triangle}
                else:
                    tempTriangleRegionDict[str(interval)].add(triangle)

        # tempDebugging = set()
        # for inter in tempTriangleRegionDict.keys():
        #     for tri in tempTriangleRegionDict[inter]:
        #         tempDebugging.add(tri)
        # print(len(tempDebugging))

        tempNodes = set()
        insertedTriangles = 0
        updates = 0
        insertedTrianglesSet = set()

        for interval in tempTriangleRegionDict.keys():
            # print(interval)
            regionTriangles = tempTriangleRegionDict[interval]
            # tempDebugging.update(regionTriangles)
            triangleAmount = len(regionTriangles)
            self.debug('----- new interval\n {} {}'.format(interval, triangleAmount))

            if triangleAmount == 0:
                self.errors.append(
                    '{} insert_triangles_into_region_graph\tno triangles in this interval\tinterval: {}'.format(self.now(), interval))
                # print('no triangles in this region')
                break

            indexedTriangles = set()
            queue = set()
            finished = False
            i = 0

            for triangle in regionTriangles:
                if 0 not in triangle:  # and len(self.find_intervals(triangle)) == 1:
                    break
            indexedTriangles.add(triangle)
            currentNode = self.add_triangle_to_new_node(interval, triangle)
            tempNodes.add(currentNode)
            # tempNodes[currentNode] = {'previous_nodes': set()}
            # tempNodes[currentNode]['previous_nodes'].update(oldTriangleInventory[triangle])
            insertedTriangles += 1
            updates += 1
            insertedTrianglesSet.add(triangle)
            queue.add(triangle)

            while not finished:

                additions = 0
                # print(queue)
                for triangle in queue.copy():
                    for neighboringTriangle in self.adjacent_triangles(triangle):
                        # print(neighboringTriangle)
                        if 0 not in neighboringTriangle:
                            if neighboringTriangle in triangles:
                                neighborIntervals = self.find_intervals(neighboringTriangle)
                                if int(interval) in neighborIntervals:
                                    if neighboringTriangle not in indexedTriangles:
                                        if not self.saddle_test(triangle, neighboringTriangle, int(interval)):
                                            indexedTriangles.add(neighboringTriangle)
                                            queue.add(neighboringTriangle)
                                            self.add_triangle_to_node(
                                                neighboringTriangle, currentNode)
                                            # tempNodes[currentNode]['previous_nodes'].update(
                                            #     oldTriangleInventory[triangle])
                                            additions += 1
                                            insertedTriangles += 1
                                            insertedTrianglesSet.add(neighboringTriangle)
                                if int(interval) + 1 in neighborIntervals:
                                    self.add_triangle_to_queue(
                                        neighboringTriangle, currentNode, 'deep')
                                if int(interval) - 1 in neighborIntervals:
                                    self.add_triangle_to_queue(
                                        neighboringTriangle, currentNode, 'shallow')

                    queue.remove(triangle)

                i += 0
                if len(indexedTriangles) == triangleAmount:
                    self.debug('all triangles in this region visited, ending')
                    self.debug(len(indexedTriangles))
                    finished = True
                elif i > 500:
                    self.errors.append('{} insert_triangles_into_region_graph\titeration limit exceeded on splitting in touching nodes\tinterval: {}\tcurrent node: {}'.format(
                        self.now(), interval, currentNode))
                    finished = True
                elif not additions:
                    # print('====new node====')
                    for triangle in regionTriangles.difference(indexedTriangles):
                        if 0 not in triangle:  # and len(self.find_intervals(triangle)) == 1:
                            break
                    indexedTriangles.add(triangle)
                    # print(triangle)
                    # print('istriangle: ', self.triangulation.is_triangle(triangle))
                    # print('neighbors: ', self.adjacent_triangles(triangle))

                    existingTracker = False
                    neighboringTriangles = self.adjacent_triangles(triangle)
                    for existingNode in self.get_all_nodes_in_interval(interval):
                        if existingTracker:
                            break
                        # print('\nexistingNode: ', existingNode, interval)
                        # self.get_triangles(existingNode).intersection(triangle):
                        if triangle in self.get_triangles(existingNode):
                            self.add_triangle_to_node(triangle, existingNode)
                            # tempNodes[currentNode]['previous_nodes'].update(
                            #     oldTriangleInventory[triangle])
                            indexedTriangles.add(triangle)
                            existingTracker = True
                            insertedTriangles += 1
                            insertedTrianglesSet.add(triangle)
                        else:
                            for neighboringTriangle in neighboringTriangles:
                                # print('neighboringTriangle: ', neighboringTriangle)
                                # print(neighboringTriangle in self.get_triangles(existingNode))
                                if 0 not in neighboringTriangle:
                                    if neighboringTriangle in triangles:
                                        neighborIntervals = self.find_intervals(neighboringTriangle)
                                        # print('neighborIntervals: ', neighborIntervals)
                                        if int(interval) in neighborIntervals:
                                            # print('im in the interval')
                                            # if self.saddle_test(triangle, neighboringTriangle, int(interval)):
                                            #     # print('im a saddle...')
                                            if not self.saddle_test(triangle, neighboringTriangle, int(interval)):
                                                # print('im not a saddle')
                                                # print(self.get_triangles(
                                                #     existingNode).intersection(neighboringTriangle))
                                                # print(neighboringTriangle in self.get_triangles(existingNode))
                                                if neighboringTriangle in self.get_triangles(existingNode):
                                                    self.add_triangle_to_node(
                                                        triangle, existingNode)
                                                    indexedTriangles.add(triangle)
                                                    # tempNodes[currentNode]['previous_nodes'].update(
                                                    #     oldTriangleInventory[triangle])
                                                    existingTracker = True
                                                    insertedTriangles += 1
                                                    insertedTrianglesSet.add(triangle)
                                                    # break

                    if not existingTracker:
                        currentNode = self.add_triangle_to_new_node(interval, triangle)
                        tempNodes.add(currentNode)
                        # indexedTriangles.add(currentNode)

                        # tempNodes[currentNode] = {'previous_nodes': set()}
                        # tempNodes[currentNode]['previous_nodes'].update(
                        #     oldTriangleInventory[triangle])
                        insertedTriangles += 1
                        insertedTrianglesSet.add(triangle)
                        for neighboringTriangle in self.adjacent_triangles(triangle):
                            if 0 not in neighboringTriangle:
                                if neighboringTriangle in triangles:
                                    neighborIntervals = self.find_intervals(neighboringTriangle)
                                    if int(interval) in neighborIntervals:
                                        if neighboringTriangle not in indexedTriangles:
                                            if not self.saddle_test(triangle, neighboringTriangle, int(interval)):
                                                indexedTriangles.add(neighboringTriangle)
                                                queue.add(neighboringTriangle)
                                                self.add_triangle_to_node(
                                                    neighboringTriangle, currentNode)
                                                insertedTriangles += 1
                                                insertedTrianglesSet.add(neighboringTriangle)
                                                # tempNodes[currentNode]['previous_nodes'].update(
                                                #     oldTriangleInventory[triangle])
                                    if int(interval) + 1 in neighborIntervals:
                                        self.add_triangle_to_queue(
                                            neighboringTriangle, currentNode, 'deep')
                                    if int(interval) - 1 in neighborIntervals:
                                        self.add_triangle_to_queue(
                                            neighboringTriangle, currentNode, 'shallow')

                    if len(queue) == 0:
                        finished = False
                        self.debug('no queue left: {} {}'.format(
                            len(indexedTriangles), triangleAmount))
                        for triangle in regionTriangles.difference(indexedTriangles):
                            if 0 not in triangle:  # and len(self.find_intervals(triangle)) == 1:
                                break
                        # print(triangle in indexedTriangles)
                        indexedTriangles.add(triangle)

                        currentNode = self.add_triangle_to_new_node(interval, triangle)
                        tempNodes.add(currentNode)
                        # tempNodes[currentNode] = {'previous_nodes': set()}
                        # tempNodes[currentNode]['previous_nodes'].update(
                        #     oldTriangleInventory[triangle])
                        insertedTriangles += 1
                        updates += 1
                        insertedTrianglesSet.add(triangle)
                        queue.add(triangle)

                        # print(triangle)
                        # for vId in triangle:
                        #     print(self.triangulation.get_point(vId))
                        # self.msg('no queue left', 'warning')
                        self.errors.append(
                            '{} insert_triangles_in_region_graph\tno queue left\tinterval: {}\tcurrent node: {}'.format(self.now(), interval, currentNode))

        self.debug('tempNodes: {}'.format(tempNodes))
        affectedNodes = tempNodes.copy()
        # self.add_triangle_to_new_node(interval, triangle)

        # print('tempDebug: ', len(tempDebugging))
        # print('inserted triangles: ', insertedTriangles, len(
        #     insertedTrianglesSet), len(indexedTriangles))
        # print('remove/insert diff: ', set(triangles).difference(insertedTrianglesSet))

        self.debug('======\ntempNodes')
        # merge nodes with existing nodes if possible
        for tempNode in tempNodes:
            tempNodeInterval = self.get_interval_from_node(tempNode)
            previousNodes = oldEdges
            tempNodeTriangles = self.get_triangles(tempNode)
            self.debug('------ {} {}'.format(tempNode, tempNodeInterval))
            self.debug(previousNodes)
            match = False
            for previousNode in previousNodes:
                if self.is_node(previousNode):
                    # print(self.get_interval_from_node(previousNode))
                    if self.get_interval_from_node(previousNode) == tempNodeInterval and previousNode not in tempNodes:
                        # print(previousNode)
                        for tempNodeTriangle in tempNodeTriangles:
                            for adjacentTriangle in self.adjacent_triangles(tempNodeTriangle):
                                if not self.saddle_test(tempNodeTriangle, adjacentTriangle, tempNodeInterval):
                                    # print(oldTriangleInventory[adjacentTriangle])
                                    # in oldTriangleInventory[adjacentTriangle]:
                                    if adjacentTriangle in self.get_triangles(previousNode):
                                        match = True
                                        # print('merging: ', previousNode, tempNode)
                                        self.merge_nodes(previousNode, tempNode)
                                        affectedNodes.add(previousNode)
                                        affectedNodes.discard(tempNode)
                                        break
                                if match:
                                    break
                            if match:
                                break
                    if match:
                        break

            if match is False:
                self.debug('need searching.. BUT should be in the previousedges??')
                # TODO first try to search the shallow/deeper nodes of the previous nodes, probably it is adjacent to that
                for oldEdgingNode in oldEdges:
                    if self.is_node(oldEdgingNode):
                        # for sameIntervalNode in self.regionNodes[str(tempNodeInterval)]:
                        # if tempNodeInterval == self.get_interval_from_node(oldEdgingNode)
                        if oldEdgingNode not in tempNodes and tempNodeInterval == self.get_interval_from_node(oldEdgingNode):
                            self.debug(oldEdgingNode)
                            for tempNodeTriangle in tempNodeTriangles:
                                for adjacentTriangle in self.adjacent_triangles(tempNodeTriangle):
                                    if not self.saddle_test(tempNodeTriangle, adjacentTriangle, tempNodeInterval):
                                        # sameIntervalNode in oldTriangleInventory[adjacentTriangle]:
                                        if adjacentTriangle in self.get_triangles(oldEdgingNode):
                                            match = True
                                            # print('merging nodes: ', oldEdgingNode, tempNode)
                                            self.merge_nodes(oldEdgingNode, tempNode)
                                            affectedNodes.add(oldEdgingNode)
                                            affectedNodes.discard(tempNode)
                                            break
                                if match:
                                    break
                    if match:
                        break

            # if match is False:
            #     print('need searching.. BUT should be in the previousedges??')
            #     # TODO first try to search the shallow/deeper nodes of the previous nodes, probably it is adjacent to that
            #     for sameIntervalNode in self.regionNodes[str(tempNodeInterval)]:
            #         if self.is_node(sameIntervalNode) and sameIntervalNode not in tempNodes:
            #             print(sameIntervalNode)
            #             for tempNodeTriangle in tempNodeTriangles:
            #                 for adjacentTriangle in self.adjacent_triangles(tempNodeTriangle):
            #                     if not self.saddle_test(tempNodeTriangle, adjacentTriangle, tempNodeInterval):
            #                         # sameIntervalNode in oldTriangleInventory[adjacentTriangle]:
            #                         if adjacentTriangle in self.get_triangles(sameIntervalNode):
            #                             match = True
            #                             self.merge_nodes(sameIntervalNode, tempNode)
            #                             break
            #                 if match:
            #                     break
            #         if match:
            #             break

            if match is False:
                self.debug('im a completely new/rebuilt node')
                pass

        return affectedNodes

    def insert_triangles_into_region_graph(self, trianglesWithInterval, oldTriangleInventory):
        self.msg('inserting triangles again...', 'info')
        print(len(trianglesWithInterval.keys()))

        tempTriangleRegionDict = {}

        # first grouping all new triangles in regions of equal depth
        for triangle in trianglesWithInterval.keys():
            print(triangle, oldTriangleInventory[triangle])
            for interval in trianglesWithInterval[triangle]['updated_intervals']:
                if str(interval) not in tempTriangleRegionDict.keys():
                    tempTriangleRegionDict[str(interval)] = {triangle}
                else:
                    tempTriangleRegionDict[str(interval)].add(triangle)

        tempDebugging = set()
        # for inter in tempTriangleRegionDict.keys():
        #     for tri in tempTriangleRegionDict[inter]:
        #         tempDebugging.add(tri)
        # print(len(tempDebugging))

        tempNodes = dict()
        insertedTriangles = 0
        updates = 0
        insertedTrianglesSet = set()

        for interval in tempTriangleRegionDict.keys():
            # print(interval)
            regionTriangles = tempTriangleRegionDict[interval]
            tempDebugging.update(regionTriangles)
            triangleAmount = len(regionTriangles)
            print('----- new interval\n', interval, triangleAmount)

            if triangleAmount == 0:
                self.errors.append(
                    '{} insert_triangles_into_region_graph\tno triangles in this interval\tinterval: {}'.format(self.now(), interval))
                # print('no triangles in this region')
                break

            indexedTriangles = set()
            queue = set()
            finished = False
            i = 0

            for triangle in regionTriangles:
                if 0 not in triangle:  # and len(self.find_intervals(triangle)) == 1:
                    break
            indexedTriangles.add(triangle)
            currentNode = self.add_triangle_to_new_node(interval, triangle)
            tempNodes[currentNode] = {'previous_nodes': set()}
            tempNodes[currentNode]['previous_nodes'].update(oldTriangleInventory[triangle])
            insertedTriangles += 1
            updates += 1
            insertedTrianglesSet.add(triangle)
            queue.add(triangle)

            while not finished:

                additions = 0
                # print(queue)
                for triangle in queue.copy():
                    for neighboringTriangle in self.adjacent_triangles(triangle):
                        # print(neighboringTriangle)
                        if 0 not in neighboringTriangle:
                            if neighboringTriangle in trianglesWithInterval.keys():
                                neighborIntervals = self.find_intervals(neighboringTriangle)
                                if int(interval) in neighborIntervals:
                                    if neighboringTriangle not in indexedTriangles:
                                        if not self.saddle_test(triangle, neighboringTriangle, int(interval)):
                                            indexedTriangles.add(neighboringTriangle)
                                            queue.add(neighboringTriangle)
                                            self.add_triangle_to_node(
                                                neighboringTriangle, currentNode)
                                            tempNodes[currentNode]['previous_nodes'].update(
                                                oldTriangleInventory[triangle])
                                            additions += 1
                                            insertedTriangles += 1
                                            insertedTrianglesSet.add(neighboringTriangle)
                                if int(interval) + 1 in neighborIntervals:
                                    self.add_triangle_to_queue(
                                        neighboringTriangle, currentNode, 'deep')
                                if int(interval) - 1 in neighborIntervals:
                                    self.add_triangle_to_queue(
                                        neighboringTriangle, currentNode, 'shallow')

                    queue.remove(triangle)

                i += 0
                if len(indexedTriangles) == triangleAmount:
                    print('all triangles in this region visited, ending')
                    print(len(indexedTriangles))
                    finished = True
                elif i > 500:
                    self.errors.append('{} insert_triangles_into_region_graph\titeration limit exceeded on splitting in touching nodes\tinterval: {}\tcurrent node: {}'.format(
                        self.now(), interval, currentNode))
                    finished = True
                elif not additions:
                    # print('====new node====')
                    for triangle in regionTriangles.difference(indexedTriangles):
                        if 0 not in triangle:  # and len(self.find_intervals(triangle)) == 1:
                            break
                    indexedTriangles.add(triangle)
                    # print(triangle)
                    # print('istriangle: ', self.triangulation.is_triangle(triangle))
                    # print('neighbors: ', self.adjacent_triangles(triangle))

                    existingTracker = False
                    neighboringTriangles = self.adjacent_triangles(triangle)
                    for existingNode in self.get_all_nodes_in_interval(interval):
                        if existingTracker:
                            break
                        # print('\nexistingNode: ', existingNode, interval)
                        if self.get_triangles(existingNode).intersection(triangle):
                            self.add_triangle_to_node(triangle, existingNode)
                            tempNodes[currentNode]['previous_nodes'].update(
                                oldTriangleInventory[triangle])
                            existingTracker = True
                            insertedTriangles += 1
                            insertedTrianglesSet.add(triangle)
                        else:
                            for neighboringTriangle in neighboringTriangles:
                                # print('neighboringTriangle: ', neighboringTriangle)
                                # print(neighboringTriangle in self.get_triangles(existingNode))
                                if 0 not in neighboringTriangle:
                                    if neighboringTriangle in trianglesWithInterval.keys():
                                        neighborIntervals = self.find_intervals(neighboringTriangle)
                                        # print('neighborIntervals: ', neighborIntervals)
                                        if int(interval) in neighborIntervals:
                                            # print('im in the interval')
                                            # if self.saddle_test(triangle, neighboringTriangle, int(interval)):
                                            #     # print('im a saddle...')
                                            if not self.saddle_test(triangle, neighboringTriangle, int(interval)):
                                                # print('im not a saddle')
                                                # print(self.get_triangles(
                                                #     existingNode).intersection(neighboringTriangle))
                                                # print(neighboringTriangle in self.get_triangles(existingNode))
                                                if neighboringTriangle in self.get_triangles(existingNode):
                                                    self.add_triangle_to_node(
                                                        triangle, existingNode)
                                                    tempNodes[currentNode]['previous_nodes'].update(
                                                        oldTriangleInventory[triangle])
                                                    existingTracker = True
                                                    insertedTriangles += 1
                                                    insertedTrianglesSet.add(triangle)
                                                    # break

                    if not existingTracker:
                        currentNode = self.add_triangle_to_new_node(interval, triangle)
                        tempNodes[currentNode] = {'previous_nodes': set()}
                        tempNodes[currentNode]['previous_nodes'].update(
                            oldTriangleInventory[triangle])
                        insertedTriangles += 1
                        insertedTrianglesSet.add(triangle)
                        for neighboringTriangle in self.adjacent_triangles(triangle):
                            if 0 not in neighboringTriangle:
                                if neighboringTriangle in trianglesWithInterval.keys():
                                    neighborIntervals = self.find_intervals(neighboringTriangle)
                                    if int(interval) in neighborIntervals:
                                        if neighboringTriangle not in indexedTriangles:
                                            if not self.saddle_test(triangle, neighboringTriangle, int(interval)):
                                                indexedTriangles.add(neighboringTriangle)
                                                queue.add(neighboringTriangle)
                                                self.add_triangle_to_node(
                                                    neighboringTriangle, currentNode)
                                                insertedTriangles += 1
                                                insertedTrianglesSet.add(neighboringTriangle)
                                                tempNodes[currentNode]['previous_nodes'].update(
                                                    oldTriangleInventory[triangle])
                                    if int(interval) + 1 in neighborIntervals:
                                        self.add_triangle_to_queue(
                                            neighboringTriangle, currentNode, 'deep')
                                    if int(interval) - 1 in neighborIntervals:
                                        self.add_triangle_to_queue(
                                            neighboringTriangle, currentNode, 'shallow')

                    if len(queue) == 0:
                        finished = False
                        print('no queue left: ', len(indexedTriangles), triangleAmount)
                        for triangle in regionTriangles.difference(indexedTriangles):
                            if 0 not in triangle:  # and len(self.find_intervals(triangle)) == 1:

                                break
                        indexedTriangles.add(triangle)
                        currentNode = self.add_triangle_to_new_node(interval, triangle)
                        tempNodes[currentNode] = {'previous_nodes': set()}
                        tempNodes[currentNode]['previous_nodes'].update(
                            oldTriangleInventory[triangle])
                        insertedTriangles += 1
                        updates += 1
                        insertedTrianglesSet.add(triangle)
                        queue.add(triangle)

                        # print(triangle)
                        # for vId in triangle:
                        #     print(self.triangulation.get_point(vId))
                        # self.msg('no queue left', 'warning')
                        self.errors.append(
                            '{} insert_triangles_in_region_graph\tno queue left\tinterval: {}\tcurrent node: {}'.format(self.now(), interval, currentNode))

            # self.add_triangle_to_new_node(interval, triangle)

        print('tempDebug: ', len(tempDebugging))
        print('inserted triangles: ', insertedTriangles, len(
            insertedTrianglesSet), len(indexedTriangles))
        print('remove/insert diff: ', set(trianglesWithInterval.keys()).difference(insertedTrianglesSet))

        print('======\ntempNodes')
        for tempNode in tempNodes.keys():
            tempNodeInterval = self.get_interval_from_node(tempNode)
            previousNodes = tempNodes[tempNode]['previous_nodes']
            tempNodeTriangles = self.get_triangles(tempNode)
            print('------', tempNode, tempNodeInterval)
            print(previousNodes)
            match = False
            for previousNode in previousNodes:
                # print(self.get_interval_from_node(previousNode))
                if self.get_interval_from_node(previousNode) == tempNodeInterval and previousNode not in tempNodes.keys():
                    # print(previousNode)
                    for tempNodeTriangle in tempNodeTriangles:
                        for adjacentTriangle in self.adjacent_triangles(tempNodeTriangle):
                            if not self.saddle_test(tempNodeTriangle, adjacentTriangle, tempNodeInterval):
                                # print(oldTriangleInventory[adjacentTriangle])
                                if previousNode in oldTriangleInventory[adjacentTriangle]:
                                    if self.is_node(previousNode):
                                        match = True
                                        self.merge_nodes(previousNode, tempNode)
                                        break
                            if match:
                                break
                        if match:
                            break
                if match:
                    break

            if match is False:
                print('need searching..')
                # TODO first try to search the shallow/deeper nodes of the previous nodes, probably it is adjacent to that
                for sameIntervalNode in self.regionNodes[str(tempNodeInterval)]:
                    if self.is_node(sameIntervalNode):
                        print(sameIntervalNode)
                        for tempNodeTriangle in tempNodeTriangles:
                            for adjacentTriangle in self.adjacent_triangles(tempNodeTriangle):
                                if not self.saddle_test(tempNodeTriangle, adjacentTriangle, tempNodeInterval):
                                    if sameIntervalNode in oldTriangleInventory[adjacentTriangle]:
                                        match = True
                                        self.merge_nodes(sameIntervalNode, tempNode)
                                        break
                            if match:
                                break
                    if match:
                        break

            if match is False:
                print('im a completely new node')

    def merge_nodes(self, keepNode, mergeNode):
        self.debug('mergin nodes: {} {}'.format(keepNode, mergeNode))

        trianglesToAdd = self.get_triangles(mergeNode)
        deepsToAdd = self.get_queue(mergeNode, 'deep')
        shallowsToAdd = self.get_queue(mergeNode, 'shallow')

        for triangle in trianglesToAdd:
            self.add_triangle_to_node(triangle, keepNode)
        for triangle in deepsToAdd:
            self.add_triangle_to_queue(triangle, keepNode, 'deep')
        for triangle in shallowsToAdd:
            self.add_triangle_to_queue(triangle, keepNode, 'shallow')

        # self.delete_node(mergeNode)
        self.remove_node_and_all_contents(mergeNode)

    def check_deleted_nodes(self, listOfPossibleNodes):
        deletedNodes = set()
        for nodeId in listOfPossibleNodes:
            if len(self.get_triangles(nodeId)) == 0:
                deletedNodes.add(nodeId)
        return deletedNodes

    def delete_edge(self, edgeCombination):
        self.debug('deleting edge from graph: {}'.format(edgeCombination))

        shallowNode = edgeCombination[0]
        deepNode = edgeCombination[1]
        # remove pointers
        if shallowNode in self.graph['nodes'].keys():
            self.graph['nodes'][shallowNode]['deepNeighbors'].discard(deepNode)
        if deepNode in self.graph['nodes'].keys():
            self.graph['nodes'][deepNode]['shallowNeighbors'].discard(shallowNode)

        # remove edge itself
        for edgeId in self.graph['edges'].keys():
            if self.graph['edges'][edgeId]['edge'] == [shallowNode, deepNode]:
                del self.graph['edges'][edgeId]
                if shallowNode in self.graph['nodes']:
                    self.graph['nodes'][shallowNode]['edges'].remove(edgeId)
                if deepNode in self.graph['nodes']:
                    self.graph['nodes'][deepNode]['edges'].remove(edgeId)
                self.debug('removed edge')
                break

    def remove_node_and_all_contents(self, nodeId):
        self.debug('deleting node from graph: {}'.format(nodeId))
        nodeInterval = self.get_interval_from_node(nodeId)

        # remove pointers from neighboring nodes
        shallowNeighbors = self.get_neighboring_nodes(nodeId, 'shallow')
        for shallowNeighbor in shallowNeighbors:
            self.graph['nodes'][shallowNeighbor]['deepNeighbors'].remove(nodeId)
            # edgesToRemove.append((shallowNeighbor, nodeId))
        deepNeighbors = self.get_neighboring_nodes(nodeId, 'deep')
        for deepNeighbor in deepNeighbors:
            self.graph['nodes'][deepNeighbor]['shallowNeighbors'].remove(nodeId)
            # edgesToRemove.append((nodeId, deepNeighbor))

        # removes triangles from inventory
        for triangle in self.get_triangles(nodeId):
            # self.triangleInventory.pop(triangle, None)
            self.triangleInventory[triangle].discard(nodeId)

        # remove from regionNodes dict
        self.regionNodes[str(nodeInterval)].remove(nodeId)

        # remove node itself
        del self.graph['nodes'][nodeId]
        self.availableNodeIds.add(nodeId)

    def delete_node(self, nodeId):
        # from graph, from edges, pointers of neighbors
        self.debug('deleting node from graph: {}'.format(nodeId))
        nodeInterval = self.get_interval_from_node(nodeId)

        edgesToRemove = []

        # remove pointers from neighboring nodes
        shallowNeighbors = self.get_neighboring_nodes(nodeId, 'shallow')
        for shallowNeighbor in shallowNeighbors:
            self.graph['nodes'][shallowNeighbor]['deepNeighbors'].remove(nodeId)
            edgesToRemove.append((shallowNeighbor, nodeId))
        deepNeighbors = self.get_neighboring_nodes(nodeId, 'deep')
        for deepNeighbor in deepNeighbors:
            self.graph['nodes'][deepNeighbor]['shallowNeighbors'].remove(nodeId)
            edgesToRemove.append((nodeId, deepNeighbor))

        # remove edges
        # for edge in edgesToRemove:
        edgeIdsToRemove = set()
        for edgeId in self.graph['edges'].keys():
            if self.graph['edges'][edgeId]['edge'] in edgesToRemove:
                edgeIdsToRemove.add(edgeId)
        for edgeIdToRemove in edgeIdsToRemove:
            del self.graph['edges'][edgeIdToRemove]

        # remove from regionNodes dict
        self.regionNodes[str(nodeInterval)].remove(nodeId)

        # remove node itself
        del self.graph['nodes'][nodeId]
        self.availableNodeIds.add(nodeId)

    def get_changed_triangles(self, updatedVertices, oldTriangleInventory):
        updatedTriangles = dict()
        triangleNodes = set()
        for updatedVertex in updatedVertices:
            # print('=== updated vertex: ', updatedVertex)
            incidentTriangles = self.triangulation.incident_triangles_to_vertex(updatedVertex)
            for incidentTriangle in incidentTriangles:
                incidentTriangle = tuple(self.pseudo_triangle(incidentTriangle))
                # check whether the vertical intervals actually changed, otherwise updating is not needed
                previousIntervals = self.find_previous_intervals(incidentTriangle)
                updatedIntervals = self.find_intervals(incidentTriangle, indexOnly=True)
                if previousIntervals != updatedIntervals:
                    # print(incidentTriangle, previousIntervals, updatedIntervals)
                    pseudoTriangle = tuple(self.pseudo_triangle(incidentTriangle))
                    updatedTriangles[pseudoTriangle] = dict()
                    updatedTriangles[pseudoTriangle]['previous_intervals'] = previousIntervals
                    updatedTriangles[pseudoTriangle]['updated_intervals'] = updatedIntervals
                    # print(incidentTriangle, oldTriangleInventory[pseudoTriangle])
                    triangleNodes.update(oldTriangleInventory[pseudoTriangle])
                    # updatedTriangles.add(tuple(self.pseudo_triangle(incidentTriangle)))

        return updatedTriangles, triangleNodes

    def update_region_graph(self, updatedVertices):
        # simple approach, just delete all of the incident triangles and rebuild
        updatedTriangles = dict()
        for updatedVertex in updatedVertices:
            # print('=== updated vertex: ', updatedVertex)
            incidentTriangles = self.triangulation.incident_triangles_to_vertex(updatedVertex)
            for incidentTriangle in incidentTriangles:
                # check whether the vertical intervals actually changed, otherwise updating is not needed
                previousIntervals = self.find_previous_intervals(incidentTriangle)
                updatedIntervals = self.find_intervals(incidentTriangle, indexOnly=True)
                if previousIntervals != updatedIntervals:
                    # print(incidentTriangle, previousIntervals, updatedIntervals)
                    pseudoTriangle = tuple(self.pseudo_triangle(incidentTriangle))
                    updatedTriangles[pseudoTriangle] = dict()
                    updatedTriangles[pseudoTriangle]['previous_intervals'] = previousIntervals
                    updatedTriangles[pseudoTriangle]['updated_intervals'] = updatedIntervals
                    # updatedTriangles.add(tuple(self.pseudo_triangle(incidentTriangle)))

        print('updated triangles: ', len(updatedTriangles))

        for updatedVertex in updatedVertices:
            self.vertexDict.remove_previous_z(self.triangulation.get_point(updatedVertex))

        if len(updatedTriangles) == 0:
            return

        oldTriangleInventory = self.triangleInventory.copy()
        possibleDeletedNodes, possibleDeletedEdges = self.remove_triangles_from_graph(
            updatedTriangles)

        if possibleDeletedNodes or possibleDeletedEdges:
            print(possibleDeletedNodes, '\n', possibleDeletedEdges)
            deletedNodes = self.check_deleted_nodes(possibleDeletedNodes)
            if deletedNodes:
                for deletedNode in deletedNodes:

                    # TODO, delete a node!

                    shallowNeighbors = self.get_neighboring_nodes(deletedNode, 'shallow')
                    for shallowNeighbor in shallowNeighbors:
                        possibleDeletedEdges.add((shallowNeighbor, deletedNode))
                    deepNeighbors = self.get_neighboring_nodes(deletedNode, 'deep')
                    for deepNeighbor in deepNeighbors:
                        possibleDeletedEdges.add((deletedNode, deepNeighbor))

                    self.delete_node(deletedNode)

            print(possibleDeletedEdges)
            for possibleDeletedEdge in possibleDeletedEdges:
                if possibleDeletedEdge[0] not in self.graph['nodes'].keys() or possibleDeletedEdge[1] not in self.graph['nodes'].keys():
                    # node already deleted, so need to delete the edge as well
                    self.delete_edge(possibleDeletedEdge)
                else:
                    shallowNode = possibleDeletedEdge[0]
                    shallowTriangles = self.get_triangles(shallowNode)
                    deepNode = possibleDeletedEdge[1]
                    deepTriangles = self.get_triangles(deepNode)
                    if len(shallowTriangles.intersection(deepTriangles)) == 0:
                        # no intersection anymore, delete edge
                        self.delete_edge(possibleDeletedEdge)

        self.insert_triangles_into_region_graph(updatedTriangles, oldTriangleInventory)
        # self.print_graph()

    def establish_edges_on_affected_nodes(self, affectedNodes):
        self.debug(affectedNodes)
        # print(self.get_triangles('7'))
        for nodeId in affectedNodes:
            # print(nodeId)
            nodeInterval = self.get_interval_from_node(nodeId)
            nodeTriangles = self.get_triangles(nodeId)

            for otherNodeId in affectedNodes:
                # print(nodeId, otherNodeId)
                otherNodeInterval = self.get_interval_from_node(otherNodeId)
                if (nodeInterval + 1) == otherNodeInterval:
                    # deeper node
                    edgeIntersection = nodeTriangles.intersection(
                        self.get_triangles(otherNodeId))
                    if len(edgeIntersection):
                        self.add_new_edge(nodeId, otherNodeId)
                        self.graph['nodes'][nodeId]['deepQueue'].difference_update(
                            edgeIntersection)
                        self.graph['nodes'][otherNodeId]['shallowQueue'].difference_update(
                            edgeIntersection)
                elif (nodeInterval - 1) == otherNodeInterval:
                    # shallower node
                    edgeIntersection = nodeTriangles.intersection(
                        self.get_triangles(otherNodeId))
                    if len(edgeIntersection):
                        self.add_new_edge(otherNodeId, nodeId)
                        self.graph['nodes'][nodeId]['shallowQueue'].difference_update(
                            edgeIntersection)
                        self.graph['nodes'][otherNodeId]['deepQueue'].difference_update(
                            edgeIntersection)

            # deepQueue = self.get_triangles(node)
            # if len(self.get_queue(node, 'deep')):
            #     # print('resolving deeps')
            #     deeperNodes = self.get_all_nodes_in_interval(nodeInterval + 1)
            #     # print(deeperNodes)
            #     for deeperNode in deeperNodes:
            #         edgeIntersection = deepQueue.intersection(
            #             self.get_triangles(deeperNode))
            #         if len(edgeIntersection):
            #             self.add_new_edge(node, deeperNode)
            #             self.graph['nodes'][node]['deepQueue'].difference_update(
            #                 edgeIntersection)
            #             self.graph['nodes'][deeperNode]['shallowQueue'].difference_update(
            #                 edgeIntersection)
            #
            # shallowQueue = self.get_triangles(node)
            # if len(self.get_queue(node, 'shallow')):
            #     # print('resolving shallows')
            #     shallowerNodes = self.get_all_nodes_in_interval(nodeInterval - 1)
            #     for shallowerNode in shallowerNodes:
            #         edgeIntersection = shallowQueue.intersection(
            #             self.get_triangles(shallowerNode))
            #         if len(edgeIntersection):
            #             self.add_new_edge(shallowerNode, node)
            #             self.graph['nodes'][node]['shallowQueue'].difference_update(
            #                 edgeIntersection)
            #             self.graph['nodes'][shallowerNode]['deepQueue'].difference_update(
            #                 edgeIntersection)

        pass

    # --------------- #
    #   HELPERS
    # --------------- #

    def add_triangle_to_new_node(self, interval, triangle):
        # self.graph['nodes'][str(self.nrNodes)] = {'region': tuple(interval), 'triangles': {
        #     tuple(self.pseudo_triangle(triangle))}, 'edges': set()}
        pseudoTriangle = tuple(self.pseudo_triangle(triangle))

        if len(self.availableNodeIds) == 0:
            nodeId = str(self.nrNodes)
        else:
            for idn in self.availableNodeIds:
                nodeId = idn
                self.availableNodeIds.discard(idn)
                break

        self.graph['nodes'][nodeId] = {'region': interval,
                                       'triangles': {pseudoTriangle},
                                       'deepNeighbors': set(),
                                       'shallowNeighbors': set(),
                                       'currentQueue': set(),
                                       'shallowQueue': set(),
                                       'deepQueue': set(),
                                       'classification': None,
                                       'full_area': None,
                                       'edges': [],
                                       'outer_boundary': None,
                                       'holes': []}
        self.nrNodes += 1
        # print('new node: ', nodeId)

        self.regionNodes[interval].add(nodeId)

        if pseudoTriangle in self.triangleInventory.keys():
            self.triangleInventory[pseudoTriangle].add(nodeId)
        else:
            self.triangleInventory[pseudoTriangle] = {nodeId}

        return nodeId

    def add_triangle_to_node(self, triangle, nodeId):
        pseudoTriangle = tuple(self.pseudo_triangle(triangle))
        self.graph['nodes'][nodeId]['triangles'].add(pseudoTriangle)

        if pseudoTriangle in self.triangleInventory.keys():
            self.triangleInventory[pseudoTriangle].add(nodeId)
        else:
            self.triangleInventory[pseudoTriangle] = {nodeId}

    def delete_triangle_from_node(self, triangle, nodeId):
        self.graph['nodes'][nodeId]['triangles'].discard(triangle)

    def add_triangle_to_queue(self, triangle, nodeId, type):
        queueType = type + 'Queue'
        self.graph['nodes'][nodeId][queueType].add(tuple(self.pseudo_triangle(triangle)))

    def remove_triangle_from_queue(self, triangle, nodeId, type):
        queueType = type + 'Queue'
        # try:
        #     self.graph['nodes'][nodeId][queueType].remove(tuple(self.pseudo_triangle(triangle)))
        # except:
        #     print('couldnt remove triangle')
        #     pass

        self.graph['nodes'][nodeId][queueType].discard(tuple(self.pseudo_triangle(triangle)))
        # self.graph['nodes'][nodeId][queueType].remove(tuple(self.pseudo_triangle(triangle)))

    def add_triangle_to_limit(self, triangle, nodeId, type):
        queueType = type + 'Neighbors'
        self.graph['nodes'][nodeId][queueType].add(tuple(self.pseudo_triangle(triangle)))

    def get_queue(self, nodeId, type):
        queueType = type + 'Queue'
        return self.graph['nodes'][nodeId][queueType]

    def get_interval_from_node(self, nodeId):
        return int(self.graph['nodes'][nodeId]['region'])

    def get_neighboring_nodes(self, nodeId, type):
        neighborType = type + 'Neighbors'
        return self.graph['nodes'][nodeId][neighborType]

    def get_triangles(self, nodeId):
        return self.graph['nodes'][nodeId]['triangles']

    def triangle_in_node(self, triangle, nodeId):
        if tuple(self.pseudo_triangle(triangle)) in self.graph['nodes'][nodeId]['triangles']:
            return True
        else:
            return False

    def is_node(self, nodeId):
        if nodeId in self.graph['nodes'].keys():
            return True
        else:
            return False

    def triangle_in_queue(self, triangle, nodeId, type):
        queueType = type + 'Queue'
        if tuple(self.pseudo_triangle(triangle)) in self.graph['nodes'][nodeId][queueType]:
            return True
        else:
            return False

    def add_new_edge(self, shallowNode, deepNode):

        if str(shallowNode) not in self.graph['nodes'][str(deepNode)]['shallowNeighbors'] and str(deepNode) not in self.graph['nodes'][str(shallowNode)]['deepNeighbors']:
            edgeId = str(self.nrEdges)
            self.graph['edges'][edgeId] = {}
            edge = self.graph['edges'][edgeId]

            edge['edge'] = [shallowNode, deepNode]
            self.graph['nodes'][str(shallowNode)]['deepNeighbors'].add(deepNode)
            self.graph['nodes'][str(deepNode)]['shallowNeighbors'].add(shallowNode)
            self.graph['nodes'][str(shallowNode)]['edges'].append(edgeId)
            self.graph['nodes'][str(deepNode)]['edges'].append(edgeId)
            edge['value'] = self.get_edge_value(edgeId)
            edge['closed'] = None
            edge['iso_area'] = None
            edge['bend_detector'] = None
            self.nrEdges += 1

    def get_edge_value(self, edgeId):
        nodeList = self.graph['edges'][edgeId]['edge']
        # print(nodeList)
        # print(nodeList[0])
        # print('regions: ', self.regions)
        # print(self.get_interval_from_node(nodeList[0]))
        regionsOne = self.regions[self.get_interval_from_node(nodeList[0])]
        regionsTwo = self.regions[self.get_interval_from_node(nodeList[1])]
        edgeValue = float(list(set(regionsOne).intersection(regionsTwo))[0])
        # print('EdgeValue: ', edgeValue)

        return edgeValue

    def get_edge_triangles(self, edgeId):
        # print(edgeId)
        nodeList = self.graph['edges'][edgeId]['edge']
        trianglesOne = self.get_triangles(nodeList[0])
        trianglesTwo = self.get_triangles(nodeList[1])
        return trianglesOne.intersection(trianglesTwo)

    def saddle_test(self, triangleOne, triangleTwo, interval):
        similarEdge = set(triangleOne).intersection(triangleTwo)
        region = self.regions[interval]  # 8-10 eg
        # print(similarEdge, interval, region)
        lower = 0
        higher = 0
        # print(region)
        for vertex in similarEdge:
            # print(self.get_z(vertex, True))
            if self.get_z(vertex, idOnly=True) <= region[0]:
                lower += 1
                # print(lower)
            elif self.get_z(vertex, idOnly=True) > region[1]:
                higher += 1
                # print(higher)
        if lower == 2 or higher == 2:
            # self.msg('SADDLE', 'warning')
            # print('t1: ', triangleOne)
            # for vId in triangleOne:
            #     print(self.triangulation.get_point(vId))
            # print('t2: ', triangleTwo)
            # for vId in triangleTwo:
            #     print(self.triangulation.get_point(vId))
            # print('saddle', interval)
            return True
        else:
            return False

    def get_all_nodes_in_interval(self, interval):
        return self.regionNodes[str(interval)]

    # ====================================== #
    #
    #   Isobaths
    #
    # ====================================== #

    def ___ISOBATHS___(self):
        # placeholder for Atom symbol-tree-view
        pass

    def generate_isobaths4(self, edgeIds=[]):
        if len(edgeIds) == 0:
            edgeIds = list(self.graph['edges'].keys())

        for edge in edgeIds:
            # self.msg('--new edge', 'header')
            isoValue = self.graph['edges'][edge]['value']
            # print('isoValue: ', isoValue, self.graph['edges'][edge]['edge'], edge)

            edgeTriangles = self.get_edge_triangles(edge)
            # print('len: ', len(edgeTriangles))

            isobathSegments = set()

            for triangle in edgeTriangles:
                # triangleContour = ['start', 'end']
                intersections, isPoint = self.triangle_intersections(triangle, isoValue)
                # triangleMin, triangleMax = self.minmax_from_triangle(triangle)

                if intersections == 3:
                    # should not happen
                    continue
                elif isPoint:
                    # print('IM A POINT')
                    continue
                else:
                    triangleSegment = ['start', 'end']
                    if intersections == 0:
                        # full intersection
                        for i in range(3):
                            segment = (triangle[i], triangle[(i + 1) % 3])
                            zOne = self.get_z(segment[0], idOnly=True)
                            zTwo = self.get_z(segment[1], idOnly=True)
                            if min(zOne, zTwo) < isoValue < max(zOne, zTwo):
                                if zOne > zTwo:
                                    # deep is on the left
                                    triangleSegment[0] = segment
                                else:
                                    triangleSegment[1] = segment
                        # print(triangleSegment, tuple(triangleSegment))
                        isobathSegments.add(tuple(triangleSegment))
                    elif intersections == 1:
                        # point to edge or edge to point
                        # print('IM A SEMI')
                        for i in range(3):
                            segment = (triangle[i], triangle[(i + 1) % 3])
                            zOne = self.get_z(segment[0], idOnly=True)
                            zTwo = self.get_z(segment[1], idOnly=True)
                            if min(zOne, zTwo) < isoValue < max(zOne, zTwo):
                                if zOne > zTwo:
                                    # deep is on the left
                                    triangleSegment[0] = segment
                                else:
                                    triangleSegment[1] = segment
                            elif zOne == isoValue and zOne < zTwo:
                                triangleSegment[1] = (segment[0])
                            elif zOne == isoValue and zOne > zTwo:
                                triangleSegment[0] = (segment[0])
                        # print(triangleSegment)
                        isobathSegments.add(tuple(triangleSegment))

                    elif intersections == 2:
                        # edge
                        # print('IM AN EDGE')
                        for i in range(3):
                            segment = (triangle[i], triangle[(i + 1) % 3])
                            zOne = self.get_z(segment[0], idOnly=True)
                            zTwo = self.get_z(segment[1], idOnly=True)
                            if zOne == isoValue and zTwo != isoValue:
                                if zTwo < isoValue:
                                    triangleSegment[0] = (segment[0])
                                elif zTwo > isoValue:
                                    triangleSegment[1] = (segment[0])
                            elif zTwo == isoValue and zOne != isoValue:
                                if zOne > isoValue:
                                    triangleSegment[0] = (segment[1])
                                elif zOne < isoValue:
                                    triangleSegment[1] = (segment[1])
                        isobathSegments.add(tuple(triangleSegment))
                        # print((triangleSegment))

            #
            # # self.msg('> exporting shapefiles...', 'info')
            # shpName = edge
            # pointShpName = 'isobathsegments_{}_{}.shp'.format(shpName, self.now())
            # pointShpFile = os.path.join(os.getcwd(), 'projects', self.projectName, pointShpName)
            # print('isobathsegmentsPoints file: ', pointShpFile)
            #
            # with shapefile.Writer(pointShpFile) as wp:
            #     wp.field('depth', 'F', decimal=4)
            #     wp.field('id', 'N')
            #     wp.field('segment', 'C')
            #     # for point in self.triangulation.all_vertices()[1:]:
            #     for i, segment in enumerate(isobathSegments):
            #         for seg in segment:
            #             if type(seg) == int:
            #                 point = self.triangulation.get_point(seg)
            #                 wp.point(point[0], point[1])
            #                 wp.record(point[2], seg, str(segment))
            #             elif type(seg) == tuple:
            #                 for p in seg:
            #                     point = self.triangulation.get_point(p)
            #                     wp.point(point[0], point[1])
            #                     wp.record(point[2], p, str(segment))
            #     self.msg('> isosegments written to shapefile', 'info')

            forwardPath = []
            backwardPath = []
            for path in isobathSegments:
                break
            isobathSegments.remove(path)
            forwardPath.append(path[1])
            backwardPath.append(path[0])

            i = 0
            finished = False
            while not finished:
                # i = 0
                p = 0

                # print('==NEW LOOP==')
                # print(len(isobathSegments))
                # print('FPath-1: ', forwardPath[-1])
                # print('BPath-1: ', backwardPath[-1])
                # print('fpathfull: ', forwardPath)
                # print('bpathfull: ', backwardPath)
                # print('isobathSegments: ', isobathSegments)

                for seg in isobathSegments.copy():

                    # FPath-1:  (3162, 4261)
                    # BPath-1:  (1820, 693)
                    # print('new seg: ', seg)
                    # print(forwardPath[-1], backwardPath[-1], seg)
                    # print(seg)

                    # if type(forwardPath[-1]) == int or type(seg[0]) == int:
                    #     print('Fpath[-1]: ', forwardPath[-1])
                    #     print('seg: ', seg, 'seg[0]: ', seg[0], 'seg[1]: ', seg[1])
                    #     if forwardPath[-1] == seg[0]:
                    #         # print('forward add')
                    #         forwardPath.append(seg[1])
                    #         isobathSegments.remove(seg)
                    #
                    # elif type(backwardPath[-1]) == int or type(seg[-1]) == int:
                    #     print('Bpath[-1]: ', forwardPath[-1])
                    #     print('seg: ', seg, 'seg[0]: ', seg[0], 'seg[1]: ', seg[1])
                    #     if backwardPath[-1] == seg[1]:
                    #         # print('backward add')
                    #         backwardPath.append(seg[0])
                    #         isobathSegments.remove(seg)
                    '''
                    if type(backwardPath[-1]) == type(seg[1]) == int:
                        if backwardPath[-1] == seg[1]:
                            backwardPath.append(seg[0])
                            isobathSegments.remove(seg)
                    elif type(backwardPath[-1]) == type(seg[1]) == tuple:
                        if len(set(backwardPath[-1]).intersection(seg[1])) == 2:
                            backwardPath.append(seg[0])
                            isobathSegments.remove(seg)

                    elif type(forwardPath[-1]) == type(seg[0]) == int:
                        # print('FPath: ', forwardPath[-1], 'seg: ', seg[0])
                        if forwardPath[-1] == seg[0]:
                            forwardPath.append(seg[1])
                            isobathSegments.remove(seg)
                    elif type(forwardPath[-1]) == type(seg[0]) == tuple:
                        if len(set(forwardPath[-1]).intersection(seg[0])) == 2:
                            forwardPath.append(seg[1])
                            isobathSegments.remove(seg)
                    '''

                    if type(seg[0]) != int and type(seg[1]) != int and type(forwardPath[-1]) != int and type(backwardPath[-1]) != int:
                        if len(set(forwardPath[-1]).intersection(seg[0])) == 2:
                            forwardPath.append(seg[1])
                            # print('forward add')
                            isobathSegments.remove(seg)
                        elif len(set(backwardPath[-1]).intersection(seg[1])) == 2:
                            backwardPath.append(seg[0])
                            # print('backward add')
                            isobathSegments.remove(seg)
                    else:
                        # print('Fpath[-1]: ', forwardPath[-1])
                        # print('seg: ', seg, 'seg[0]: ', seg[0], 'seg[1]: ', seg[1])
                        if forwardPath[-1] == seg[0]:
                            # print('forward add')
                            forwardPath.append(seg[1])
                            isobathSegments.remove(seg)
                        elif type(forwardPath[-1]) == type(seg[0]) and type(seg[0]) != int:
                            if len(set(forwardPath[-1]).intersection(seg[0])) == 2:
                                forwardPath.append(seg[1])
                                # print('forward add')
                                isobathSegments.remove(seg)
                        # elif len(set(forwardPath[-1]).intersection(seg[0])) == 2:
                        #     forwardPath.append(seg[1])
                        #     # print('forward add')
                        #     isobathSegments.remove(seg)

                        # print('Bpath[-1]: ', forwardPath[-1])
                        # print('seg: ', seg, 'seg[0]: ', seg[0], 'seg[1]: ', seg[1])
                        if backwardPath[-1] == seg[1]:
                            # print('backward add')
                            backwardPath.append(seg[0])
                            isobathSegments.remove(seg)
                        elif type(backwardPath[-1]) == seg[1]:
                            if len(set(backwardPath[-1]).intersection(seg[1])) == 2 and type(seg[1]) != int:
                                backwardPath.append(seg[0])
                                # print('backward add')
                                isobathSegments.remove(seg)

                # print('edge', edge, 'lenIso', len(isobathSegments))
                i += 1
                p += 1

                if len(isobathSegments) == 0:
                    # print(len(forwardPath), len(backwardPath))
                    # print(forwardPath)
                    # print(backwardPath)
                    finished = True
                else:
                    if type(forwardPath[-1]) == type(backwardPath[-1]) == int:
                        if forwardPath[-1] == backwardPath[-1]:
                            # print('closed line trigger')
                            self.errors.append(
                                '{} generate_isobaths4\tclosed line trigger\tedge: {}\tisoValue: {}'.format(self.now(), edge, isoValue))
                            finished = True
                    elif type(forwardPath[-1]) == type(backwardPath[-1]) == tuple:
                        if min(forwardPath[-1]) == min(backwardPath[-1]) and max(forwardPath[-1]) == max(backwardPath[-1]):
                            # print('closed line trigger')
                            self.errors.append(
                                '{} generate_isobaths4\tclosed line trigger\tedge: {}\tisoValue: {}'.format(self.now(), edge, isoValue))
                            finished = True

                if i > 100000:
                    # self.msg('longer trigger', 'warning')
                    # print(len(forwardPath), len(backwardPath))
                    self.errors.append(
                        '{} generate_isobaths4\tlonger trigger\tedge: {}\tisoValue: {}'.format(self.now(), edge, isoValue))
                    finished = True

            if len(isobathSegments):
                # self.msg('> exporting shapefiles...', 'info')
                shpName = edge
                pointShpName = 'isobathsegments_{}_{}.shp'.format(shpName, self.now())
                pointShpFile = os.path.join(os.getcwd(), 'projects', self.projectName, pointShpName)
                # print('invalid/missing isobathsegmentsPoints file: ', pointShpFile)

                with shapefile.Writer(pointShpFile) as wp:
                    wp.field('depth', 'F', decimal=4)
                    wp.field('id', 'N')
                    wp.field('segment', 'C')
                    # for point in self.triangulation.all_vertices()[1:]:
                    for i, segment in enumerate(isobathSegments):
                        for seg in segment:
                            if type(seg) == int:
                                point = self.triangulation.get_point(seg)
                                wp.point(point[0], point[1])
                                wp.record(point[2], seg, str(segment))
                            elif type(seg) == tuple:
                                for p in seg:
                                    point = self.triangulation.get_point(p)
                                    wp.point(point[0], point[1])
                                    wp.record(point[2], p, str(segment))
                    # self.msg('> invalid/missing isosegments written to shapefile', 'warning')
                self.errors.append(
                    '{} generate_isobaths4\tinvalid/missing isobathsegments\t edge: {}\t isovalue: {}\n\tinvalid segments written to: {}'.format(self.now(), edge, isoValue, pointShpFile))

            backwardPath.reverse()
            fullPath = backwardPath + forwardPath
            # print(fullPath[0], fullPath[-1])

            if type(fullPath[0]) == type(fullPath[-1]) == int:
                if fullPath[0] == fullPath[-1]:
                    self.graph['edges'][edge]['closed'] = True
                else:
                    self.graph['edges'][edge]['closed'] = False
            elif type(fullPath[0]) == type(fullPath[-1]) == tuple:
                if min(fullPath[0]) == min(fullPath[-1]) and max(fullPath[0]) == max(fullPath[-1]):
                    self.graph['edges'][edge]['closed'] = True
                else:
                    self.graph['edges'][edge]['closed'] = False

            # if min(fullPath[0]) == min(fullPath[-1]) and max(fullPath[0]) == max(fullPath[-1]):
            #     self.graph['edges'][edge]['closed'] = True
            # else:
            #     self.graph['edges'][edge]['closed'] = False
            # print(fullPath)

            isoGeom = []
            for intersection in fullPath:
                # print(intersection)
                if type(intersection) == int:
                    geom = self.triangulation.get_point(intersection)
                    isoGeom.append([geom[0], geom[1]])
                else:
                    geomOne = self.triangulation.get_point(intersection[0])
                    geomTwo = self.triangulation.get_point(intersection[1])
                    xOne, yOne, zOne = geomOne[0], geomOne[1], self.get_z(
                        intersection[0], idOnly=True)
                    xTwo, yTwo, zTwo = geomTwo[0], geomTwo[1], self.get_z(
                        intersection[1], idOnly=True)
                    if xOne == xTwo:
                        x = round(xOne, 3)
                        y = round(yOne + ((isoValue-zOne)/(zTwo-zOne)) * (yTwo-yOne), 3)
                    else:
                        x = round((isoValue*xTwo-isoValue*xOne-zOne*xTwo+zTwo*xOne)/(zTwo-zOne), 3)
                        y = round((x*(yTwo-yOne)-xOne*yTwo+xTwo*yOne)/(xTwo-xOne), 3)
                    isoGeom.append([x, y])

            self.graph['edges'][edge]['geom'] = isoGeom

    def generate_isobaths5(self, edgeIds=[]):  # ['6', '10', '22', '29']):
        # self.print_graph()
        if len(edgeIds) == 0:
            edgeIds = list(self.graph['edges'].keys())

        for edge in edgeIds:
            # self.msg('--new edge', 'header')
            edgeObject = self.graph['edges'][edge]
            isoValue = edgeObject['value']
            # print('isoValue: ', isoValue, edgeObject['edge'], edge)
            # print('isoValue: ', isoValue, edge)

            edgeTriangles = self.get_edge_triangles(edge)

            # print(len(edgeTriangles))

            # create some data entries in the edge
            # { '1': { 'triangle': (tvId1, tvId2, tvId3),
            #          'segment': ((ivX, ivY), (ivX, ivY)) },
            #   '2': { 'triangle': (tvId1, tvId2, tvId3),
            #          'segment': ((ivX, ivY), (ivX, ivY)) },
            #   '3': ...
            # }
            edgeObject['ordered_triangles'] = {}
            # { (ivX, ivY): ['1', '5'],
            #   (ivX, ivY): ['2'],
            #   ...
            # }
            edgeObject['iso_vertex_pointers'] = {}
            triangleCounter = 0
            indexedTriangles = set()

            # get a starting triangle
            pikol = 0
            for triangle in edgeTriangles:
                pikol += 1
                intersections, isPoint = self.triangle_intersections(triangle, isoValue)
                if not isPoint:
                    break
                # TODO: throw error and skip this isobath, probably a sounding

            finished = False
            backwardSearch = False
            iterations = 0
            while not finished:

                # print('newwhile')

                triangleCopy = triangle

                intersections, isPoint = self.triangle_intersections(triangle, isoValue)
                # print('triangle: ', triangle, intersections, isPoint)
                triangleSegment = ['start', 'end']
                trianglePoint = None

                # probably remove this option, handling it in NEXT or PREVIOUS triangle
                # if isPoint:
                #     # not handling as segment
                #     # but still inventorize the triangle itself
                #     print('POINT')
                #     for vId in triangle:
                #         vertexElevation = self.get_z(vId, idOnly=True)
                #         if vertexElevation == isoValue:
                #             trianglePoint = vId

                if intersections == 0:
                    # print('FULL')
                    # full intersection
                    for i in range(3):
                        segment = (triangle[i], triangle[(i + 1) % 3])
                        zOne = self.get_z(segment[0], idOnly=True)
                        zTwo = self.get_z(segment[1], idOnly=True)
                        if min(zOne, zTwo) < isoValue < max(zOne, zTwo):
                            if zOne > zTwo:
                                # deep is on the left
                                triangleSegment[0] = segment
                            else:
                                triangleSegment[1] = segment  # or elif

                elif intersections == 1:
                    # print('SEMI')
                    # point to edge or edge to point
                    for i in range(3):
                        segment = (triangle[i], triangle[(i + 1) % 3])
                        zOne = self.get_z(segment[0], idOnly=True)
                        zTwo = self.get_z(segment[1], idOnly=True)
                        if min(zOne, zTwo) < isoValue < max(zOne, zTwo):
                            if zOne > zTwo:
                                # deep is on the left
                                triangleSegment[0] = segment
                            else:
                                triangleSegment[1] = segment
                        elif zOne == isoValue and zOne < zTwo:
                            triangleSegment[1] = (segment[0])
                        elif zOne == isoValue and zOne > zTwo:
                            triangleSegment[0] = (segment[0])

                elif intersections == 2:
                    # print('EDGE')
                    # edge
                    for i in range(3):
                        segment = (triangle[i], triangle[(i + 1) % 3])
                        zOne = self.get_z(segment[0], idOnly=True)
                        zTwo = self.get_z(segment[1], idOnly=True)
                        if zOne == isoValue and zTwo != isoValue:
                            if zTwo < isoValue:
                                triangleSegment[0] = (segment[0])
                            elif zTwo > isoValue:
                                triangleSegment[1] = (segment[0])
                        elif zTwo == isoValue and zOne != isoValue:
                            if zOne > isoValue:
                                triangleSegment[0] = (segment[1])
                            elif zOne < isoValue:
                                triangleSegment[1] = (segment[1])

                elif intersections == 3:
                    # not handling horizontal triangles
                    # print('HORIZONTAL')
                    continue

                ####
                # print('triangleSegment: ', triangleSegment)

                # adding to content
                # if trianglePoint:  # is not None:
                #     triangleCounter += 1
                #     edgeObject['ordered_triangles'][str(triangleCounter)] = {'triangle': triangle,
                #                                                              'segment': None,
                #                                                              'tri_segment': None}
                #     isoVertexPointers = edgeObject['iso_vertex_pointers']
                #     geom = self.triangulation.get_point(trianglePoint)
                #     if tuple(geom) in isoVertexPointers:
                #         isoVertexPointers[tuple(geom)].append(triangle)
                #     else:
                #         isoVertexPointers[tuple(geom)] = [triangle]

                # moved below piece into forwardsearch:
                # if not trianglePoint:
                #     triangleCounter += 1
                #     isoVertexPointers = edgeObject['iso_vertex_pointers']
                #
                #     lineGeom = self.lineseg_from_vertices(triangleSegment, isoValue)
                #     # print(lineGeom)
                #
                #     edgeObject['ordered_triangles'][str(triangleCounter)] = {'triangle': triangle,
                #                                                              'segment': tuple(lineGeom),
                #                                                              'tri_segment': triangleSegment}
                #     for geom in lineGeom:
                #         if geom in isoVertexPointers:
                #             isoVertexPointers[geom].append(triangle)
                #         else:
                #             isoVertexPointers[geom] = [triangle]
                #
                # indexedTriangles.add(triangle)

                if not backwardSearch:  # forward search

                    if not trianglePoint:
                        triangleCounter += 1
                        isoVertexPointers = edgeObject['iso_vertex_pointers']

                        lineGeom = self.lineseg_from_vertices(triangleSegment, isoValue)
                        # print(lineGeom)

                        edgeObject['ordered_triangles'][str(triangleCounter)] = {'triangle': triangle,
                                                                                 'segment': tuple(lineGeom),
                                                                                 'tri_segment': triangleSegment}
                        for geom in lineGeom:
                            if geom in isoVertexPointers:
                                isoVertexPointers[geom].append(triangle)
                            else:
                                isoVertexPointers[geom] = [triangle]

                    indexedTriangles.add(triangle)

                    # print('forward search: ', triangleSegment, triangleSegment[1])
                    if type(triangleSegment[1]) == int:
                        # ending in a vertex
                        # print('\ntype is int')
                        incidentTriangles = self.triangulation.incident_triangles_to_vertex(
                            triangleSegment[1])
                        incidentTriangles = [tuple(self.pseudo_triangle(tri))
                                             for tri in incidentTriangles]

                        # now first add all incident triangles a POINT and last find the edge
                        for incTriangle in incidentTriangles:
                            # print(incTriangle)

                            if incTriangle in indexedTriangles:
                                continue

                            if incTriangle not in edgeTriangles:
                                continue

                            # print('inctri: ', incTriangle)

                            intersections, isPoint = self.triangle_intersections(
                                incTriangle, isoValue)
                            if isPoint:
                                # print('also point')
                                for vId in incTriangle:
                                    vertexElevation = self.get_z(vId, idOnly=True)
                                    if vertexElevation == isoValue:
                                        trianglePoint = vId

                                indexedTriangles.add(incTriangle)
                                triangleCounter += 1
                                edgeObject['ordered_triangles'][str(triangleCounter)] = {'triangle': incTriangle,
                                                                                         'segment': None,
                                                                                         'tri_segment': None}
                                isoVertexPointers = edgeObject['iso_vertex_pointers']
                                geom = self.triangulation.get_point(trianglePoint)
                                geom = (geom[0], geom[1])
                                # print('inctri samepoint:', geom)
                                if tuple(geom) in isoVertexPointers:
                                    isoVertexPointers[geom].append(incTriangle)
                                else:
                                    isoVertexPointers[geom] = [incTriangle]

                            else:
                                triangle = incTriangle

                            # print(isoVertexPointers[tuple(geom)])

                    else:
                        # ending in an edge
                        # print('type is edge')
                        adjacentTriangles = self.adjacent_triangles(triangle)
                        for adjTriangle in adjacentTriangles:

                            if len(set(adjTriangle).intersection(triangleSegment[1])) != 2:
                                continue
                            if adjTriangle == triangle:
                                continue
                            if adjTriangle not in edgeTriangles:
                                # impossible??
                                continue
                            if adjTriangle in indexedTriangles:
                                continue

                            triangle = adjTriangle

                # backwardsearch
                elif backwardSearch:  # backward search
                    if not trianglePoint:
                        triangleCounter -= 1
                        isoVertexPointers = edgeObject['iso_vertex_pointers']

                        lineGeom = self.lineseg_from_vertices(triangleSegment, isoValue)
                        # print(lineGeom)

                        edgeObject['ordered_triangles'][str(triangleCounter)] = {'triangle': triangle,
                                                                                 'segment': tuple(lineGeom),
                                                                                 'tri_segment': triangleSegment}
                        for geom in lineGeom:
                            if geom in isoVertexPointers:
                                isoVertexPointers[geom].append(triangle)
                            else:
                                isoVertexPointers[geom] = [triangle]

                    indexedTriangles.add(triangle)

                    # print('backward search: ', triangleSegment, triangleSegment[0])
                    # try:
                    #     for pointy in triangleSegment[0]:
                    #         # print('coord: ', self.triangulation.get_point(pointy))
                    # except:
                    #     print('coord: ', self.triangulation.get_point(triangleSegment[0]))

                    if type(triangleSegment[0]) == int:
                        # ending in a vertex
                        # print('type is int')
                        incidentTriangles = self.triangulation.incident_triangles_to_vertex(
                            triangleSegment[0])
                        incidentTriangles = [tuple(self.pseudo_triangle(tri))
                                             for tri in incidentTriangles]

                        # now first add all incident triangles a POINT and last find the edge
                        for incTriangle in incidentTriangles:

                            if incTriangle in indexedTriangles:
                                continue

                            if incTriangle not in edgeTriangles:
                                continue

                            intersections, isPoint = self.triangle_intersections(
                                incTriangle, isoValue)
                            if isPoint:
                                for vId in incTriangle:
                                    vertexElevation = self.get_z(vId, idOnly=True)
                                    if vertexElevation == isoValue:
                                        trianglePoint = vId

                                indexedTriangles.add(incTriangle)
                                triangleCounter -= 1
                                edgeObject['ordered_triangles'][str(triangleCounter)] = {'triangle': incTriangle,
                                                                                         'segment': None,
                                                                                         'tri_segment': None}
                                isoVertexPointers = edgeObject['iso_vertex_pointers']
                                geom = self.triangulation.get_point(trianglePoint)
                                geom = (geom[0], geom[1])
                                if tuple(geom) in isoVertexPointers:
                                    isoVertexPointers[geom].append(incTriangle)
                                else:
                                    isoVertexPointers[geom] = [incTriangle]

                            else:
                                triangle = incTriangle

                    else:
                        # ending in an edge
                        # print('type is edge')
                        adjacentTriangles = self.adjacent_triangles(triangle)
                        for adjTriangle in adjacentTriangles:
                            # print('adjTriangle: ', adjTriangle)

                            if len(set(adjTriangle).intersection(triangleSegment[0])) != 2:
                                # print('not on the shared edge')
                                continue
                            if adjTriangle == triangle:
                                # print('same triangle')
                                continue
                            if adjTriangle not in edgeTriangles:
                                # impossible??
                                # print('not in edge')
                                continue
                            if adjTriangle in indexedTriangles:
                                # print('already indexed')
                                continue

                            triangle = adjTriangle

                # managing while loop
                if len(indexedTriangles) >= len(edgeTriangles):
                    # print('all triangles visited')
                    finished = True

                    if backwardSearch is False:
                        minTriangleId = 1
                        maxTriangleId = triangleCounter
                    else:
                        minTriangleId = triangleCounter
                    break

                iterations += 0
                if iterations > 1000:
                    # print('exceeded iteration limit')
                    finished = True

                if triangleCopy == triangle and backwardSearch is False:
                    # print('no new triangle found! swtiching to backwardsearch\n')
                    # finished = True
                    maxTriangleId = triangleCounter
                    backwardSearch = True
                    triangleCounter = 1
                    triangleObject = edgeObject['ordered_triangles']['1']
                    firstTriangle = triangleObject['triangle']
                    # print('firstTriangle: ', firstTriangle)
                    firstTriangleSegment = triangleObject['tri_segment']

                    # searching first previous
                    if type(firstTriangleSegment[0]) == int:
                        # ending in a vertex
                        # print('type is int')
                        incidentTriangles = self.triangulation.incident_triangles_to_vertex(
                            firstTriangleSegment[0])
                        incidentTriangles = [tuple(self.pseudo_triangle(tri))
                                             for tri in incidentTriangles]

                        # now first add all incident triangles a POINT and last find the edge
                        for incTriangle in incidentTriangles:

                            if incTriangle in indexedTriangles:
                                continue

                            if incTriangle not in edgeTriangles:
                                continue

                            intersections, isPoint = self.triangle_intersections(
                                incTriangle, isoValue)
                            if isPoint:
                                for vId in incTriangle:
                                    vertexElevation = self.get_z(vId, idOnly=True)
                                    if vertexElevation == isoValue:
                                        trianglePoint = vId

                                indexedTriangles.add(incTriangle)
                                triangleCounter -= 1
                                edgeObject['ordered_triangles'][str(triangleCounter)] = {'triangle': incTriangle,
                                                                                         'segment': None,
                                                                                         'tri_segment': None}
                                isoVertexPointers = edgeObject['iso_vertex_pointers']
                                geom = self.triangulation.get_point(trianglePoint)
                                geom = (geom[0], geom[1])

                                if tuple(geom) in isoVertexPointers:
                                    isoVertexPointers[geom].append(incTriangle)
                                else:
                                    isoVertexPointers[geom] = [incTriangle]

                            else:
                                triangle = incTriangle

                    else:
                        # ending in an edge
                        # print('type is edge')
                        adjacentTriangles = self.adjacent_triangles(firstTriangle)
                        for adjTriangle in adjacentTriangles:

                            if len(set(adjTriangle).intersection(firstTriangleSegment[0])) != 2:
                                continue
                            if adjTriangle == firstTriangle:
                                continue
                            if adjTriangle not in edgeTriangles:
                                # impossible??
                                continue
                            if adjTriangle in indexedTriangles:
                                continue

                            triangle = adjTriangle
                            # print('new tri for bwsearch: ', triangle)

                if triangleCopy == triangle and backwardSearch:
                    # print('no new triangle found, open isobath')
                    edgeObject['closed'] = False
                    finished = True
                    minTriangleId = triangleCounter

            # print(edgeObject['ordered_triangles'].keys())
            # print('min: {}  max: {}'.format(minTriangleId, maxTriangleId))
            edgeObject['minmax_order'] = [minTriangleId, maxTriangleId]

            startFalse = True
            while startFalse:
                if edgeObject['ordered_triangles'][str(minTriangleId)]['tri_segment']:
                    startFalse = False
                else:
                    print('non valid start segment')
                    minTriangleId = minTriangleId + 1
            endFalse = True
            while endFalse:
                if edgeObject['ordered_triangles'][str(maxTriangleId)]['tri_segment']:
                    endFalse = False
                else:
                    print('non valid end segment')
                    maxTriangleId = maxTriangleId - 1
            startSegment = edgeObject['ordered_triangles'][str(minTriangleId)]['tri_segment'][0]
            endSegment = edgeObject['ordered_triangles'][str(maxTriangleId)]['tri_segment'][1]
            # print(startSegment, endSegment)
            # print(startSegment == endSegment)
            # print(startSegment == reversed(endSegment))
            edgeObject['closed'] = self.is_closed_isobath(startSegment, endSegment)
            # print('closed: ', edgeObject['closed'])

            self.create_simple_iso_geom(edge)
            self.compute_isobath_area(edgeIds=[edge])

            if not edgeObject['closed']:
                # print('not closed isobath, checking convex hull')

                # print(startSegment, endSegment)

                if type(startSegment) == int:
                    # print(self.triangulation.is_vertex_convex_hull(startSegment))
                    pass
                else:
                    # print('first ', self.triangulation.is_vertex_convex_hull(startSegment[0]))
                    # print('second ', self.triangulation.is_vertex_convex_hull(startSegment[1]))
                    pass
                if type(endSegment) == int:
                    # print(self.triangulation.is_vertex_convex_hull(endSegment))
                    pass
                else:
                    # print('first ', self.triangulation.is_vertex_convex_hull(endSegment[0]))
                    # print('second ', self.triangulation.is_vertex_convex_hull(endSegment[1]))
                    pass

    def create_simple_iso_geom(self, edgeId):
        edgeObject = self.graph['edges'][edgeId]
        orderedTriangles = edgeObject['ordered_triangles']
        # closed = edgeObject['closed']
        # geom = edgeObject['iso_geom']
        # print(geom)
        simpleGeom = []

        minTri, maxTri = edgeObject['minmax_order']
        # print(minTri, maxTri)

        firstPoint = orderedTriangles[str(minTri)]['segment'][0]
        simpleGeom.append(list(firstPoint))
        for triangleNumber in range(minTri, maxTri+1):
            segment = orderedTriangles[str(triangleNumber)]['segment']
            if segment:
                simpleGeom.append(list(segment[1]))
        # print(simpleGeom)

        edgeObject['geom'] = simpleGeom

    def is_closed_isobath(self, start_seg, end_seg):

        if type(start_seg) == type(end_seg) == int:
            if start_seg == end_seg:
                return True
            else:
                return False

        elif type(start_seg) == type(start_seg) == tuple:
            if min(start_seg) == min(end_seg) and max(start_seg) == max(end_seg):
                return True
            else:
                return False

        else:
            return False

    def lineseg_from_vertices(self, vertex_list, isoValue):

        # print(vertex_list)
        lineGeom = []

        for intersection in vertex_list:

            # print(intersection)
            if type(intersection) == int:
                geom = self.triangulation.get_point(intersection)
                lineGeom.append((geom[0], geom[1]))
            else:
                geomOne = self.triangulation.get_point(intersection[0])
                geomTwo = self.triangulation.get_point(intersection[1])
                xOne, yOne, zOne = geomOne[0], geomOne[1], self.get_z(
                    intersection[0], idOnly=True)
                xTwo, yTwo, zTwo = geomTwo[0], geomTwo[1], self.get_z(
                    intersection[1], idOnly=True)
                if xOne == xTwo:
                    x = round(xOne, 3)
                    y = round(yOne + ((isoValue-zOne)/(zTwo-zOne)) * (yTwo-yOne), 3)
                else:
                    x = round((isoValue*xTwo-isoValue*xOne-zOne*xTwo+zTwo*xOne)/(zTwo-zOne), 3)
                    y = round((x*(yTwo-yOne)-xOne*yTwo+xTwo*yOne)/(xTwo-xOne), 3)
                lineGeom.append((x, y))

        return lineGeom

    def triangle_intersections(self, triangle, isoValue):
        isPoint = False
        intersections = 0
        for vId in triangle:
            vertexElevation = self.get_z(vId, idOnly=True)
            if vertexElevation == isoValue:
                intersections += 1

        if intersections == 1:
            triangleMin, triangleMax = self.minmax_from_triangle(triangle)
            if triangleMin == isoValue or triangleMax == isoValue:
                isPoint = True

        return intersections, isPoint

    def generate_depth_areas_nonclosed(self, nodeIds=[]):
        self.msg('> generating depth areas...', 'header')
        if nodeIds == []:
            nodeIds = self.graph['nodes'].keys()

        for nodeId in nodeIds:
            print(nodeId)
            node = self.graph['nodes'][nodeId]
            nodeEdgeIds = node['edges']

            for nodeEdgeId in nodeEdgeIds:
                edge = self.graph['edges'][nodeEdgeId]
                print(nodeEdgeId, edge['closed'])

                if edge['closed'] is not True:
                    closeShallow = False
                    closeDeep = False

                    # edge['edge'] # [shallowNode, deepNode]
                    if edge['edge'].index(nodeId) == 0:
                        # node is the shallow node
                        closeShallow = True
                    elif edge['edge'].index(nodeId) == 1:
                        # node is the deeper side of the edge
                        closeDeep = True

                    startPoint = edge['geom'][0]
                    endPoint = edge['geom'][-1]

                    startTri = self.triangulation.locate(startPoint[0], startPoint[1])
                    endTri = self.triangulation.locate(endPoint[0], endPoint[1])

                    startVertices = []
                    endVertices = []
                    for v in startTri:
                        if self.triangulation.is_vertex_convex_hull(v):
                            startVertices.append(v)
                    startDepths = [self.get_z(vertex, idOnly=True) for vertex in startVertices]

                    for v in endTri:
                        if self.triangulation.is_vertex_convex_hull(v):
                            endVertices.append(v)
                    endDepths = [self.get_z(vertex, idOnly=True) for vertex in endVertices]

                    # print(self.triangulation.is_vertex(startPoint[0], startPoint[1]))
                    print(startPoint, endPoint)
                    print(startTri, endTri)
                    print(startVertices, endVertices)
                    print(self.triangulation.convex_hull())

    def generate_depth_areas(self, nodeIds=[]):
        self.msg('> generating depth areas...', 'header')

        # self.print_graph()

        depare_areas_current = {'total': 0.0, 'regions': []}

        for r in self.regions:
            depare_areas_current['regions'].append(0.0)

        if nodeIds == []:
            nodeIds = self.graph['nodes'].keys()

        computedEdges = set()

        for nodeId in nodeIds:
            nonClosed = False

            boundaryArea = -1.0
            outerBoundary = None
            innerHoles = []

            node = self.graph['nodes'][nodeId]
            node['boundary_area'] = 0.0
            # interval = self.get_interval_from_node(nodeId)
            # region = self.regions[interval]
            nodeEdgeIds = node['edges']
            # print('nodeedges: ', nodeId, nodeEdgeIds)
            if len(nodeEdgeIds) == 0:
                self.msg('> buggy node detected! nodeId: {}'.format(nodeId), 'warning')
                continue
            # print('----new node ', nodeId, nodeEdgeIds)

            for edgeId in nodeEdgeIds:
                edge = self.graph['edges'][edgeId]

                # print('depare: ', nodeId, edgeId)

                if not edge['closed']:
                    nonClosed = True
                    break

                if edgeId not in computedEdges:
                    self.compute_isobath_area(edgeIds=[edgeId])
                    computedEdges.add(edgeId)
                fullIsoArea = edge['iso_area']

                if fullIsoArea > boundaryArea:
                    if outerBoundary is not None:
                        innerHoles.append(outerBoundary)
                    # outerBoundary = edge['geom']
                    outerBoundary = edgeId
                    boundaryArea = fullIsoArea
                else:
                    # innerHoles.append(edge['geom'])
                    innerHoles.append(edgeId)

            if nonClosed:
                continue

            node['outer_boundary'] = outerBoundary
            node['holes'] = innerHoles

            # print(len(outerBoundary), len(innerHoles))
            # print(outerBoundary)

            # print('area')
            edges = self.graph['edges']
            bArea = edges[outerBoundary]['iso_area']
            # print('boundary ', bArea)
            hArea = 0.0
            for hole in innerHoles:
                cArea = edges[hole]['iso_area']
                hArea += cArea
            #     print(cArea)
            # print('holes ', hArea)
            # print('total:', round(bArea - hArea, 3))

            totalArea = round(bArea - hArea, 3)
            node['boundary_area'] = bArea
            regionIndex = self.get_interval_from_node(nodeId)

            depare_areas_current['regions'][regionIndex] = round(
                totalArea + depare_areas_current['regions'][regionIndex], 3)
            depare_areas_current['total'] = round(totalArea + depare_areas_current['total'], 3)

        # print(self.depare_areas['total'])
        # print(self.depare_areas)

        totalArea = depare_areas_current['total']
        for regionArea in depare_areas_current['regions']:
            # print(round(regionArea/totalArea * 100, 2))
            pass

        # self.depare_areas.append(depare_areas_current)
        self.depare_areas = depare_areas_current

        return depare_areas_current

    # ====================================== #
    #
    #   Interpolation
    #
    # ====================================== #

    def ___INTERPOLATION___(self):
        # placeholder for Atom symbol-tree-view
        pass

    def get_vertices_around_point(self, point_tuple, rings=3):
        locatedTriangle = tuple(self.pseudo_triangle(
            self.triangulation.locate(point_tuple[0], point_tuple[1])))
        # print(locatedTriangle)

        trianglesOfInterest = {locatedTriangle}
        triangleQueue = {locatedTriangle}
        verticesOfInterest = set()

        for i in range(rings):
            # print('ring: ', i)
            for triangle in triangleQueue.copy():
                for neighboringTriangle in self.adjacent_triangles(triangle):
                    if neighboringTriangle not in trianglesOfInterest:
                        trianglesOfInterest.add(tuple(neighboringTriangle))
                        triangleQueue.add(tuple(neighboringTriangle))
                triangleQueue.remove(tuple(triangle))
            # print(trianglesOfInterest)

        for triangle in trianglesOfInterest:
            for i in range(3):
                verticesOfInterest.add(triangle[i])
        # print(verticesOfInterest)

        return verticesOfInterest

    def get_vertices_from_node(self, nodeIds):
        print(nodeIds)
        indexedVertices = set()

        for nodeId in nodeIds:
            prevLen = len(indexedVertices)
            print('nodeId: ', nodeId)
            triangles = self.get_triangles(nodeId)
            i = 0
            for triangle in triangles:
                for vId in triangle:
                    # print(vId)
                    i += 0
                    if vId != 0:
                        indexedVertices.add(vId)

                if i > 30:  # only for testing
                    break
            print('added vertices: ', len(indexedVertices)-prevLen)

        return indexedVertices

    def smooth_vertices(self, vertexSet):
        # disabled the convex hull vertices

        # print('smoothing ...')

        triangleCenters = dict()
        updatedVertices = set()
        updates = 0

        for vertex in vertexSet:

            # print('---- ', vertex)

            handleConvex = False
            if self.triangulation.is_vertex_convex_hull(vertex):
                # handle different...
                # discard at all, too few information
                # print('im on the hull! skipping')
                handleConvex = True
                continue

            adjacentVertices = self.triangulation.adjacent_vertices_to_vertex(vertex)
            if 0 in adjacentVertices:
                # some kind of convex hull. Not sure how to handle this one yet.
                # print('Im a neighbor of vertex 0, some sort of convex hull, SKIPPING')
                continue

            vertexLocation = self.triangulation.get_point(vertex)
            originalZ = self.get_z(vertex, idOnly=True)
            # print(self.triangulation.get_point(vertex))
            # nrAdjacentVertices = len(adjacentVertices)
            # print(nrAdjacentVertices)
            incidentTriangles = self.triangulation.incident_triangles_to_vertex(vertex)
            # print(adjacentVertices)
            # print(incidentTriangles)

            sumOfWeights = 0
            sumOfWeightedAvg = 0
            for i, adjacentVertex in enumerate(adjacentVertices):
                # print(adjacentVertex)

                # delaunay distances
                adjacentVertexLocation = self.triangulation.get_point(adjacentVertex)
                dxT = vertexLocation[0] - adjacentVertexLocation[0]
                dyT = vertexLocation[1] - adjacentVertexLocation[1]
                dtDist = math.hypot(dxT, dyT)
                # print(dtDist)

                leftTriangle = incidentTriangles[i]
                rightTriangle = incidentTriangles[i-1]
                leftPseudoTriangle = tuple(self.pseudo_triangle(leftTriangle))
                rightPseudoTriangle = tuple(self.pseudo_triangle(rightTriangle))

                # print('original: ', leftPseudoTriangle, rightPseudoTriangle)

                # if 0 in leftTriangle:
                #     print('leftTriangle contains 0')
                # elif 0 in rightTriangle:
                #     print('rightTriangle contains 0')

                # if handleConvex:
                #     if self.triangulation.is_vertex_convex_hull(adjacentVertex):
                #         print('adjacent vertex is hull')
                #         if self.triangulation.is_vertex_convex_hull(adjacentVertices[i-1]):
                #             print('right is empty')
                #             leftTriangle = [vertex, adjacentVertex,
                #                             adjacentVertices[(i+1) % nrAdjacentVertices]]
                #             leftPseudoTriangle = tuple(self.pseudo_triangle(leftTriangle))
                #             rightPseudoTriangle = None
                #         elif self.triangulation.is_vertex_convex_hull(adjacentVertices[(i+1) % nrAdjacentVertices]):
                #             print('left is empty')
                #             rightTriangle = [vertex, adjacentVertices[i-1], adjacentVertex]
                #             rightPseudoTriangle = tuple(self.pseudo_triangle(rightTriangle))
                #             leftPseudoTriangle = None

                # print('new triangles: ', leftPseudoTriangle, rightPseudoTriangle)

                # voronoi distances
                if not leftPseudoTriangle in triangleCenters:
                    leftCenter = self.circumcenter(leftPseudoTriangle)
                    triangleCenters[leftPseudoTriangle] = leftCenter
                else:
                    leftCenter = triangleCenters[leftPseudoTriangle]
                if not rightPseudoTriangle in triangleCenters:
                    rightCenter = self.circumcenter(rightPseudoTriangle)
                    triangleCenters[rightPseudoTriangle] = rightCenter
                else:
                    rightCenter = triangleCenters[rightPseudoTriangle]

                dxV = rightCenter[0] - leftCenter[0]
                dyV = rightCenter[1] - leftCenter[1]
                vdDist = math.hypot(dxV, dyV)
                # print(vdDist)

                # weighted average
                vertexZ = self.get_z(adjacentVertex, idOnly=True)
                vertexWeight = vdDist / dtDist
                vertexWeightedAvg = vertexWeight * vertexZ
                sumOfWeights += vertexWeight
                sumOfWeightedAvg += vertexWeightedAvg

            interpolatedZ = round(sumOfWeightedAvg / sumOfWeights, 3)
            # print(originalZ, interpolatedZ, interpolatedZ < originalZ)

            if interpolatedZ < originalZ:
                # print('updated vertex', interpolatedZ)
                updates += 1
                self.add_vertex_to_queue(vertex, interpolatedZ, idOnly=True)
                updatedVertices.add(vertex)

        self.msg('updated vertices: {}'.format(updates), 'info')

        return updatedVertices

        # self.vertexDict.update_values_from_queue()
        # self.update_region_graph(updatedVertices)

        # print(adjacentVertex, leftPseudoTriangle, rightPseudoTriangle)

    def displace_vertices(self, displaceDict):

        displacementOvershoot = 0.01  # one centimeter up

        updatedVertices = set()
        updates = 0

        for connectingNodeId in displaceDict.keys():
            # print('connectingNodeId: ', connectingNodeId)
            aggLevel = displaceDict[connectingNodeId]['aggregation_level']
            aggLevel = aggLevel - displacementOvershoot
            # set of ids
            verticesToAggregate = displaceDict[connectingNodeId]['vertices_to_aggregate']

            for vertex in verticesToAggregate:

                if self.triangulation.is_vertex_convex_hull(vertex):
                    # handle different...
                    # discard at all, too few information
                    # print('im on the hull! skipping')
                    continue

                adjacentVertices = self.triangulation.adjacent_vertices_to_vertex(vertex)
                if 0 in adjacentVertices:
                    # some kind of convex hull. Not sure how to handle this one yet.
                    # print('Im a neighbor of vertex 0, some sort of convex hull, SKIPPING')
                    continue

                originalZ = self.get_z(vertex, idOnly=True)
                queuedZ = self.get_queued_z(vertex, idOnly=True)

                if queuedZ:
                    if aggLevel < queuedZ:
                        self.add_vertex_to_queue(vertex, aggLevel, idOnly=True)
                        updatedVertices.add(vertex)
                elif aggLevel < originalZ:
                    updates += 1
                    self.add_vertex_to_queue(vertex, aggLevel, idOnly=True)
                    updatedVertices.add(vertex)

        self.msg('updated vertices: {}'.format(updates), 'info')

        return updatedVertices

    def get_triangles_to_isopoints_in_edge(self, isopoints, edgeId):
        # print(edgeId, isopoints)
        edgeObject = self.graph['edges'][edgeId]
        isoVertexPointers = edgeObject['iso_vertex_pointers']

        # print(isoVertexPointers)
        # for v in isoVertexPointers.keys():
        #     print(v, isoVertexPointers[v])

        immediateTriangles = set()

        for isoPoint in isopoints:
            # print(isoPoint)
            # print(isoVertexPointers[isoPoint])
            for triangle in isoVertexPointers[isoPoint]:
                immediateTriangles.add(triangle)

        # print(immediateTriangles)
        return immediateTriangles

    def get_all_immediate_triangles(self, edge_isopoints_dict):

        immediateTriangles = set()

        for edgeId in edge_isopoints_dict.keys():
            sharpTriangles = self.get_triangles_to_isopoints_in_edge(
                edge_isopoints_dict[edgeId], edgeId)
            immediateTriangles.update(sharpTriangles)

        return immediateTriangles

    def get_ring_around_triangle(self, triangle):

        ringTriangles = set()
        for v in triangle:
            incidentTriangles = self.triangulation.incident_triangles_to_vertex(v)
            trueIncidentTriangles = []
            for incTriangle in incidentTriangles:
                if 0 not in incTriangle:
                    trueIncidentTriangles.append(tuple(self.pseudo_triangle(incTriangle)))
            # incidentTriangles = [tuple(self.pseudo_triangle(tri)) for tri in incidentTriangles]
            ringTriangles.update(trueIncidentTriangles)

        return ringTriangles

    def get_triangle_rings_around_triangles(self, triangles, rings=0):

        allTriangles = set(triangles)

        ring = 0
        while ring < rings:
            # print('ring: ', ring)

            for triangle in allTriangles.copy():
                # print(triangle)
                ringTriangles = self.get_ring_around_triangle(triangle)
                # print(ringTriangles)

                allTriangles.update(ringTriangles)

            ring += 1

        # print(len(allTriangles))
        return allTriangles

    def get_vertices_from_triangles(self, triangles):

        allVertices = set()

        for triangle in triangles:
            allVertices.update(triangle)

        return allVertices

    def simple_smooth_and_rebuild(self, vertexSet):

        # self.print_graph()

        self.msg('smoothing', 'header')
        self.msg('vertices to smooth: {}'.format(len(vertexSet)), 'info')

        allChangedVertices = set()
        for i in range(1):
            changedVertices = self.smooth_vertices(vertexSet)
            allChangedVertices.update(changedVertices)
            # print(allChangedVertices)
            self.vertexDict.update_previous_z_from_queue()  # stored the old zvalue in previous_z
            self.vertexDict.update_values_from_queue()  # updates the working z-value in z
            # queue is now empty again
        # may again smooth the vertices?

        if len(allChangedVertices) == 0:
            return False, len(allChangedVertices)

        # remove previous_z because region graph is built again
        for changedVertex in allChangedVertices:
            self.vertexDict.remove_previous_z(self.triangulation.get_point(
                changedVertex))

        # delete entire graph
        self.graph = {'nodes': {}, 'edges': {}, 'shallowestNodes': set(), 'deepestNodes': set()}
        self.triangleInventory = dict()
        self.nrNodes = 0
        self.nrEdges = 0
        self.generate_regions()

        self.build_graph2()
        # self.print_graph()

        return True, len(allChangedVertices)

    def displace_vertices_helper(self, displaceDict):
        self.msg('Aggregation pass...', 'header')
        print('input connecting nodes: ', len(displaceDict))

        changedVertices = self.displace_vertices(displaceDict)

        self.vertexDict.update_previous_z_from_queue()
        self.vertexDict.update_values_from_queue()
        # print('vertices with updated depth: ', len(changedVertices))

        # print('allnodesfirst: ', self.graph['nodes'].keys())
        changedTriangles, changedNodes = self.get_changed_triangles(
            changedVertices, self.triangleInventory.copy())

        # nodesInTI = set()
        # for tri in self.triangleInventory.keys():
        #     # print(self.triangleInventory[tri])
        #     nodesInTI.update(self.triangleInventory[tri])
        #
        # print('tinodes1: ', nodesInTI, '\nallnodes: ', self.graph['nodes'].keys())

        print('changed nodes: ', len(changedNodes))
        # print('changed triangles: ', len(changedTriangles))
        # if len(changedTriangles) == 0:
        #     print('no triangles were changed in interval, returning without updating!')
        #     return False, 0

        allDeletedTriangles = set()
        oldNeighboringNodes = set()
        changedEdges = set()
        for changedNode in changedNodes:
            nodeTriangles = self.get_triangles(changedNode)
            deepNeighbors = self.get_neighboring_nodes(changedNode, 'deep')
            for deepNeighbor in deepNeighbors:
                changedEdges.add((changedNode, deepNeighbor))
            shallowNeighbors = self.get_neighboring_nodes(changedNode, 'shallow')
            for shallowNeighbor in shallowNeighbors:
                changedEdges.add((shallowNeighbor, changedNode))
            allDeletedTriangles.update(nodeTriangles)
            oldNeighboringNodes.update(deepNeighbors)
            oldNeighboringNodes.update(shallowNeighbors)

        # print(len(allDeletedTriangles), oldNeighboringNodes)
        # print(oldNeighboringNodes.difference(changedNodes))

        poppedNodes = set()
        for triangle in allDeletedTriangles:
            # print(triangle)
            # print(self.triangleInventory[triangle])
            poppedNodes.update(self.triangleInventory[triangle])
            for reffedNode in self.triangleInventory[triangle]:
                self.delete_triangle_from_node(triangle, reffedNode)
            # print(self.triangleInventory[triangle])
            del self.triangleInventory[triangle]

        # for nodeId in poppedNodes:
        #     print(nodeId, len(self.get_triangles(nodeId)),
        #           len(self.graph['nodes'][nodeId]['edges']))
        #     if len(self.get_triangles(nodeId)) == 0 and len(self.graph['nodes'][nodeId]['edges']) == 0:
        #         changedNodes.add(nodeId)
        #         self.msg('poppednode will be deleted {}'.format(nodeId), 'warning')

        # print(poppedNodes)
        # print('changedNodes: ', changedNodes, '\npoppedNodes: ', poppedNodes)

        for changedEdge in changedEdges:
            self.delete_edge(changedEdge)

        for changedNode in changedNodes:
            self.remove_node_and_all_contents(changedNode)

        # nodesInTI = set()
        # for tri in self.triangleInventory.keys():
        #     # print(self.triangleInventory[tri])
        #     nodesInTI.update(self.triangleInventory[tri])
        # print('tinodes2: ', nodesInTI)

        # remove previous_z because region graph is built again
        for changedVertex in changedVertices:
            self.vertexDict.remove_previous_z(self.triangulation.get_point(
                changedVertex))

        # insert all deleted triangles back in the graph
        if len(allDeletedTriangles) > 0:
            affectedNodes = self.insert_triangles_into_region_graph2(
                allDeletedTriangles, poppedNodes)
            # print(affectedNodes)
            self.establish_edges_on_affected_nodes(affectedNodes)
            self.debug(affectedNodes)

        # newly inserted nodes are not connected yet

        # self.print_graph()
        # establish edges again
        # self.establish_edges_on_affected_nodes(affectedNodes)

        # self.print_graph()
        # print(self.availableNodeIds)

        keysCopy = list(self.graph['nodes'].keys())

        for nodeId in keysCopy:
            # print(nodeId, len(self.get_triangles(nodeId)),
                  # len(self.graph['nodes'][nodeId]['edges']))
            if len(self.get_triangles(nodeId)) == 0 and len(self.graph['nodes'][nodeId]['edges']) == 0:
                self.msg('poppednode will be deleted {}'.format(nodeId), 'warning')
                self.remove_node_and_all_contents(nodeId)
            elif len(self.get_triangles(nodeId)) == 0:
                self.msg('poppednode also deleted  {}, '.format(nodeId), 'warning')
                for edgeId in self.graph['nodes'][nodeId]['edges']:
                    self.delete_edge(self.graph['edges'][edgeId]['edge'])
                self.remove_node_and_all_contents(nodeId)

        return len(changedVertices)

    def smooth_vertices_new(self, vertexSet):
        # self.msg('\n==== Smoothing pass ====', 'header')
        # print('input vertices: ', len(vertexSet))

        changedVertices = self.smooth_vertices(vertexSet)
        self.vertexDict.update_previous_z_from_queue()
        self.vertexDict.update_values_from_queue()
        # print('vertices with updated depth: ', len(changedVertices))

        # print('allnodesfirst: ', self.graph['nodes'].keys())
        changedTriangles, changedNodes = self.get_changed_triangles(
            changedVertices, self.triangleInventory.copy())

        # nodesInTI = set()
        # for tri in self.triangleInventory.keys():
        #     # print(self.triangleInventory[tri])
        #     nodesInTI.update(self.triangleInventory[tri])
        #
        # print('tinodes1: ', nodesInTI, '\nallnodes: ', self.graph['nodes'].keys())

        print('changed nodes: ', len(changedNodes))
        # print('changed triangles: ', len(changedTriangles))
        # if len(changedTriangles) == 0:
        #     print('no triangles were changed in interval, returning without updating!')
        #     return False, 0

        allDeletedTriangles = set()
        oldNeighboringNodes = set()
        changedEdges = set()
        for changedNode in changedNodes:
            nodeTriangles = self.get_triangles(changedNode)
            deepNeighbors = self.get_neighboring_nodes(changedNode, 'deep')
            for deepNeighbor in deepNeighbors:
                changedEdges.add((changedNode, deepNeighbor))
            shallowNeighbors = self.get_neighboring_nodes(changedNode, 'shallow')
            for shallowNeighbor in shallowNeighbors:
                changedEdges.add((shallowNeighbor, changedNode))
            allDeletedTriangles.update(nodeTriangles)
            oldNeighboringNodes.update(deepNeighbors)
            oldNeighboringNodes.update(shallowNeighbors)

        # print(len(allDeletedTriangles), oldNeighboringNodes)
        # print(oldNeighboringNodes.difference(changedNodes))

        poppedNodes = set()
        for triangle in allDeletedTriangles:
            # print(triangle)
            # print(self.triangleInventory[triangle])
            poppedNodes.update(self.triangleInventory[triangle])
            for reffedNode in self.triangleInventory[triangle]:
                self.delete_triangle_from_node(triangle, reffedNode)
            # print(self.triangleInventory[triangle])
            del self.triangleInventory[triangle]

        # for nodeId in poppedNodes:
        #     print(nodeId, len(self.get_triangles(nodeId)),
        #           len(self.graph['nodes'][nodeId]['edges']))
        #     if len(self.get_triangles(nodeId)) == 0 and len(self.graph['nodes'][nodeId]['edges']) == 0:
        #         changedNodes.add(nodeId)
        #         self.msg('poppednode will be deleted {}'.format(nodeId), 'warning')

        # print(poppedNodes)
        # print('changedNodes: ', changedNodes, '\npoppedNodes: ', poppedNodes)

        for changedEdge in changedEdges:
            self.delete_edge(changedEdge)

        for changedNode in changedNodes:
            self.remove_node_and_all_contents(changedNode)

        # nodesInTI = set()
        # for tri in self.triangleInventory.keys():
        #     # print(self.triangleInventory[tri])
        #     nodesInTI.update(self.triangleInventory[tri])
        # print('tinodes2: ', nodesInTI)

        # remove previous_z because region graph is built again
        for changedVertex in changedVertices:
            self.vertexDict.remove_previous_z(self.triangulation.get_point(
                changedVertex))

        # insert all deleted triangles back in the graph
        if len(allDeletedTriangles) > 0:
            affectedNodes = self.insert_triangles_into_region_graph2(
                allDeletedTriangles, poppedNodes)
            # print(affectedNodes)
            self.establish_edges_on_affected_nodes(affectedNodes)
            self.debug(affectedNodes)

        # newly inserted nodes are not connected yet

        # self.print_graph()
        # establish edges again
        # self.establish_edges_on_affected_nodes(affectedNodes)

        # self.print_graph()
        # print(self.availableNodeIds)

        keysCopy = list(self.graph['nodes'].keys())

        for nodeId in keysCopy:
            # print(nodeId, len(self.get_triangles(nodeId)),
                  # len(self.graph['nodes'][nodeId]['edges']))
            if len(self.get_triangles(nodeId)) == 0 and len(self.graph['nodes'][nodeId]['edges']) == 0:
                self.msg('poppednode will be deleted {}'.format(nodeId), 'warning')
                self.remove_node_and_all_contents(nodeId)
            elif len(self.get_triangles(nodeId)) == 0:
                self.msg('poppednode also deleted  {}, '.format(nodeId), 'warning')
                for edgeId in self.graph['nodes'][nodeId]['edges']:
                    self.delete_edge(self.graph['edges'][edgeId]['edge'])
                self.remove_node_and_all_contents(nodeId)

        return len(changedVertices)

    def smooth_vertices_helper2(self, vertexSet):

        self.msg('\n==== Smoothing pass ====', 'header')
        print('input vertices: ', len(vertexSet))
        # self.print_graph()
        # self.make_network_graph()
        # this dict contains for each triangle the nodes it belonged to previously
        oldTriangleInventory = self.triangleInventory.copy()
        allChangedVertices = set()

        # compute the new z-value and if it is shallower, append it to changedVertices
        # the new z-value is stored in vertexDict.queue
        for i in range(1):
            changedVertices = self.smooth_vertices(vertexSet)
            allChangedVertices.update(changedVertices)
            # print(allChangedVertices)
            self.vertexDict.update_previous_z_from_queue()  # stored the old zvalue in previous_z
            self.vertexDict.update_values_from_queue()  # updates the working z-value in z
            # queue is now empty again
        # may again smooth the vertices?

        print('vertices with updated depth: ', len(allChangedVertices))

        # Updatin the region graph if necessary:
        changedTriangles, changedNodes = self.get_changed_triangles(
            allChangedVertices, oldTriangleInventory)
        # print(changedNodes)
        print('triangles with updated interval: ', len(changedTriangles))
        print('affected nodes: ', changedNodes)

        if len(changedTriangles) == 0:
            print('no triangles were changed in interval, returning without updating!')
            return False

        # we need to update the entire node, so lets get all triangles in each node
        trianglesToBeDeleted = set()
        edgesToBeDeleted = set()
        for changedNode in changedNodes:
            # print('changedNode: ', changedNode, self.get_interval_from_node(changedNode))
            # print(changedNode, len(self.get_triangles(changedNode)))
            trianglesToBeDeleted.update(self.get_triangles(changedNode))
            shallowNeighbors = self.get_neighboring_nodes(changedNode, 'shallow')
            for shallowNeighbor in shallowNeighbors:
                edgesToBeDeleted.add((shallowNeighbor, changedNode))
            deepNeighbors = self.get_neighboring_nodes(changedNode, 'deep')
            for deepNeighbor in deepNeighbors:
                edgesToBeDeleted.add((changedNode, deepNeighbor))
        # print('all triangles to be deleted: ', len(trianglesToBeDeleted), 'edges: ', edgesToBeDeleted)

        # for tri in trianglesToBeDeleted:
        #     print(oldTriangleInventory[tri])

        # removes actual edges
        possibleNeighboringEdges = set()
        extendedNeighboringNodes = set()
        for edgeCombination in edgesToBeDeleted:
            possibleNeighboringEdges.update({edgeCombination[0], edgeCombination[1]})

            # extendedNeighboringNodes.update(self.get_neighboring_nodes(edgeCombination[0], 'deep'))
            # extendedNeighboringNodes.update(
            #     self.get_neighboring_nodes(edgeCombination[0], 'shallow'))
            # extendedNeighboringNodes.update(self.get_neighboring_nodes(edgeCombination[1], 'deep'))
            # extendedNeighboringNodes.update(
            #     self.get_neighboring_nodes(edgeCombination[1], 'shallow'))

            self.delete_edge(edgeCombination)

        # removes actual nodes and all its triangles inside
        for changedNode in changedNodes:
            self.remove_node_and_all_contents(changedNode)

        # # removes actual edges
        # possibleNeighboringEdges = set()
        # for edgeCombination in edgesToBeDeleted:
        #     possibleNeighboringEdges.update({edgeCombination[0], edgeCombination[1]})
        #
        #     self.delete_edge(edgeCombination)

        # remove previous_z because region graph is built again
        for changedVertex in allChangedVertices:
            self.vertexDict.remove_previous_z(self.triangulation.get_point(
                changedVertex))

        # self.build_graph2()
        self.debug('######old neighboring nodes: {}'.format(possibleNeighboringEdges))
        self.debug('######ext neighboring nodes: {}'.format(extendedNeighboringNodes))

        # insert all deleted triangles back in the graph
        affectedNodes = self.insert_triangles_into_region_graph2(
            trianglesToBeDeleted, possibleNeighboringEdges)
        # newly inserted nodes are not connected yet
        self.debug(affectedNodes)

        # self.print_graph()
        # establish edges again
        self.establish_edges_on_affected_nodes(affectedNodes)

        # self.print_graph()
        # self.make_network_graph()

        return True, len(allChangedVertices)

    def smooth_vertices_helper(self, vertexSet):
        # contains pointers per triangle to which nodes it belonged to previously
        oldTriangleInventory = self.triangleInventory.copy()
        changedVertices = self.smooth_vertices(vertexSet)  # set
        # changed vertices are now in the vertexDict queue with a new z-value
        self.vertexDict.update_previous_z_from_queue()  # saves the previous known z-values
        self.vertexDict.update_values_from_queue()  # edits the interpolated z-value
        # queue is now empty
        # gets all the affected triangles, only if their interval is also changed
        changedTriangles = self.get_changed_triangles(changedVertices, oldTriangleInventory)

        for changedVertex in changedVertices:
            self.vertexDict.remove_previous_z(self.triangulation.get_point(
                changedVertex))  # cautieso, used in smooth_vertices()

        self.update_region_graph(changedVertices)

    def circumcenter(self, triangle):
        # https://stackoverflow.com/a/56225021
        ptA = self.triangulation.get_point(triangle[0])
        ptB = self.triangulation.get_point(triangle[1])
        ptC = self.triangulation.get_point(triangle[2])
        ax, ay = ptA[0], ptA[1]
        bx, by = ptB[0], ptB[1]
        cx, cy = ptC[0], ptC[1]
        # ax = float(input('What is x of point 1?'))
        # ay = float(input('What is y of point 1?'))
        # bx = float(input('What is x of point 2?'))
        # by = float(input('What is y of point 2?'))
        # cx = float(input('What is x of point 3?'))
        # cy = float(input('What is y of point 3?'))
        d = 2 * (ax * (by - cy) + bx * (cy - ay) + cx * (ay - by))
        ux = ((ax * ax + ay * ay) * (by - cy) + (bx * bx + by * by)
              * (cy - ay) + (cx * cx + cy * cy) * (ay - by)) / d
        uy = ((ax * ax + ay * ay) * (cx - bx) + (bx * bx + by * by)
              * (ax - cx) + (cx * cx + cy * cy) * (bx - ax)) / d
        ux = round(ux, 3)
        uy = round(uy, 3)
        return (ux, uy)

    def simple_densify_and_rebuild(self, trianglesToDensify, tempRings=3):
        self.msg('> densifying {} triangles'.format(len(trianglesToDensify)), 'info')

        circumCenters = set()
        newPoints = list()

        for triangle in trianglesToDensify:
            circumCenter = self.circumcenter(triangle)
            circumTriangle = self.triangulation.locate(circumCenter[0], circumCenter[1])
            if circumTriangle == []:
                # outside convex hull
                # print('is outside convex hull')
                continue
            convexHull = False
            for vId in circumTriangle:
                if self.triangulation.is_vertex_convex_hull(vId):
                    convexHull = True
                    break
            if convexHull:
                # wont add a point in a triangle adjacent to convex hull,
                # we cannot interpolate there
                # print('is convex hull triangle')
                continue

            # now we have a valid triangle to insert a new point
            # just use 5 rings to make sure we have a complete voronoi?
            # TODO
            circumTriangle = tuple(self.pseudo_triangle(circumTriangle))
            neighborhoodTriangles = self.get_triangle_rings_around_triangles(
                [circumTriangle], rings=tempRings)
            neighborhoodVertices = self.get_vertices_from_triangles(neighborhoodTriangles)

            tempVerticesList = []
            for tempVertex in neighborhoodVertices:
                tvPoint = self.triangulation.get_point(tempVertex)
                tvElevation = self.get_z(tempVertex, idOnly=True)
                tvX, tvY = tvPoint[0], tvPoint[1]

                tempVerticesList.append([tvX, tvY, tvElevation])

            tempTriangulation = startin.DT()
            tempTriangulation.insert(tempVerticesList)
            interpolatedValue = tempTriangulation.interpolate_laplace(
                circumCenter[0], circumCenter[1])
            interpolatedValue = round(interpolatedValue, 3)
            del tempTriangulation

            # print('interpolated: ', interpolatedValue)

            newPoints.append([circumCenter[0], circumCenter[1], interpolatedValue])
            self.pointQueue.append([circumCenter[0], circumCenter[1], interpolatedValue])

        # print(newPoints)
        # self.pointQueue.append(point)
        self.pointCount += 1

        self.triangulation_insert()

        # delete entire graph
        self.graph = {'nodes': {}, 'edges': {}, 'shallowestNodes': set(), 'deepestNodes': set()}
        self.triangleInventory = dict()
        self.nrNodes = 0
        self.nrEdges = 0
        self.generate_regions()

        # rebuild graph
        self.build_graph2()

    # ====================================== #
    #
    #   Metrics
    #
    # ====================================== #

    def ___METRICS___(self):
        # placeholder for Atom symbol-tree-view
        pass

    def angularity(self, ptHead, ptMid, ptTail):
        # print(ptHead, ptMid, ptTail)
        dx1, dy1 = ptMid[0] - ptHead[0], ptMid[1] - ptHead[1]
        dx2, dy2 = ptTail[0] - ptMid[0], ptTail[1] - ptMid[1]
        inner_product = dx1*dx2 + dy1*dy2
        len1 = math.hypot(dx1, dy1)
        len2 = math.hypot(dx2, dy2)
        # TODO redo this function, to much problems
        if len1 == 0 or len2 == 0:
            return 0.0
        else:
            splitted = inner_product/(len1*len2)
            if splitted > 1.0:
                splitted = 1.0
            elif splitted < -1.0:
                splitted = -1.0
            # print(splitted, math.acos(splitted))
            return round(math.acos(splitted), 4)

    def check_isobath_angularity(self, edgeIds=[], threshold=3.14):
        if not len(edgeIds):
            edgeIds = self.graph['edges'].keys()

        turningPoints = set()
        turningPointsDict = {}

        for edge in edgeIds:

            turningPointsDict[edge] = []

            closed = self.graph['edges'][str(edge)]['closed']
            geom = self.graph['edges'][str(edge)]['geom']
            self.graph['edges'][str(edge)]['point_angularities'] = []
            pointAngularities = self.graph['edges'][str(edge)]['point_angularities']
            # print(geom)
            # print('edge: ', edge)

            if closed:
                # print('0', geom[-2], geom[0], geom[1])
                angularity = self.angularity(geom[-2], geom[0], geom[1])
                pointAngularities.append(angularity)
                if angularity > threshold:
                    turningPoints.add(tuple(geom[0]))
                    turningPointsDict[edge].append(tuple(geom[0]))
            for i in range(1, len(geom)-1):
                # print(i, geom[i-1], geom[i], geom[i+1])
                angularity = self.angularity(geom[i-1], geom[i], geom[i+1])
                pointAngularities.append(angularity)
                if angularity > threshold:
                    turningPoints.add(tuple(geom[i]))
                    turningPointsDict[edge].append(tuple(geom[i]))

        return turningPointsDict, turningPoints

    def triangle_area(self, triangle):
        ptOne = self.triangulation.get_point(triangle[0])
        ptTwo = self.triangulation.get_point(triangle[1])
        ptThree = self.triangulation.get_point(triangle[2])

        a = math.hypot(ptTwo[0] - ptOne[0], ptTwo[1] - ptOne[1])
        b = math.hypot(ptThree[0] - ptTwo[0], ptThree[1] - ptTwo[1])
        c = math.hypot(ptOne[0] - ptThree[0], ptOne[1] - ptThree[1])

        s = (a + b + c) / 2
        area = math.sqrt(s * (s - a) * (s - b) * (s - c))

        return Decimal(str(round(area, 3)))

    def triangle_aspect_ratio(self, triangle):
        ptOne = self.triangulation.get_point(triangle[0])
        ptTwo = self.triangulation.get_point(triangle[1])
        ptThree = self.triangulation.get_point(triangle[2])

        a = math.hypot(ptTwo[0] - ptOne[0], ptTwo[1] - ptOne[1])
        b = math.hypot(ptThree[0] - ptTwo[0], ptThree[1] - ptTwo[1])
        c = math.hypot(ptOne[0] - ptThree[0], ptOne[1] - ptThree[1])

        s = (a + b + c) / 2
        aspectRatio = (a*b*c) / (8 * (s-a) * (s-b) * (s-c))
        # area = math.sqrt(s * (s - a) * (s - b) * (s - c))

        return Decimal(str(round(aspectRatio, 3)))

    def compute_node_area(self, nodeIds=[]):
        if not len(nodeIds):
            nodeIds = self.graph['nodes'].keys()

        for nodeId in nodeIds:
            # print(nodeId, 'node_area ')
            node = self.graph['nodes'][nodeId]
            nodeTriangles = self.get_triangles(nodeId)
            node['full_area'] = 0
            for triangle in nodeTriangles:
                node['full_area'] += self.triangle_area(triangle)

    def compute_isobath_area(self, edgeIds=[]):
        if not len(edgeIds):
            edgeIds = self.graph['edges'].keys()

        for edgeId in edgeIds:
            if self.graph['edges'][edgeId]['closed'] is True:
                # print(edgeId, 'im closed isobath, calculating area')

                ptArray = np.array([[p[0], p[1]] for p in self.graph['edges'][edgeId]['geom']])
                x = ptArray[:, 0]
                y = ptArray[:, 1]

                # https://stackoverflow.com/a/53864271
                # coordinate shift
                x_ = x - x.mean()
                y_ = y - y.mean()
                # everything else is the same as maxb's code
                correction = x_[-1] * y_[0] - y_[-1] * x_[0]
                main_area = np.dot(x_[:-1], y_[1:]) - np.dot(y_[:-1], x_[1:])
                isoArea = 0.5 * np.abs(main_area + correction)
                # print(round(isoArea, 3))

                self.graph['edges'][edgeId]['iso_area'] = round(isoArea, 3)

    def check_spurs_gullys_2(self, edgeIds=[], threshold=None, spurThreshold=None, gullyThreshold=None):

        if not len(edgeIds):
            # get all edges
            edgeIds = self.graph['edges'].keys()

        spurgullyPoints = set()
        spurGullyDict = {}
        spursDict = {}
        gullyDict = {}
        allGeoms = []

        if not threshold and not spurThreshold and not gullyThreshold:
            print('please define a threshold for the spurs and gullies')
            # return set(), set()  # at least return something valid, handy for iterating later

        if threshold and not spurThreshold:
            spurThreshold = threshold
        if threshold and not gullyThreshold:
            gullyThreshold = threshold

        for edgeId in edgeIds:
            edge = self.graph['edges'][edgeId]
            edge['bend_detector'] = BendDetector(edgeId, edge, self.projectName)
            edge['bend_detector'].write_poly_file()
            edge['bend_detector'].triangulate()

            spurs, gullys = edge['bend_detector'].get_spurs_and_gullys2(
                gully_threshold=gullyThreshold, spur_threshold=spurThreshold)

            # exportDict = {'spurs': spurs, 'gullys': gullys}
            # edge['bend_detector'].export_triangles_shp(multi=exportDict)

            geomSummary = []
            spurGeoms = edge['bend_detector'].get_triangle_geoms(spurs)
            gullyGeoms = edge['bend_detector'].get_triangle_geoms(gullys)
            geomSummary.append(edgeId)
            geomSummary.append(spurGeoms)
            geomSummary.append(gullyGeoms)
            allGeoms.append(geomSummary)

            spurVertices = edge['bend_detector'].get_vertices_from_triangles(spurs)
            gullyVertices = edge['bend_detector'].get_vertices_from_triangles(gullys)

            # allInvalidTriangles = spurs.union(gullys)
            # invalidIsoVertices = edge['bend_detector'].get_vertices_from_triangles(
            #     allInvalidTriangles)
            # spurgullyPoints.update(invalidIsoVertices)

            # spurGullyDict[edgeId] = invalidIsoVertices

            spursDict[edgeId] = spurVertices
            gullyDict[edgeId] = gullyVertices

        # self.export_spur_gully_geoms(allGeoms)

        return spursDict, gullyDict

        # exportDict = {'spurs': spurs, 'gullys': gullys}
        # edge['bend_detector'].export_triangles_shp(multi=exportDict)
        # edgeBends = BendDetector(edgeId, edge, self.projectName)

        pass

    def check_spurs_gullys(self, edgeIds=[], threshold=None, spurThreshold=None, gullyThreshold=None):

        if not len(edgeIds):
            # get all edges
            edgeIds = self.graph['edges'].keys()

        spurgullyPoints = set()
        spurGullyDict = {}
        spursDict = {}
        gullyDict = {}
        allGeoms = []

        if not threshold and not spurThreshold and not gullyThreshold:
            print('please define a threshold for the spurs and gullies')
            # return set(), set()  # at least return something valid, handy for iterating later

        if threshold and not spurThreshold:
            spurThreshold = threshold
        if threshold and not gullyThreshold:
            gullyThreshold = threshold

        for edgeId in edgeIds:
            edge = self.graph['edges'][edgeId]
            edge['bend_detector'] = BendDetector(edgeId, edge, self.projectName)
            edge['bend_detector'].write_poly_file()
            edge['bend_detector'].triangulate()

            spurs, gullys = edge['bend_detector'].get_spurs_and_gullys2(
                gully_threshold=gullyThreshold, spur_threshold=spurThreshold)

            # exportDict = {'spurs': spurs, 'gullys': gullys}
            # edge['bend_detector'].export_triangles_shp(multi=exportDict)

            geomSummary = []
            spurGeoms = edge['bend_detector'].get_triangle_geoms(spurs)
            gullyGeoms = edge['bend_detector'].get_triangle_geoms(gullys)
            geomSummary.append(edgeId)
            geomSummary.append(spurGeoms)
            geomSummary.append(gullyGeoms)
            allGeoms.append(geomSummary)

            spurVertices = edge['bend_detector'].get_vertices_from_triangles(spurs)
            gullyVertices = edge['bend_detector'].get_vertices_from_triangles(gullys)

            allInvalidTriangles = spurs.union(gullys)
            invalidIsoVertices = edge['bend_detector'].get_vertices_from_triangles(
                allInvalidTriangles)
            spurgullyPoints.update(invalidIsoVertices)

            spurGullyDict[edgeId] = invalidIsoVertices

            spursDict[edgeId] = spurVertices
            gullyDict[edgeId] = gullyVertices

        self.export_spur_gully_geoms(allGeoms)

        return spurGullyDict, spurgullyPoints

        # exportDict = {'spurs': spurs, 'gullys': gullys}
        # edge['bend_detector'].export_triangles_shp(multi=exportDict)
        # edgeBends = BendDetector(edgeId, edge, self.projectName)

        pass

    def check_aggregation(self, nodeIds=[], threshold=None, extendByIntersectedTriangles=False):
        print('checking aggregation possibilities ...')

        connectingNodes = {}

        for region in self.regionNodes.keys():
            # print('region: ', region, self.regionNodes[region])
            regionNodes = self.regionNodes[region]
            for regionNode in regionNodes:
                shallowNodes = self.get_neighboring_nodes(regionNode, 'shallow')
                if len(shallowNodes) > 1:
                    # print('connectingNode: ', regionNode,
                    #       self.get_neighboring_nodes(regionNode, 'shallow'))
                    connectingNodes[regionNode] = {}

        print('found {} connecting nodes'.format(len(connectingNodes)))

        for connectingNode in connectingNodes.keys():
            connectingNodes[connectingNode]['edges'] = set()
            # print('\n----------------------\nconnecting node: ', connectingNode)
            nodeEdges = self.graph['nodes'][connectingNode]['edges']
            # print('nodeEdges: ', nodeEdges)
            for edgeId in nodeEdges:
                edge = self.graph['edges'][edgeId]
                # print('edgeiterator: ', edge['edge'])
                if connectingNode == edge['edge'][1]:
                    # the connecting node is the deeper node
                    # print('aggregation edge: ', edgeId, 'connectingNode: ',
                    #       connectingNode, 'shallowNode: ', edge['edge'][0])
                    connectingNodes[connectingNode]['edges'].add(edgeId)
                    connectingNodes[connectingNode]['aggregation_level'] = edge['value']

        # print(connectingNodes)

        noBridgeDetected = set()
        for connectingNodeId in connectingNodes.keys():
            connectingNode = connectingNodes[connectingNodeId]
            connectingNode['Aggregator'] = Aggregator(
                connectingNodeId=connectingNodeId, project_name=self.projectName)
            for edgeId in connectingNode['edges']:
                edge = self.graph['edges'][edgeId]
                connectingNode['Aggregator'].add_edge(edgeId=edgeId, edgeObject=edge)
            connectingNode['Aggregator'].write_poly_file()
            connectingNode['Aggregator'].triangulate()
            bridgeAreas = connectingNode['Aggregator'].get_area_to_aggregate(threshold=threshold)
            # list of bridging polygons, can be empty if nothing is found

            print('found {} bridge areas'.format(len(bridgeAreas)))

            # print(bridgeAreas)
            if bridgeAreas == []:
                # no bridges found
                noBridgeDetected.add(connectingNodeId)
                continue

            connectingNodeTriangles = self.get_triangles(connectingNodeId)
            connectingNodeVertices = self.get_vertices_from_triangles(connectingNodeTriangles)
            # print('\n--------------connectingNodeVertices: ', connectingNodeVertices)
            cnvDict = {}
            pointList = []
            insidePoints = set()
            for vertex in connectingNodeVertices:
                pointVal = self.triangulation.get_point(vertex)
                cnvDict[(pointVal[0], pointVal[1])] = vertex
                pointList.append((pointVal[0], pointVal[1]))

            for areaPolygon in bridgeAreas:
                searchPath = path.Path(areaPolygon)
                insides = searchPath.contains_points(pointList)
                # print(insides)

                for vIndex, insideTest in enumerate(insides):
                    # print(insideTest, type(insideTest))
                    if insideTest == True:  # np.bool_
                        insidePoints.add(cnvDict[pointList[vIndex]])

                # print(insidePoints)

            connectingNode['vertices_to_aggregate'] = insidePoints

            # tryout on extension of region
            if extendByIntersectedTriangles:
                print('extending aggregation area (incident triangles)')
                extendedPoints = set()
                for vId in insidePoints:
                    incidentTriangles = self.triangulation.incident_triangles_to_vertex(vId)
                    incidentTriangles = [tuple(self.pseudo_triangle(tri))
                                         for tri in incidentTriangles]
                    for incidentTriangle in incidentTriangles:
                        if 0 not in incidentTriangle:
                            if incidentTriangle in connectingNodeTriangles:
                                extendedPoints.update(
                                    self.get_vertices_from_triangles([incidentTriangle]))

                connectingNode['vertices_to_aggregate'] = extendedPoints

            # exportPointList = []
            # for point in insidePoints:
            #     point = self.triangulation.get_point(point)
            #     exportPointList.append((point[0], point[1]))
            # self.export_points(exportPointList, 'pointbridges_{}'.format(connectingNodeId))

            # connectingNode['Aggregator'].find_vertices_in_areas(
            #     vertexLocDict=cnvDict, areas=bridgeAreas)

            del connectingNode['Aggregator']

        for invalidNodeId in noBridgeDetected:
            connectingNodes.pop(invalidNodeId, None)

        return connectingNodes

    def set_sharp_points_bins(self, breakpoints):
        # print(breakpoints)

        sharpPointRegions = []
        sharpPointRegions.append([0, breakpoints[0]])
        for i in range(len(breakpoints))[1:]:
            sharpPointRegions.append([breakpoints[i - 1], breakpoints[i]])
        sharpPointRegions.append([breakpoints[-1], 360])

        # print(sharpPointRegions)

        self.sharpPointBins = sharpPointRegions

    def set_abs_change_bins(self, breakpoints):
        # print(breakpoints)

        absChangeRegions = []
        absChangeRegions.append([-0.1, breakpoints[0]])
        for i in range(len(breakpoints))[1:]:
            absChangeRegions.append([breakpoints[i - 1], breakpoints[i]])
        absChangeRegions.append([breakpoints[-1], 10000])

        # print(absChangeRegions)

        self.absChangeBins = absChangeRegions

    def set_min_change_bins(self, breakpoints):

        minChangeRegions = []
        minChangeRegions.append([-0.1, breakpoints[0]])
        for i in range(len(breakpoints))[1:]:
            minChangeRegions.append([breakpoints[i - 1], breakpoints[i]])
        minChangeRegions.append([breakpoints[-1], 10000])

        # print(absChangeRegions)

        self.minChangeBins = minChangeRegions

    def set_iso_seg_bins(self, breakpoints):

        isoSegBins = []
        isoSegBins.append([0, breakpoints[0]])
        for i in range(len(breakpoints))[1:]:
            isoSegBins.append([breakpoints[i - 1], breakpoints[i]])
        isoSegBins.append([breakpoints[-1], 10000])

        # print(isoSegBins)

        self.isoSegBins = isoSegBins

    def check_all_sharp_points(self):
        edgeIds = self.graph['edges'].keys()

        # sharpPointAngles = set()
        sharp_points = {}

        for bin in self.sharpPointBins:
            # print(str(bin))
            sharp_points[str(bin)[1:-1]] = 0

        for edge in edgeIds:
            closed = self.graph['edges'][str(edge)]['closed']
            geom = self.graph['edges'][str(edge)]['geom']

            if closed:
                angularity = self.angularity(geom[-2], geom[0], geom[1])
                angularity = round(math.degrees(angularity), 1)
                # print(angularity)
                # print(angularity)

                for bin, sharpBin in enumerate(self.sharpPointBins):
                    if angularity > sharpBin[0] and angularity <= sharpBin[1]:
                        sharp_points[str(sharpBin)[1:-1]] += 1
                        # print(str(sharpBin))
                        break

                # sharpPointAngles.add(angularity)

            for i in range(1, len(geom)-1):
                angularity = self.angularity(geom[i-1], geom[i], geom[i+1])
                angularity = round(math.degrees(angularity), 1)
                # print(angularity)

                for bin, sharpBin in enumerate(self.sharpPointBins):
                    if angularity > sharpBin[0] and angularity <= sharpBin[1]:
                        sharp_points[str(sharpBin)[1:-1]] += 1
                        # print(str(sharpBin))
                        break
                # sharpPointAngles.add(angularity)

        # print(sharp_points)
        return sharp_points

    def check_all_iso_lengths(self):
        edgeIds = self.graph['edges'].keys()

        iso_lengths = {}

        for bin in self.isoSegBins:
            iso_lengths[str(bin)[1:-1]] = 0

        for edge in edgeIds:
            orderedTriangles = self.graph['edges'][str(edge)]['ordered_triangles']

            for triangleId in orderedTriangles.keys():
                triangleObj = orderedTriangles[triangleId]
                if triangleObj['segment']:
                    seg = triangleObj['segment']
                    # print(seg)
                    dX = seg[1][0] - seg[0][0]
                    dY = seg[1][1] - seg[0][1]
                    segLength = math.hypot(dX, dY)

                for bin, isoBin in enumerate(self.isoSegBins):
                    if segLength > isoBin[0] and segLength <= isoBin[1]:
                        iso_lengths[str(isoBin)[1:-1]] += 1
                        break

        # for cha in iso_lengths.keys():
        #     print(cha, iso_lengths[cha])

        return iso_lengths

    def check_all_point_diffs(self):

        abs_diffs = {}
        min_diffs = {}

        for bin in self.absChangeBins:
            # print(str(bin))
            abs_diffs[str(bin)[1:-1]] = 0

        for bin in self.minChangeBins:
            # print(str(bin))
            min_diffs[str(bin)[1:-1]] = 0

        for vertex in self.vertices[1:]:
            # print(vertex)
            # print(vertex, self.get_z(vertex, idOnly=False),
            #       self.get_original_z(vertex, idOnly=False))
            originalZ = self.get_original_z(vertex)
            currentZ = self.get_z(vertex)

            absDifference = round(originalZ - currentZ, 3)

            originalMinimalDepth = self.isobathValues[bisect.bisect_right(
                self.isobathValues, originalZ) - 1]
            currentMinimalDepth = self.isobathValues[bisect.bisect_right(
                self.isobathValues, currentZ) - 1]

            minDifference = round(originalMinimalDepth - currentMinimalDepth, 3)

            # if str(minDifference) in min_diffs:
            #     min_diffs[str(minDifference)] += 1
            # else:
            #     min_diffs[str(minDifference)] = 1

            for bin, minBin in enumerate(self.minChangeBins):
                if minDifference > minBin[0] and minDifference <= minBin[1]:
                    min_diffs[str(minBin)[1:-1]] += 1
                    break

            for bin, absBin in enumerate(self.absChangeBins):
                if absDifference > absBin[0] and absDifference <= absBin[1]:
                    abs_diffs[str(absBin)[1:-1]] += 1
                    break

        # for bin in abs_diffs.keys():
        #     print(bin, abs_diffs[bin])

        # for cha in min_diffs.keys():
        #     print(cha, min_diffs[cha])

        # print(self.isobathValues)
        return abs_diffs, min_diffs

    def generate_statistics(self, tracker_dict=None):

        depare_area_dict = self.generate_depth_areas()
        sharp_points_dict = self.check_all_sharp_points()
        abs_diffs_dict, min_diffs_dict = self.check_all_point_diffs()
        iso_lengths_dict = self.check_all_iso_lengths()

        stats = self.statistics
        stats['iterations'] += 1
        stats['depare_areas'].append(depare_area_dict)
        stats['sharp_points'].append(sharp_points_dict)
        stats['abs_change'].append(abs_diffs_dict)
        stats['min_change'].append(min_diffs_dict)
        stats['iso_seg_lengths'].append(iso_lengths_dict)

        if tracker_dict:
            stats['iter_tracker'].append(tracker_dict)

    def export_statistics(self):

        stats = self.statistics
        separator = ';'

        depare_header = 'SEP={}\ndepares'.format(separator)
        sharp_header = 'SEP={}\nsharps'.format(separator)
        abs_change_header = 'SEP={}\nabs_change'.format(separator)
        min_change_header = 'SEP={}\nmin_change'.format(separator)
        isoseg_header = 'SEP={}\nisoseg'.format(separator)
        tracker_header = 'iteration{}stat{}counter'.format(separator, separator)

        for iter in range(stats['iterations']):
            depare_header = depare_header + '{}{}'.format(separator, iter)
            sharp_header = sharp_header + '{}{}'.format(separator, iter)
            abs_change_header = abs_change_header + '{}{}'.format(separator, iter)
            min_change_header = min_change_header + '{}{}'.format(separator, iter)
            isoseg_header = isoseg_header + '{}{}'.format(separator, iter)
        # print(depare_header, sharp_header)

        depare_rows = []
        depare_rows.append('total')
        for regionIndex in range(len(stats['depare_areas'][0]['regions'])):
            depare_rows.append(str(regionIndex))
        # print(depare_rows)

        sharp_rows = []
        for sharpBin in stats['sharp_points'][0].keys():
            sharp_rows.append('[{}]'.format(sharpBin))
        abs_change_rows = []
        for absBin in stats['abs_change'][0].keys():
            abs_change_rows.append('[{}]'.format(absBin))
        min_change_rows = []
        for minBin in stats['min_change'][0].keys():
            min_change_rows.append('[{}]'.format(minBin))
        isoseg_rows = []
        for isoBin in stats['iso_seg_lengths'][0].keys():
            isoseg_rows.append('[{}]'.format(isoBin))

        for iteration in range(stats['iterations']):
            # print(iteration)
            # print(stats['depare_areas'][iteration])
            # print(stats['sharp_points'][iteration])

            # DEPARE
            for rowIndex, row in enumerate(depare_rows):
                if rowIndex == 0:
                    value = str(stats['depare_areas'][iteration]['total']).replace('.', ',')
                    depare_rows[rowIndex] = row + \
                        '{}{}'.format(separator, value)
                else:
                    value = str(stats['depare_areas'][iteration]['regions']
                                [rowIndex - 1]).replace('.', ',')
                    depare_rows[rowIndex] = row + '{}{}'.format(separator, value)

            # SHARP Points
            for rowIndex, row in enumerate(stats['sharp_points'][0].keys()):
                sharp_rows[rowIndex] = sharp_rows[rowIndex] + \
                    '{}{}'.format(separator, stats['sharp_points'][iteration][row])

            # abs change Points
            for rowIndex, row in enumerate(stats['abs_change'][0].keys()):
                abs_change_rows[rowIndex] = abs_change_rows[rowIndex] + \
                    '{}{}'.format(separator, stats['abs_change'][iteration][row])

            # min change Points
            for rowIndex, row in enumerate(stats['min_change'][0].keys()):
                min_change_rows[rowIndex] = min_change_rows[rowIndex] + \
                    '{}{}'.format(separator, stats['min_change'][iteration][row])

            # iso seg length Points
            for rowIndex, row in enumerate(stats['iso_seg_lengths'][0].keys()):
                isoseg_rows[rowIndex] = isoseg_rows[rowIndex] + \
                    '{}{}'.format(separator, stats['iso_seg_lengths'][iteration][row])

        self.msg('> saving statistics...', 'info')

        depareName = 'stats_{}_depare.csv'.format(self.now())
        depareFile = os.path.join(os.getcwd(), 'projects', self.projectName, depareName)
        print('depare statistics file: ', depareFile)

        sharpsName = 'stats_{}_sharps.csv'.format(self.now())
        sharpsFile = os.path.join(os.getcwd(), 'projects', self.projectName, sharpsName)
        print('sharp statistics file: ', sharpsFile)

        absChangeName = 'stats_{}_abschanges.csv'.format(self.now())
        absChangeFile = os.path.join(os.getcwd(), 'projects', self.projectName, absChangeName)
        print('abs change statistics file: ', absChangeFile)

        minChangeName = 'stats_{}_minchanges.csv'.format(self.now())
        minChangeFile = os.path.join(os.getcwd(), 'projects', self.projectName, minChangeName)
        print('min changes statistics file: ', minChangeFile)

        isoSegName = 'stats_{}_isosegs.csv'.format(self.now())
        isoSegFile = os.path.join(os.getcwd(), 'projects', self.projectName, isoSegName)
        print('iso lengths statistics file: ', isoSegFile)

        trackerName = 'stats_{}_tracker.csv'.format(self.now())
        trackerFile = os.path.join(os.getcwd(), 'projects', self.projectName, trackerName)
        print('triacker statistics file: ', trackerFile)

        with open(depareFile, 'w') as depFile:
            # print(depare_header)
            # for depRow in depare_rows:
            #     print(depRow)
            depFile.write(depare_header + '\n')
            for depRow in depare_rows:
                depFile.write(depRow + '\n')

        # print(sharp_header)
        # for sharpRow in sharp_rows:
        #     print(sharpRow)
        with open(sharpsFile, 'w') as sharpFile:
            # print(depare_header)
            # for depRow in depare_rows:
            #     print(depRow)
            sharpFile.write(sharp_header + '\n')
            for sharpRow in sharp_rows:
                sharpFile.write(sharpRow + '\n')

        with open(absChangeFile, 'w') as absChangeFile:
            absChangeFile.write(abs_change_header + '\n')
            for absRow in abs_change_rows:
                absChangeFile.write(absRow + '\n')

        with open(minChangeFile, 'w') as minChangeFile:
            minChangeFile.write(min_change_header + '\n')
            for minRow in min_change_rows:
                minChangeFile.write(minRow + '\n')

        with open(isoSegFile, 'w') as isoSegFile:
            isoSegFile.write(isoseg_header + '\n')
            for isoRow in isoseg_rows:
                isoSegFile.write(isoRow + '\n')

        with open(trackerFile, 'w') as trackerFile:
            trackerFile.write(tracker_header + '\n')
            for iterationDict in stats['iter_tracker']:
                iterationNumber = iterationDict['iterations']
                for statKey in iterationDict.keys():
                    if not statKey == 'iterations':
                        statCount = iterationDict[statKey]
                        trackerFile.write('{};{};{}\n'.format(iterationNumber, statKey, statCount))

    # ====================================== #
    #
    #   Routine
    #
    # ====================================== #

    def start_routine(self, paramDict, statistics=False):

        self.msg('> starting routine...', 'header')

        # for param in paramDict.keys():
        #     print(param, paramDict[param])

        spurgully_threshold = paramDict['spurgully_threshold']
        spur_threshold = paramDict['spur_threshold']
        gully_threshold = paramDict['gully_threshold']
        angularity_threshold = paramDict['angularity_threshold']
        aspect_threshold = paramDict['aspect_threshold']
        size_threshold = paramDict['size_threshold']

        print('========\nthresholds:\nspurgully: {}\nspur: {}\ngully: {}\nangularity: {}\naspect: {}\nsize: {}\n========'.format(
            spurgully_threshold, spur_threshold, gully_threshold, angularity_threshold, aspect_threshold, size_threshold))

        iterations = 0

        # PREPASS
        for prepassIteration in range(paramDict['prepass']):
            self.msg('> prepass {}'.format(iterations), 'info')

            if statistics:
                # trackerDict = {'iteration': iterations}
                self.generate_isobaths5()
                self.generate_statistics()

            allVertices = self.vertices[1:]
            numberUpdatedVerticesPre = self.smooth_vertices_new(allVertices)

            iterations += 1

        # REST OF PROCESS
        routine = True
        process = True
        processNumber = 0
        while routine:

            if processNumber >= len(paramDict['process']):
                self.msg('\n> no process left', 'warning')
                break
            if iterations >= paramDict['maxiter']:
                self.msg('> max iterations exceeded', 'warning')
                routine = False
                break

            processStartIteration = iterations
            processList = paramDict['process'][processNumber]
            self.msg('\nprocess number: '.format(processNumber), 'header')
            for processMetric in processList[:-1]:
                print('metric: {}\t region: {}\t extended: {}'.format(
                    processMetric[0], processMetric[1], processMetric[2]))
            print('stop criterion: {}'.format(processList[-1]))
            # print(processList)

            while process and routine:
                self.msg('\n====== executing process, iteration: {}'.format(iterations), 'header')
                iterations += 1

                self.generate_isobaths5()
                if statistics:
                    self.generate_statistics()

                # Conflicting triangles
                conflictingTriangles = set()
                conflictingVertices = set()
                extendedConflictingTriangles = set()
                extendedConflictingVertices = set()
                verticesToUpdate = set()

                # Calculate metrics
                spurGullyCalculated = False
                for metricDefinition in processList[:-1]:
                    # print(metricDefinition)

                    if metricDefinition[0] == 'angularity':
                        sharpPointsDict, allSharpPoints = self.check_isobath_angularity(
                            threshold=angularity_threshold)
                        sharp_conflictingTriangles = self.get_all_immediate_triangles(
                            sharpPointsDict)
                        if metricDefinition[1] == 'r':
                            sharp_extendedConflictingTriangles = self.get_triangle_rings_around_triangles(
                                sharp_conflictingTriangles, rings=metricDefinition[2])
                        elif metricDefinition[1] == 'n':
                            pass
                        elif metricDefinition[1] == 'nn':
                            pass
                        conflictingTriangles.update(sharp_conflictingTriangles)
                        extendedConflictingTriangles.update(sharp_extendedConflictingTriangles)
                        print('sharp points: ', len(allSharpPoints))

                    elif metricDefinition[0] == 'spurs':
                        if not spurGullyCalculated:
                            spursDict, gullyDict = self.check_spurs_gullys_2(
                                threshold=spurgully_threshold, spurThreshold=spur_threshold, gullyThreshold=gully_threshold)
                            spurGullyCalculated = True
                        spurs_conflictingTriangles = self.get_all_immediate_triangles(
                            spursDict)
                        if metricDefinition[1] == 'r':
                            spurs_extendedConflictingTriangles = self.get_triangle_rings_around_triangles(
                                spurs_conflictingTriangles, rings=metricDefinition[2])
                        elif metricDefinition[1] == 'n':
                            pass
                        elif metricDefinition[1] == 'nn':
                            pass
                        conflictingTriangles.update(spurs_conflictingTriangles)
                        extendedConflictingTriangles.update(spurs_extendedConflictingTriangles)
                        print('spur triangles: ', len(spurs_conflictingTriangles))

                    elif metricDefinition[0] == 'gullys':
                        if not spurGullyCalculated:
                            spursDict, gullyDict = self.check_spurs_gullys_2(
                                threshold=spurgully_threshold, spurThreshold=spur_threshold, gullyThreshold=gully_threshold)
                            spurGullyCalculated = True
                        gully_conflictingTriangles = self.get_all_immediate_triangles(
                            gullyDict)
                        if metricDefinition[1] == 'r':
                            gully_extendedConflictingTriangles = self.get_triangle_rings_around_triangles(
                                gully_conflictingTriangles, rings=metricDefinition[2])
                        elif metricDefinition[1] == 'n':
                            pass
                        elif metricDefinition[1] == 'nn':
                            pass
                        conflictingTriangles.update(gully_conflictingTriangles)
                        extendedConflictingTriangles.update(gully_extendedConflictingTriangles)
                        print('gully triangles: ', len(gully_conflictingTriangles))

                print('conflictingTriangles ', len(conflictingTriangles))
                print('extendedConflictingTriangles ', len(extendedConflictingTriangles))

                if len(conflictingTriangles) == 0:
                    self.msg('> no conflicts found, skipping process', 'warning')
                    processNumber += 1
                    if iterations-1 >= paramDict['maxiter']:
                        self.msg('> max iterations exceeded', 'warning')
                        routine = False

                    break

                verticesToUpdate = self.get_vertices_from_triangles(extendedConflictingTriangles)
                # print('verticesToUpdate ', len(verticesToUpdate))

                # verticesAreUpdated, numberUpdatedVertices = self.smooth_vertices_helper2(
                #     verticesToUpdate)
                numberUpdatedVertices = self.smooth_vertices_new(
                    verticesToUpdate)
                # verticesAreUpdated, numberUpdatedVertices = self.simple_smooth_and_rebuild(
                # verticesToUpdate)
                # print('something updated: ', numberUpdatedVertices)

                # iterations += 1
                if iterations >= paramDict['maxiter']:
                    self.msg('> max iterations exceeded', 'warning')
                    routine = False
                    break
                if processList[-1] > 0 and iterations - processStartIteration >= processList[-1]:
                    self.msg('> max process iteration, next process', 'warning')
                    processNumber += 1
                    break
                if numberUpdatedVertices == 0:
                    self.msg('> no updated vertices !', 'warning')
                    processNumber += 1
                    break

        # DENSIFICATION

        for densificationIteration in range(paramDict['densification']):
            self.msg('\n> densification {}'.format(iterations), 'info')
            iterations += 1

            self.generate_isobaths5()
            if statistics:
                self.generate_statistics()

            edgeTriangles = set()
            edgeTrianglesExtracted = False

            trianglesToDensify = set()
            extendedTrianglesToDensify = set()

            for densMetric in paramDict['densification_process']:
                print(densMetric)

                if densMetric[0] == 'angularity':
                    sharp_extendedConflictingTriangles = set()
                    sharpPointsDict, allSharpPoints = self.check_isobath_angularity(
                        threshold=angularity_threshold)
                    sharp_conflictingTriangles = self.get_all_immediate_triangles(
                        sharpPointsDict)
                    if densMetric[1] == 'r':
                        sharp_extendedConflictingTriangles = self.get_triangle_rings_around_triangles(
                            sharp_conflictingTriangles, rings=densMetric[2])
                    trianglesToDensify.update(sharp_conflictingTriangles)
                    extendedTrianglesToDensify.update(sharp_extendedConflictingTriangles)
                    print('sharp triangles: ', len(sharp_conflictingTriangles))

                elif densMetric[0] == 'aspect-edges':
                    aspect_extendedConflictingTriangles = set()
                    if not edgeTrianglesExtracted:
                        edgeTriangles = self.get_all_edge_triangles()
                        edgeTrianglesExtracted = True
                    aspect_conflictingTriangles = self.check_triangle_aspect_ratio(
                        edgeTriangles, aspect_threshold)
                    if densMetric[1] == 'r':
                        aspect_extendedConflictingTriangles = self.get_triangle_rings_around_triangles(
                            aspect_conflictingTriangles, rings=densMetric[2])
                    trianglesToDensify.update(aspect_conflictingTriangles)
                    extendedTrianglesToDensify.update(aspect_extendedConflictingTriangles)
                    print('aspect triangles: ', len(aspect_conflictingTriangles))

                elif densMetric[0] == 'size-edges':
                    size_extendedConflictingTriangles = set()
                    if not edgeTrianglesExtracted:
                        edgeTriangles = self.get_all_edge_triangles()
                        edgeTrianglesExtracted = True

                    size_conflictingTriangles = self.check_triangle_size(
                        edgeTriangles, size_threshold)
                    if densMetric[1] == 'r':
                        size_extendedConflictingTriangles = self.get_triangle_rings_around_triangles(
                            size_conflictingTriangles, rings=densMetric[2])
                    trianglesToDensify.update(size_conflictingTriangles)
                    extendedTrianglesToDensify.update(size_extendedConflictingTriangles)
                    print('size triangles: ', len(size_conflictingTriangles))

            print('conflictingTriangles ', len(trianglesToDensify))
            print('extendedConflictingTriangles ', len(extendedTrianglesToDensify))

            self.simple_densify_and_rebuild(trianglesToDensify=extendedTrianglesToDensify)

    def start_routine_new(self, paramDict, statistics=False):

        self.msg(
            '\n\n===============================\n       START OF ROUTINE\n===============================\n', 'header')

        # self.classify_nodes()

        # for param in paramDict.keys():
        #     print(param, paramDict[param])

        spurgully_threshold = paramDict['spurgully_threshold']
        spur_threshold = paramDict['spur_threshold']
        gully_threshold = paramDict['gully_threshold']
        angularity_threshold = paramDict['angularity_threshold']
        aspect_threshold = paramDict['aspect_threshold']
        size_threshold = paramDict['size_threshold']
        aggregation_threshold = paramDict['aggregation_threshold']
        min_ring = paramDict['min_ring']
        max_ring = paramDict['max_ring']

        print('========\nthresholds:\nspurgully: {}\nspur: {}\ngully: {}\nangularity: {}\naspect: {}\nsize: {}\naggregation: {}\n========'.format(
            spurgully_threshold, spur_threshold, gully_threshold, angularity_threshold, aspect_threshold, size_threshold, aggregation_threshold))

        iterations = 0

        # PREPASS
        # prepass start statistics
        allVertices = set()
        for tri in self.triangles:
            if 0 not in tri:
                allVertices.update(tri)
        numberUpdatedVerticesPre = 0
        for prepassIteration in range(paramDict['prepass']):
            self.msg('> prepass {}'.format(iterations), 'info')

            # allVertices = self.vertices[1:]
            allVertices = set()
            for tri in self.triangles:
                if 0 not in tri:
                    allVertices.update(tri)
            numberUpdatedVerticesPre = self.smooth_vertices_new(allVertices)

            if statistics:
                trackerDict = {'iterations': iterations,
                               'conflicting_iso_vertices': 0,
                               'conflicting_triangles': 0,
                               'extended_conflicting_triangles': 0,
                               'vertices_to_smooth': len(allVertices),
                               'updated_vertices': numberUpdatedVerticesPre,
                               'conflicting_sharp_vertices': 0,
                               'conflicting_spur_vertices': 0,
                               'conflicting_gully_vertices': 0,
                               'conflicting_sharp_triangles': 0,
                               'conflicting_spur_triangles': 0,
                               'conflicting_gully_triangles': 0}
                self.generate_isobaths5()
                self.generate_statistics(tracker_dict=trackerDict)

            iterations += 1

        routine = True
        ring_range = range(min_ring, max_ring + 1)
        print(list(ring_range))
        processNumber = 0
        metricsToTest = paramDict['process']

        # start statistics
        conflictingTriangles = set()
        extendedConflictingTriangles = set()
        verticesToUpdate = set()
        numberUpdatedVertices = numberUpdatedVerticesPre
        conflictingSharpVertices = 0
        conflictingSpurVertices = 0
        conflictingGullyVertices = 0
        # conflictingIsoVertices = 0
        conflictingSharpTriangles = 0
        conflictingSpurTriangles = 0
        conflictingGullyTriangles = 0

        while routine:

            if processNumber >= len(ring_range):
                self.msg('\nmax rings reached', 'warning')
                break
            if iterations >= paramDict['maxiter']:
                self.msg('> max iterations exceeded', 'warning')
                routine = False
                break

            currentRings = ring_range[processNumber]

            self.msg('\n===============\nNEW STEP r{} i{}\n===============\n'.format(
                currentRings, iterations), 'header')
            # print('currentRings: ', currentRings)

            self.generate_isobaths5()

            # Conflicting triangles
            conflictingTriangles = set()
            extendedConflictingTriangles = set()
            verticesToUpdate = set()
            conflictingSharpVertices = 0
            conflictingSpurVertices = 0
            conflictingGullyVertices = 0
            conflictingSharpTriangles = 0
            conflictingSpurTriangles = 0
            conflictingGullyTriangles = 0

            # AGGREGATION
            metricTypeList = [val[0] for val in metricsToTest]
            if 'aggregation' in metricTypeList:
                # this is a small subroutinge, it will not generate new
                # iteration count, nor statistics
                # self.msg('AGGREGATION', 'warning')

                aggregationSelection = metricsToTest[metricTypeList.index('aggregation')][1]

                connectingNodes = self.check_aggregation(
                    nodeIds=[], threshold=aggregation_threshold, extendByIntersectedTriangles=aggregationSelection)
                # connectingNodes is a dict of conenctingNodeIds, being
                # the bridges between multiple peaks. It also has pointers
                # to vertices to be displaces, and a value to
                if len(connectingNodes) == 0:
                    print('no aggregation')
                else:
                    # print(connectingNodes)
                    print('aggregating nodes..')
                    numberDisplacedVertices = self.displace_vertices_helper(connectingNodes)
                    print('displaced vertices: ', numberDisplacedVertices)

                    if numberDisplacedVertices > 0:
                        # if aggregated something, it will redo the entire
                        # routine loop.
                        self.msg('some vertices displaced, redoing loop', 'header')
                        continue
                    else:
                        # Else it will just continue with the smoothing routine
                        # self.generate_isobaths5()
                        print('no vertices displaced, continuing routine')
                        pass

            # Calculate metrics
            spurGullyCalculated = False
            for metricDefinition in metricsToTest:
                # print(metricDefinition)

                if metricDefinition[0] == 'angularity':
                    sharpPointsDict, allSharpPoints = self.check_isobath_angularity(
                        threshold=angularity_threshold)
                    conflictingSharpVertices = len(allSharpPoints)
                    sharp_conflictingTriangles = self.get_all_immediate_triangles(
                        sharpPointsDict)
                    conflictingSharpTriangles = len(sharp_conflictingTriangles)
                    # if currentRings > 0:
                    sharp_extendedConflictingTriangles = self.get_triangle_rings_around_triangles(
                        sharp_conflictingTriangles, rings=currentRings)
                    conflictingTriangles.update(sharp_conflictingTriangles)
                    extendedConflictingTriangles.update(sharp_extendedConflictingTriangles)
                    print('sharp points: ', len(allSharpPoints))

                elif metricDefinition[0] == 'spurs':
                    if not spurGullyCalculated:
                        spursDict, gullyDict = self.check_spurs_gullys_2(
                            threshold=spurgully_threshold, spurThreshold=spur_threshold, gullyThreshold=gully_threshold)
                        spurGullyCalculated = True

                    conflictingSpurVertices = set()
                    for skey in spursDict.keys():
                        conflictingSpurVertices.update(spursDict[skey])
                    conflictingSpurVertices = len(conflictingSpurVertices)

                    spurs_conflictingTriangles = self.get_all_immediate_triangles(
                        spursDict)
                    conflictingSpurTriangles = len(spurs_conflictingTriangles)
                    # if currentRings > 0:
                    spurs_extendedConflictingTriangles = self.get_triangle_rings_around_triangles(
                        spurs_conflictingTriangles, rings=currentRings)
                    conflictingTriangles.update(spurs_conflictingTriangles)
                    extendedConflictingTriangles.update(spurs_extendedConflictingTriangles)
                    print('spur triangles: ', len(spurs_conflictingTriangles))
                elif metricDefinition[0] == 'gullys':
                    if not spurGullyCalculated:
                        spursDict, gullyDict = self.check_spurs_gullys_2(
                            threshold=spurgully_threshold, spurThreshold=spur_threshold, gullyThreshold=gully_threshold)
                        spurGullyCalculated = True

                    conflictingGullyVertices = set()
                    for skey in gullyDict.keys():
                        conflictingGullyVertices.update(gullyDict[skey])
                    conflictingGullyVertices = len(conflictingGullyVertices)

                    gully_conflictingTriangles = self.get_all_immediate_triangles(
                        gullyDict)
                    conflictingGullyTriangles = len(gully_conflictingTriangles)
                    # if currentRings > 0:
                    gully_extendedConflictingTriangles = self.get_triangle_rings_around_triangles(
                        gully_conflictingTriangles, rings=currentRings)
                    conflictingTriangles.update(gully_conflictingTriangles)
                    extendedConflictingTriangles.update(gully_extendedConflictingTriangles)
                    print('gully triangles: ', len(gully_conflictingTriangles))

            print('conflictingTriangles ', len(conflictingTriangles))
            print('extendedConflictingTriangles ', len(extendedConflictingTriangles))

            if len(extendedConflictingTriangles) == 0:
                self.msg('> no conflicts found, ending routine', 'warning')
                break

            verticesToUpdate = self.get_vertices_from_triangles(extendedConflictingTriangles)
            numberUpdatedVertices = self.smooth_vertices_new(
                verticesToUpdate)

            if statistics:
                self.generate_isobaths5()
                trackerDict = {'iterations': iterations,
                               'conflicting_iso_vertices': conflictingSharpVertices + conflictingSpurVertices + conflictingGullyVertices,
                               'conflicting_triangles': len(conflictingTriangles),
                               'extended_conflicting_triangles': len(extendedConflictingTriangles),
                               'vertices_to_smooth': len(verticesToUpdate),
                               'updated_vertices': numberUpdatedVertices,
                               'conflicting_sharp_vertices': conflictingSharpVertices,
                               'conflicting_spur_vertices': conflictingSpurVertices,
                               'conflicting_gully_vertices': conflictingGullyVertices,
                               'conflicting_sharp_triangles': conflictingSharpTriangles,
                               'conflicting_spur_triangles': conflictingSpurTriangles,
                               'conflicting_gully_triangles': conflictingGullyTriangles}
                self.generate_statistics(tracker_dict=trackerDict)

            iterations += 1

            if numberUpdatedVertices == 0:
                self.msg('> no updated vertices ! Adding a ring', 'warning')
                processNumber += 1
            else:
                self.msg('> setting process back to zero', 'info')
                processNumber = 0

        # DENSIFICATION

        for densificationIteration in range(paramDict['densification']):
            self.msg('\n> densification {}'.format(iterations), 'info')
            iterations += 1

            self.generate_isobaths5()
            if statistics:
                self.generate_statistics()

            edgeTriangles = set()
            edgeTrianglesExtracted = False

            trianglesToDensify = set()
            extendedTrianglesToDensify = set()

            for densMetric in paramDict['densification_process']:
                print(densMetric)

                if densMetric[0] == 'angularity':
                    sharp_extendedConflictingTriangles = set()
                    sharpPointsDict, allSharpPoints = self.check_isobath_angularity(
                        threshold=angularity_threshold)
                    sharp_conflictingTriangles = self.get_all_immediate_triangles(
                        sharpPointsDict)
                    if densMetric[1] == 'r':
                        sharp_extendedConflictingTriangles = self.get_triangle_rings_around_triangles(
                            sharp_conflictingTriangles, rings=densMetric[2])
                    trianglesToDensify.update(sharp_conflictingTriangles)
                    extendedTrianglesToDensify.update(sharp_extendedConflictingTriangles)
                    print('sharp triangles: ', len(sharp_conflictingTriangles))

                elif densMetric[0] == 'aspect-edges':
                    aspect_extendedConflictingTriangles = set()
                    if not edgeTrianglesExtracted:
                        edgeTriangles = self.get_all_edge_triangles()
                        edgeTrianglesExtracted = True
                    aspect_conflictingTriangles = self.check_triangle_aspect_ratio(
                        edgeTriangles, aspect_threshold)
                    if densMetric[1] == 'r':
                        aspect_extendedConflictingTriangles = self.get_triangle_rings_around_triangles(
                            aspect_conflictingTriangles, rings=densMetric[2])
                    trianglesToDensify.update(aspect_conflictingTriangles)
                    extendedTrianglesToDensify.update(aspect_extendedConflictingTriangles)
                    print('aspect triangles: ', len(aspect_conflictingTriangles))

                elif densMetric[0] == 'size-edges':
                    size_extendedConflictingTriangles = set()
                    if not edgeTrianglesExtracted:
                        edgeTriangles = self.get_all_edge_triangles()
                        edgeTrianglesExtracted = True

                    size_conflictingTriangles = self.check_triangle_size(
                        edgeTriangles, size_threshold)
                    if densMetric[1] == 'r':
                        size_extendedConflictingTriangles = self.get_triangle_rings_around_triangles(
                            size_conflictingTriangles, rings=densMetric[2])
                    trianglesToDensify.update(size_conflictingTriangles)
                    extendedTrianglesToDensify.update(size_extendedConflictingTriangles)
                    print('size triangles: ', len(size_conflictingTriangles))

            print('conflictingTriangles ', len(trianglesToDensify))
            print('extendedConflictingTriangles ', len(extendedTrianglesToDensify))

            self.simple_densify_and_rebuild(trianglesToDensify=extendedTrianglesToDensify)

        self.msg(
            '\n\n===============================\n       END OF ROUTINE\n===============================\n\n', 'header')

    def get_all_edge_triangles(self):

        allEdgeTriangles = set()
        for edgeId in self.graph['edges'].keys():
            edgeTriangles = self.get_edge_triangles(edgeId)
            allEdgeTriangles.update(edgeTriangles)

        return allEdgeTriangles

    def check_triangle_size(self, trianglesToTest, sizeThreshold):

        conflictingTriangles = set()
        for triangle in trianglesToTest:
            if self.triangle_area(triangle) > sizeThreshold:
                conflictingTriangles.add(triangle)

        return conflictingTriangles

    def check_triangle_aspect_ratio(self, trianglesToTest, aspectThreshold):

        conflictingTriangles = set()
        for triangle in trianglesToTest:
            if self.triangle_aspect_ratio(triangle) > aspectThreshold:
                conflictingTriangles.add(triangle)

        return conflictingTriangles

    # ==================================================================== #
    #
    #   NOT IN USE  /  NOT IN USE  /  NOT IN USE  /  NOT IN USE
    #
    # ==================================================================== #

    def old_functions(self):
        '''
        def adjacent_triangles_in_set(self, triangle, lookupSet):
            adjacentTriangles = []
            addedVertices = []
            for vId in triangle:
                if len(addedVertices) == 3:
                    break
                else:
                    for incidentTriangle in self.triangulation.incident_triangles_to_vertex(vId):
                        if len(set(triangle).intersection(incidentTriangle)) == 2 and set(incidentTriangle).difference(triangle) not in addedVertices:
                            if tuple(self.pseudo_triangle(incidentTriangle)) in lookupSet:
                                adjacentTriangles.append(self.pseudo_triangle(incidentTriangle))
                                addedVertices.append(set(incidentTriangle).difference(triangle))

            return adjacentTriangles

        def index_region_triangles(self):
            self.msg('> indexing region triangles...', 'info')
            for triangle in self.triangles:
                min, max = self.minmax_from_triangle(triangle)
                # print(min, max)
                for index in range(bisect.bisect_left(self.isobathValues, min), bisect.bisect_left(self.isobathValues, max) + 1):
                    # print(self.regions[index])
                    self.triangleRegions[index].append(triangle)
            # print(self.triangleRegions)
            self.msg('> triangles indexed in regions', 'info')

        def locate_point_in_set(self, point, lookupSet):
            print(self.pseudo_triangle(self.triangulation.locate(point[0], point[1])))

        def create_tr_graph(self):
            self.trGraph.initialize_graph(self.triangulation)
            self.trGraph.vertexDict = self.vertexDict
            self.trGraph.build_graph()

        def generate_walker_graph(self, triangle, interval, nodeId):
            # NOT IN USE ANYMORE: Max recursion limit
            for neighbor in self.adjacent_triangles(triangle):
                if interval in self.find_intervals(neighbor) and not self.triangle_in_node(neighbor, nodeId):
                    # print(neighbor)
                    self.add_triangle_to_node(neighbor, nodeId)
                    self.generate_walker_graph(neighbor, interval, nodeId)

        def iterative_generator(self, triangle, interval, nodeId):
            print('--itergenerator--', interval)
            for neighbor in self.adjacent_triangles(triangle):
                neighborIntervals = self.find_intervals(neighbor)
                print(neighbor, neighborIntervals)

                if interval in neighborIntervals and not self.triangle_in_node(neighbor, nodeId):
                    self.add_triangle_to_queue(neighbor, nodeId, 'current')
                    print('current')

                if interval+1 in neighborIntervals:
                    alreadyDeeper = False
                    for deeperNeighbor in self.get_neighboring_nodes(nodeId, 'deep'):
                        if self.triangle_in_node(neighbor, nodeId):
                            alreadyDeeper = True
                            print('adeep')
                            self.remove_triangle_from_queue(neighbor, deeperNeighbor, 'shallow')
                            self.remove_triangle_from_queue(neighbor, nodeId, 'deep')
                    if not alreadyDeeper:
                        self.add_triangle_to_queue(neighbor, nodeId, 'deep')
                        print('deep')

                if interval-1 in neighborIntervals:
                    alreadyShallower = False
                    for shallowerNeighbor in self.get_neighboring_nodes(nodeId, 'shallow'):
                        if self.triangle_in_node(neighbor, nodeId):
                            alreadyShallower = True
                            print('ashallow')
                            self.remove_triangle_from_queue(neighbor, shallowerNeighbor, 'deep')
                            self.remove_triangle_from_queue(neighbor, nodeId, 'shallow')
                    if not alreadyShallower:
                        self.add_triangle_to_queue(neighbor, nodeId, 'shallow')
                        print('shallow')

        def clean_queues(self, nodeId):
            deeperNeighbors = self.get_neighboring_nodes(nodeId, 'deep')
            shallowerNeighbors = self.get_neighboring_nodes(nodeId, 'shallow')
            deepQueue = self.get_queue(nodeId, 'deep')
            shallowQueue = self.get_queue(nodeId, 'shallow')

            for deepNeighbor in deeperNeighbors:
                deepNeighborShallowQueue = self.get_queue(deepNeighbor, 'shallow')
                for triangle in deepQueue.copy():
                    if triangle in deepNeighborShallowQueue:
                        self.remove_triangle_from_queue(triangle, deepNeighbor, 'shallow')
                        self.remove_triangle_from_queue(triangle, nodeId, 'deep')
            for shallowNeighbor in shallowerNeighbors:
                shallowNeighborDeepQueue = self.get_queue(shallowNeighbor, 'deep')
                for triangle in shallowQueue.copy():
                    if triangle in shallowNeighborDeepQueue:
                        self.remove_triangle_from_queue(triangle, shallowNeighbor, 'deep')
                        self.remove_triangle_from_queue(triangle, nodeId, 'shallow')

        def expand_node(self, nodeId, interval):
            while len(self.get_queue(nodeId, 'current')):
                for triangle in self.get_queue(nodeId, 'current').copy():
                    self.add_triangle_to_node(triangle, nodeId)
                    self.remove_triangle_from_queue(triangle, nodeId, 'current')
                    self.iterative_generator(triangle, interval, nodeId)

            self.clean_queues(nodeId)

        def go_deeper(self, nodeId, interval):
            for tri in self.get_queue(nodeId, 'deep'):
                break
            deeperNode = self.add_triangle_to_new_node(interval+1, tri)
            self.add_new_edge(nodeId, deeperNode)
            deeperInterval = self.get_interval_from_node(deeperNode)

            self.iterative_generator(tri, deeperInterval, deeperNode)
            self.expand_node(deeperNode, deeperInterval)

        def go_shallower(self, nodeId, interval):
            for tri in self.get_queue(nodeId, 'shallow'):
                break
            shallowerNode = self.add_triangle_to_new_node(interval-1, tri)
            self.add_new_edge(shallowerNode, nodeId)
            shallowerInterval = self.get_interval_from_node(shallowerNode)

            self.iterative_generator(tri, shallowerInterval, shallowerNode)
            self.expand_node(shallowerNode, shallowerInterval)

        def grow_node(self, nodeId):
            nodeInterval = self.get_interval_from_node(nodeId)
            print('nodeId: ', nodeId, 'nodeInterval: ', nodeInterval)
            trianglesInNode = self.get_triangles(nodeId)

            additions = True
            visitedTriangles = set()
            while additions:
                addedTriangles = 0
                for triangle in trianglesInNode.copy():
                    if triangle:  # not in visitedTriangles:
                        for neighbor in self.adjacent_triangles(triangle):
                            if 0 in neighbor:
                                break
                            if tuple(self.pseudo_triangle(neighbor)) not in visitedTriangles:
                                visitedTriangles.add(tuple(self.pseudo_triangle(neighbor)))

                                deepTracker = False
                                shallowTracker = False

                                # same interval
                                if nodeInterval in self.find_intervals(neighbor) and not self.triangle_in_node(neighbor, nodeId):
                                    self.add_triangle_to_node(neighbor, nodeId)
                                    addedTriangles += 1

                                # deeper interval
                                # and not self.triangle_in_queue(neighbor, nodeId, 'deep'):
                                if nodeInterval + 1 in self.find_intervals(neighbor):
                                    for deeperNode in self.get_neighboring_nodes(nodeId, 'deep'):
                                        if self.triangle_in_queue(neighbor, deeperNode, 'shallow'):
                                            self.remove_triangle_from_queue(
                                                neighbor, deeperNode, 'shallow')
                                            # self.remove_triangle_from_queue(neighbor, nodeId, 'deep')
                                            deepTracker = True
                                            # print('remove')
                                    if not deepTracker:
                                        self.add_triangle_to_queue(neighbor, nodeId, 'deep')
                                        self.unfinishedDeep.add(nodeId)
                                        addedTriangles += 1
                                        # print('not remove')

                                # shallower interval
                                # and not self.triangle_in_queue(neighbor, nodeId, 'shallow'):
                                if nodeInterval - 1 in self.find_intervals(neighbor):
                                    for shallowerNode in self.get_neighboring_nodes(nodeId, 'shallow'):
                                        if self.triangle_in_queue(neighbor, shallowerNode, 'deep'):
                                            self.remove_triangle_from_queue(
                                                neighbor, shallowerNode, 'deep')
                                            # self.remove_triangle_from_queue(neighbor, nodeId, 'shallow')
                                            shallowTracker = True
                                            # print('remove')
                                    if not shallowTracker:
                                        self.add_triangle_to_queue(neighbor, nodeId, 'shallow')
                                        self.unfinishedShallow.add(nodeId)
                                        addedTriangles += 1
                                        # print('not remove')
                # print(addedTriangles)
                if not addedTriangles:
                    additions = False

        def grow_deeper(self, nodeId):
            for triangle in self.get_queue(nodeId, 'deep'):
                break
            currentInterval = self.get_interval_from_node(nodeId)
            deeperInterval = currentInterval + 1

            nodeTracker = False
            neighbors = self.get_neighboring_nodes(nodeId, 'deep')
            for neighbor in neighbors:
                if self.triangle_in_node(triangle, neighbor):
                    nodeTracker = True
            if not nodeTracker:
                deeperNode = self.add_triangle_to_new_node(deeperInterval, triangle)
                self.remove_triangle_from_queue(triangle, nodeId, 'deep')
                self.add_new_edge(nodeId, deeperNode)

                self.grow_node(deeperNode)

        def grow_shallower(self, nodeId):
            for triangle in self.get_queue(nodeId, 'shallow'):
                break
            currentInterval = self.get_interval_from_node(nodeId)
            shallowerInterval = currentInterval - 1

            nodeTracker = False
            neighbors = self.get_neighboring_nodes(nodeId, 'shallow')
            for neighbor in neighbors:
                if self.triangle_in_node(triangle, neighbor):
                    nodeTracker = True
            if not nodeTracker:
                shallowerNode = self.add_triangle_to_new_node(shallowerInterval, triangle)
                self.remove_triangle_from_queue(triangle, nodeId, 'shallow')
                self.add_new_edge(shallowerNode, nodeId)

                self.grow_node(shallowerNode)

        def adjacent_triangle_in_set_with_edge(self, triangle, lookupSet, edge):
            # print(triangle, edge)
            adjacentTriangles = []
            addedVertices = []

            for vertex in edge:
                for incidentTriangle in self.triangulation.incident_triangles_to_vertex(vertex):
                    # print(incidentTriangle)
                    if len(set(incidentTriangle).intersection(edge)) == 2:
                        # print(incidentTriangle)
                        if len(set(incidentTriangle).intersection(triangle)) != 3:
                            if tuple(self.pseudo_triangle(incidentTriangle)) in lookupSet:
                                # print(incidentTriangle)
                                return tuple(self.pseudo_triangle(incidentTriangle))

            return False

            # for vId in triangle:
            #     if len(addedVertices) == 3:
            #         break
            #     else:
            #         for incidentTriangle in self.triangulation.incident_triangles_to_vertex(vId):
            #             # print('inc: ', incidentTriangle)
            #             if len(set(triangle).intersection(incidentTriangle)) == 2 and set(incidentTriangle).difference(triangle) not in addedVertices:
            #                 if tuple(self.pseudo_triangle(incidentTriangle)) in lookupSet:
            #                     adjacentTriangles.append(self.pseudo_triangle(incidentTriangle))
            #                     addedVertices.append(set(incidentTriangle).difference(triangle))
            #
            # for triangle in adjacentTriangles:
            #     # print('adj:', triangle)
            #     if len(set(triangle).intersection(edge)) == 2:
            #         return tuple(self.pseudo_triangle(triangle))

            # return False

            # return adjacentTriangles
            pass

        def generate_isobaths3(self, edgeIds=[]):
            if len(edgeIds) == 0:
                edgeIds = list(self.graph['edges'].keys())

            for edge in edgeIds:
                self.msg('--new edge', 'header')
                isoValue = self.graph['edges'][edge]['value']
                print('isoValue: ', isoValue)

                edgeTriangles = self.get_edge_triangles(edge)
                for triangle in edgeTriangles:
                    intersections, isPoint = self.check_triangle_vertex_intersections_with_value(
                        triangle, isoValue)
                    if intersections == 0:
                        startingTriangle = triangle
                        break
                print(startingTriangle)

                isobathSegments = []
                visitedTriangles = set()

                segmentIntersections = self.get_intersected_segments(
                    startingTriangle, isoValue, 'full')
                isobathSegments.append(segmentIntersections[0])
                isobathSegments.append(segmentIntersections[1])
                visitedTriangles.add(startingTriangle)
                nextTriangle = startingTriangle

                # print(isobathSegments)

                finished = False
                i = 0
                while not finished:
                    # print('---New Loop')
                    if len(segmentIntersections) == 2:
                        # print('find neighboring edge')
                        nextTriangle = self.adjacent_triangle_in_set_with_edge(
                            nextTriangle, edgeTriangles.difference(visitedTriangles), segmentIntersections[1])
                        if not nextTriangle:
                            # couldnt find a satisfying neighbor (end of sequence)
                            print('end of sequence')
                            # finished = True
                            break

                        # print(nextTriangle)
                        intersections, isPoint = self.check_triangle_vertex_intersections_with_value(
                            nextTriangle, isoValue)
                        # print(intersections, isPoint, nextTriangle)

                        if intersections == 0:
                            segmentIntersections = self.get_intersected_segments(
                                nextTriangle, isoValue, 'full')
                            isobathSegments.append(segmentIntersections[1])
                            visitedTriangles.add(nextTriangle)
                        elif intersections == 1:
                            segmentIntersections == self.get_intersected_segments(
                                nextTriangle, isoValue, 'nextPoint')
                            isobathSegments.append(segmentIntersections[0])
                            visitedTriangles.add(nextTriangle)

                    elif len(segmentIntersections) == 1:
                        print('finding neighboring points')

                        # print(isobathSegments)

                    if len(edgeTriangles.difference(visitedTriangles)) == 0:
                        print('every edge triangle visited')
                        finished = True
                    i += 0
                    if i > 2:
                        finished = True

                isoGeom = []
                for intersection in isobathSegments:
                    # print(intersection)
                    if len(intersection) == 1:
                        geom = self.triangulation.get_point(intersection[0])
                        isoGeom.append([geom[0], geom[1]])
                    else:
                        geomOne = self.triangulation.get_point(intersection[0])
                        geomTwo = self.triangulation.get_point(intersection[1])
                        xOne, yOne, zOne = geomOne[0], geomOne[1], self.get_z(
                            intersection[0], idOnly=True)
                        xTwo, yTwo, zTwo = geomTwo[0], geomTwo[1], self.get_z(
                            intersection[1], idOnly=True)
                        if xOne == xTwo:
                            x = round(xOne, 3)
                            y = round(yOne + ((isoValue-zOne)/(zTwo-zOne)) * (yTwo-yOne), 3)
                        else:
                            x = round((isoValue*xTwo-isoValue*xOne- \
                                      zOne*xTwo+zTwo*xOne)/(zTwo-zOne), 3)
                            y = round((x*(yTwo-yOne)-xOne*yTwo+xTwo*yOne)/(xTwo-xOne), 3)
                        isoGeom.append([x, y])

                self.graph['edges'][edge]['geom'] = isoGeom
            self.export_all_isobaths()

        def establish_node(self, nodeId):
            nodeInterval = self.get_interval_from_node(nodeId)
            # print('nodeId: ', nodeId, 'nodeInterval: ', nodeInterval)
            trianglesInNode = self.get_triangles(nodeId)

            visitedTriangles = set()
            adding = True
            while adding:
                addedTriangles = 0
                for triangle in trianglesInNode.copy():
                    for neighbor in self.adjacent_triangles(triangle):
                        if 0 in neighbor:
                            continue
                        # if len(self.find_intervals(neighbor)) != 1:
                        #     continue
                        if tuple(neighbor) not in visitedTriangles:
                            visitedTriangles.add(tuple(neighbor))
                            # print(neighbor)

                            # same interval
                            if nodeInterval in self.find_intervals(neighbor) and not self.triangle_in_node(neighbor, nodeId):
                                # if not self.saddle_test(triangle, neighbor, nodeInterval):
                                self.add_triangle_to_node(neighbor, nodeId)
                                addedTriangles += 1
                                # else:
                                #     visitedTriangles.remove(tuple(neighbor))

                            # deeper interval
                            deepTracker = False
                            if nodeInterval + 1 in self.find_intervals(neighbor):
                                for deeperNode in self.get_neighboring_nodes(nodeId, 'deep'):
                                    if self.triangle_in_queue(neighbor, deeperNode, 'shallow'):
                                        self.remove_triangle_from_queue(
                                            neighbor, deeperNode, 'shallow')
                                        deepTracker = True
                                if not deepTracker:
                                    self.add_triangle_to_queue(neighbor, nodeId, 'deep')
                                    addedTriangles += 1
                                    # visitedTriangles.add(tuple(neighbor))

                            # shallower interval
                            shallowTracker = False
                            if nodeInterval - 1 in self.find_intervals(neighbor):
                                for shallowerNode in self.get_neighboring_nodes(nodeId, 'shallow'):
                                    if self.triangle_in_queue(neighbor, shallowerNode, 'deep'):
                                        self.remove_triangle_from_queue(
                                            neighbor, shallowerNode, 'deep')
                                        shallowTracker = True
                                if not shallowTracker:
                                    self.add_triangle_to_queue(neighbor, nodeId, 'shallow')
                                    addedTriangles += 1
                                    # visitedTriangles.add(tuple(neighbor))

                            # for neighboringNode in self.get_neighboring_nodes(nodeId, 'deep'):
                            #     if self.triangle_in_queue(neighbor, neighboringNode, 'shallow'):
                            #         self.remove_triangle_from_queue(
                            #             neighbor, neighboringNode, 'shallow')
                            #
                            # for neighboringNode in self.get_neighboring_nodes(nodeId, 'shallow'):
                            #     if self.triangle_in_queue(neighbor, neighboringNode, 'deep'):
                            #         self.remove_triangle_from_queue(neighbor, neighboringNode, 'deep')

                if not addedTriangles:
                    adding = False

            self.check_unfinished(nodeId)

        def resolve_queues(self, nodeId):
            nodeInterval = self.get_interval_from_node(nodeId)
            deeperInterval = nodeInterval + 1
            shallowerInterval = nodeInterval - 1
            # deeperNodes = self.get_neighboring_nodes(nodeId, 'deep')
            # shallowerNodes = self.get_neighboring_nodes(nodeId, 'shallow')

            resolved = False
            while not resolved:
                # print('deepQueue: ', len(self.get_queue(nodeId, 'deep')))
                if not len(self.get_queue(nodeId, 'deep')):
                    # print('resolveTrigger')
                    resolved = True

                triangle = 0
                for triangle in self.get_queue(nodeId, 'deep'):
                    break
                if triangle:
                    triangleTracker = False
                    for neighboringNode in self.get_neighboring_nodes(nodeId, 'deep'):
                        if self.triangle_in_node(triangle, neighboringNode):
                            self.remove_triangle_from_queue(triangle, nodeId, 'deep')
                            triangleTracker = True
                    if not triangleTracker:
                        deeperNode = self.add_triangle_to_new_node(deeperInterval, triangle)
                        self.remove_triangle_from_queue(triangle, nodeId, 'deep')
                        self.add_new_edge(nodeId, deeperNode)
                        self.establish_node(deeperNode)

                    # print('deepQueue: ', len(self.get_queue(nodeId, 'deep')))
                    # if not len(self.get_queue(nodeId, 'deep')):
                    #     # print('resolveTrigger')
                    #     resolved = True
                else:
                    # print('resolveTrigger')
                    resolved = True

            resolved = False
            while not resolved:
                # print('shallowQueue: ', len(self.get_queue(nodeId, 'deep')))
                if not len(self.get_queue(nodeId, 'shallow')):
                    # print('resolveTrigger')
                    resolved = True

                triangle = 0
                for triangle in self.get_queue(nodeId, 'shallow'):
                    break
                if triangle:
                    triangleTracker = False
                    for neighboringNode in self.get_neighboring_nodes(nodeId, 'shallow'):
                        if self.triangle_in_node(triangle, neighboringNode):
                            self.remove_triangle_from_queue(triangle, nodeId, 'shallow')
                            triangleTracker = True
                    if not triangleTracker:
                        shallowerNode = self.add_triangle_to_new_node(shallowerInterval, triangle)
                        self.remove_triangle_from_queue(triangle, nodeId, 'shallow')
                        self.add_new_edge(shallowerNode, nodeId)
                        self.establish_node(shallowerNode)

                    # print('shallowQueue: ', len(self.get_queue(nodeId, 'deep')))
                    # if not len(self.get_queue(nodeId, 'shallow')):
                    #     print('resolveTrigger')
                    #     resolved = True
                else:
                    # print('resolveTrigger')
                    resolved = True

            self.check_unfinished(nodeId)

        def build_graph(self):
            self.msg('> building triangle region graph...', 'info')
            for startingTriangle in self.triangles:
                if len(self.find_intervals(startingTriangle)) == 1:
                    break
            # startingTriangle = self.triangles[23]
            # startingTriangle = self.triangles[0]

            print('\n=======starter=======')
            # print(self.minmax_from_triangle(startingTriangle))
            print('starting triangle: ', startingTriangle)
            print('starting interval: ', self.find_intervals(startingTriangle))
            print('=====================')

            intervalStart = self.find_intervals(startingTriangle)[0]
            currentNodeId = self.add_triangle_to_new_node(intervalStart, startingTriangle)

            self.establish_node(currentNodeId)
            self.check_unfinished(currentNodeId)

            finished = False
            i = 0
            while not finished:
                for node in self.nodeQueue.copy():
                    print('==============resolving node: ', node)
                    print('nodeQueue: ', self.nodeQueue)
                    self.resolve_queues(node)
                    # i += 1
                    # if i == 30:
                    #     finished = True
                if not len(self.nodeQueue):
                    finished = True

            # self.clean_nodes()

            # self.load_node_queues(currentNodeId)

            ###################
            # self.grow_node(currentNodeId)
            #
            # unfinished = True
            # i = 0
            # while unfinished:
            #     # deepsTracker = len(self.unfinishedDeep)
            #     #
            #     # for unfinishedDeep in self.unfinishedDeep.copy():
            #     #     self.grow_deeper(unfinishedDeep)
            #     #
            #     # if len(self.unfinishedDeep) == deepsTracker:
            #     #     unfinished = False
            #     shallowsTracker = len(self.unfinishedShallow)
            #     deepsTracker = len(self.unfinishedDeep)
            #
            #     for unfinishedShallow in self.unfinishedShallow.copy():
            #         self.grow_shallower(unfinishedShallow)
            #         if not len(self.get_queue(unfinishedShallow, 'shallow')):
            #             self.unfinishedShallow.remove(unfinishedShallow)
            #
            #     for unfinishedDeep in self.unfinishedDeep.copy():
            #         self.grow_deeper(unfinishedDeep)
            #         if not len(self.get_queue(unfinishedDeep, 'deep')):
            #             self.unfinishedDeep.remove(unfinishedDeep)
            #
            #     if len(self.unfinishedShallow) == shallowsTracker and len(self.unfinishedDeep) == deepsTracker:
            #         print('triggered')
            #         unfinished = False
            #     # if i == 1:
            #     #     unfinished = False
            #
            #     print(self.unfinishedShallow)
            #     print(self.unfinishedDeep)
            #     i += 1
            #
            #     # unfinished = False
            #
            # print(self.unfinishedShallow)
            # print(self.unfinishedDeep)
            # interval = self.get_interval_from_node(currentNodeId)
            ###################

            ###################
            # self.iterative_generator(startingTriangle, interval, currentNodeId)
            # self.expand_node(currentNodeId, interval)
            # self.go_deeper(currentNodeId, interval)
            # self.go_shallower(currentNodeId, interval)
            ###################

            # self.generate_walker_graph(startingTriangle, interval, currentNodeId)
            # for interval in self.find_intervals(startingTriangle):
            #     currentNodeId = self.add_triangle_to_new_node(interval, startingTriangle)
            #     # self.generate_walker_graph(startingTriangle, interval, currentNodeId)
            #     self.iterative_generator(startingTriangle, interval, currentNodeId)
            #     while len(self.get_queue(currentNodeId, 'current')):
            #         for triangle in self.get_queue(currentNodeId, 'current').copy():
            #             self.add_triangle_to_node(list(triangle), currentNodeId)
            #             self.remove_triangle_from_queue(list(triangle), currentNodeId, 'current')
            #             self.iterative_generator(triangle, interval, currentNodeId)

            # print('----neighbors----')
            # for neighbor in self.adjacent_triangles(startingTriangle):
            #     # print(neighbor, self.find_intervals(neighbor))
            #     # print('pseudo: ', self.pseudo_triangle(neighbor))
            #     print(self.pseudo_triangle(neighbor), self.find_intervals(self.pseudo_triangle(neighbor)))

            # self.add_new_edge(0, 1)

            self.print_graph()
            print('nodeQueue: ', self.nodeQueue)
            self.msg('> triangle region graph created', 'info')
            self.export_all_node_triangles()

        def check_triangle_vertex_intersections_with_value(self, triangle, isoValue):
            isPoint = False

            pointZees = []
            for vId in triangle:
                pointZees.append(self.get_z(vId, idOnly=True))
            intersections = len(set(pointZees).intersection([isoValue]))
            # print(intersections)

            if intersections == 1:
                min, max = self.minmax_from_triangle(triangle)
                print(min, max)
                if min == isoValue or max == isoValue:
                    isPoint = True

            return intersections, isPoint

        def check_unfinished(self, nodeId):
            if len(self.get_queue(nodeId, 'deep')):
                self.unfinishedDeep.add(nodeId)
                self.nodeQueue.add(nodeId)
            else:
                if nodeId in self.unfinishedDeep:
                    self.unfinishedDeep.remove(nodeId)

            if len(self.get_queue(nodeId, 'shallow')):
                self.unfinishedShallow.add(nodeId)
                self.nodeQueue.add(nodeId)
            else:
                if nodeId in self.unfinishedShallow:
                    self.unfinishedShallow.remove(nodeId)

            if not len(self.get_queue(nodeId, 'deep')) and not len(self.get_queue(nodeId, 'shallow')):
                if nodeId in self.nodeQueue:
                    self.nodeQueue.remove(nodeId)

        def clean_nodes(self):
            for nodeId in self.graph['nodes'].keys():
                conflictingTris = set()
                saddleTris = set()
                print(nodeId)
                interval = self.get_interval_from_node(nodeId)
                region = self.regions[interval]
                print(region)
                for triangle in self.get_triangles(nodeId):
                    print(triangle)
                    outsiders = 0
                    conflictingVids = []
                    for vId in triangle:
                        vertexElevation = self.get_z(vId, True)
                        if vertexElevation < region[0] or vertexElevation > region[1]:
                            outsiders += 1
                            conflictingVids.append(vId)
                            print(vertexElevation)

                    if outsiders == 2:
                        conflictingTris.add((min(conflictingVids), max(conflictingVids)))

                        if (min(conflictingVids), max(conflictingVids)) in conflictingTris:
                            saddleTris.add(self.pseudo_triangle(triangle))
                # print(saddleTris)
                # self.msg('I contain a saddle', 'warning')
            pass

        def generate_isobaths2(self, edgeIds=[]):
            if len(edgeIds) == 0:
                edgeIds = list(self.graph['edges'].keys())

            for edge in edgeIds:
                self.msg('--new edge', 'header')
                isoValue = self.graph['edges'][edge]['value']
                print('isoValue: ', isoValue)

                linePoints = []
                edgeTriangles = self.get_edge_triangles(edge)

                for triangle in edgeTriangles:
                    triangleLine = self.contour_triangle(triangle, isoValue)
                    if triangleLine != [0, 0]:
                        # linePoints.append(triangleLine)
                        linePoints.append(geometry.LineString(
                            [[triangleLine[0][0], triangleLine[0][1]], [triangleLine[1][0], triangleLine[1][1]]]))
                # print(linePoints)
                multiLine = geometry.MultiLineString(linePoints)
                mergedLine = ops.linemerge(multiLine)
                self.graph['edges'][edge]['geom'] = mergedLine

            self.export_all_isobaths()

        def generate_isobaths(self, edgeIds=[]):
            # deep=left of the line
            if len(edgeIds) == 0:
                edgeIds = list(self.graph['edges'].keys())

            for edge in edgeIds:
                self.msg('--new edge', 'header')
                isoValue = self.graph['edges'][edge]['value']
                print('isoValue: ', isoValue)

                linePoints = []
                visitedTriangles = set()

                edgeTriangles = self.get_edge_triangles(edge)
                for startingTriangle in edgeTriangles:
                    break
                print(startingTriangle)

                # for vId in startingTriangle:
                #     print(self.triangulation.get_point(vId))

                trianglePoints = self.contour_triangle(startingTriangle, isoValue)
                linePoints.append(trianglePoints[0])
                linePoints.append(trianglePoints[1])
                visitedTriangles.add(self.pseudo_triangle(startingTriangle))
                # print(linePoints)

                nextTriangle = startingTriangle

                finished = False
                while not finished:
                    additions = 0

                    for neighbor in self.adjacent_triangles_in_set(nextTriangle, edgeTriangles.difference(visitedTriangles)):
                        tri = [self.triangulation.get_point(vId) for vId in neighbor]
                        # print('neighbor: ', neighbor)
                        # print('tri: ', tri)
                        # print(point_in_triangle(linePoints[-1], tri))
                        # print(linePoints)
                        if point_in_triangle(linePoints[-1], tri):
                            trianglePoints = self.contour_triangle(neighbor, isoValue)
                            # linePoints.append(trianglePoints[0])
                            linePoints.append(trianglePoints[1])
                            visitedTriangles.add(tuple(self.pseudo_triangle(neighbor)))
                            # print(linePoints)
                            # print(len(edgeTriangles.difference(visitedTriangles)))
                            nextTriangle = neighbor
                            additions += 1

                    if len(edgeTriangles.difference(visitedTriangles)) == 0 or additions == 0:
                        finished = True
                    # print(self.triangulation.locate(linePoints[-1][0], linePoints[-1][1]))
                    # print(point_in_triangle(linePoints[0], tri))

                self.graph['edges'][edge]['geom'] = linePoints

            self.export_all_isobaths()
            # closedLine = True
            # if not closedLine:
            #     pass

            # for vId in startingTriangle:
            #     print(self.get_z(vId, idOnly=True))

            # print(edgeTriangles)
            pass

        def contour_triangle(self, triangle, isoValue):

            triangleVertexZero = self.triangulation.get_point(triangle[0])
            triangleVertexOne = self.triangulation.get_point(triangle[1])
            triangleVertexTwo = self.triangulation.get_point(triangle[2])
            triangleSegments = [[triangleVertexZero, triangleVertexOne],
                                [triangleVertexOne, triangleVertexTwo],
                                [triangleVertexTwo, triangleVertexZero]]
            triangleLine = [0, 0]
            for i, segment in enumerate(triangleSegments):
                xOne, yOne, zOne = segment[0][0], segment[0][1], self.get_z(segment[0])
                xTwo, yTwo, zTwo = segment[1][0], segment[1][1], self.get_z(segment[1])
                # print(xOne, yOne, zOne)
                # print(xTwo, yTwo, zTwo)
                sMin, sMax = min(zOne, zTwo), max(zOne, zTwo)
                if xTwo-xOne == 0:
                    xTwo += 0.0001
                if sMin <= isoValue <= sMax:
                    x = round((isoValue*xTwo-isoValue*xOne-zOne*xTwo+zTwo*xOne)/(zTwo-zOne), 3)
                    y = round((x*(yTwo-yOne)-xOne*yTwo+xTwo*yOne)/(xTwo-xOne), 3)
                    # print(x, y)
                    if zOne > zTwo:
                        triangleLine[0] = (x, y)
                    else:
                        triangleLine[1] = (x, y)
                        nextSegment = i

            # nextSegment = {triangle[nextSegment], triangle[(nextSegment+1) % 2]}
            # print(nextSegment)

            return triangleLine

        def get_intersected_segments(self, triangle, isoValue, type):
            if type == 'full':
                # full intersection model
                segmentIntersections = [0, 0]
                for i in range(3):
                    # print('segment: ', i)
                    segment = [triangle[i], triangle[(i+1) % 3]]
                    zOne, zTwo = self.get_z(segment[0], idOnly=True), self.get_z(
                        segment[1], idOnly=True)
                    sMin, sMax = min(zOne, zTwo), max(zOne, zTwo)
                    if sMin < isoValue < sMax:
                        # print('intersects!')
                        if zOne > zTwo:
                            # print('start segment')
                            segmentIntersections[0] = segment
                        else:
                            # print('end segment')
                            segmentIntersections[1] = segment
                # print(segmentIntersections)
                return segmentIntersections

            if type == 'nextPoint':
                for vId in triangle:
                    vertexZ = self.get_z(vId, idOnly=True)
                    if vertexZ == isoValue:
                        return [vId]

        def intersected_triangle_segments(self, triangle, isoValue, type):
            if type == 'full':
                triangleSegment = ['start', 'end']
                for i in range(3):
                    segment = [triangle[i], triangle[(i + 1) % 3]]
                    zOne = self.get_z(segment[0], idOnly=True)
                    zTwo = self.get_z(segment[1], idOnly=True)
                    if min(zOne, zTwo) < isoValue < max(zOne, zTwo):
                        if zOne > zTwo:
                            # deep is on the left
                            triangleSegment[0] = segment
                        else:
                            triangleSegment[1] = segment
                return triangleSegment

        def find_next_edge_triangle(self, currentTriangle, edge, lookupSet):

            for vId in edge:
                incidentTriangles = self.triangulation.incident_triangles_to_vertex(vId)
                for incidentTriangle in incidentTriangles:
                    if len(set(incidentTriangle).intersection(edge)) == 2:
                        if len(set(incidentTriangle).intersection(currentTriangle)) != 3:
                            incidentTriangle = tuple(self.pseudo_triangle(incidentTriangle))
                            if incidentTriangle not in lookupSet:
                                return tuple(self.pseudo_triangle(incidentTriangle))

            # no neighboring triangle found
            return False

        '''

    # ================
