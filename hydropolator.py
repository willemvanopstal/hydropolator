# @Author: Willem van Opstal <willemvanopstal>
# @Date:   17-Jan-2020
# @Email:  willemvanopstal home nl
# @Project: Hydropolator
# @Last modified by:   Bonny
# @Last modified time: 04-Mar-2020


from ElevationDict import ElevationDict
from BendDetector import BendDetector

import startin

from decimal import *
import math
import networkx as nx
from matplotlib import cm, colors
import matplotlib.pyplot as plt
import numpy as np
# from PointInTriangle import point_in_triangle
import os
from datetime import datetime
import shapefile
import bisect
import pickle
# from shapely import geometry, ops
import colorama
colorama.init()

# from TriangleRegionGraph import TriangleRegionGraph


class Hydropolator:
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
                  'iso_seg_lengths': []}

    projectName = None
    initDate = None
    modifiedDate = None

    errors = []

    def __init__(self):
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

        print(colColor + string + colorama.Style.RESET_ALL)

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
        nx.draw(G, pos, node_color=colorLabels, edgecolors=edgeColors,
                font_size=16, with_labels=False)
        # for p in pos:  # raise text positions
        #     pos[p][1] += 0.07
        nx.draw_networkx_labels(G, pos, nodelabels, font_size=6)
        # plt.show()

        regionGraphName = 'regiongraph_{}.pdf'.format(self.now())
        regionGraphFile = os.path.join(os.getcwd(), 'projects', self.projectName, regionGraphName)
        plt.savefig(regionGraphFile)

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
            # for point in self.triangulation.all_vertices()[1:]:
            for i, point in enumerate(self.vertices[1:]):  # remove the infinite vertex in startTIN
                actualZ = self.get_z(point, idOnly=False)
                wp.point(point[0], point[1])
                wp.record(point[2], i, point[2]-actualZ)
            self.msg('> points written to shapefile', 'info')

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
            for node in nodeIds:
                geom = []
                for triangle in self.graph['nodes'][node]['triangles']:
                    geom.append(self.poly_from_triangle(list(triangle)))

                region = self.get_interval_from_node(node)
                interval = str(self.regions[region])
                shallowNeighbors = str(self.get_neighboring_nodes(node, 'shallow'))
                deepNeighbors = str(self.get_neighboring_nodes(node, 'deep'))
                nodeArea = self.graph['nodes'][node]['full_area']

                wt.poly(geom)
                wt.record(int(node), region, interval, shallowNeighbors, deepNeighbors, nodeArea)

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

        self.msg('> edge triangles saved', 'info')

    def export_all_isobaths(self):
        self.msg('> saving all isobaths...', 'info')
        lineShpName = 'isobaths_{}.shp'.format(self.now())
        lineShpFile = os.path.join(os.getcwd(), 'projects', self.projectName, lineShpName)
        print('isobaths file: ', lineShpFile)

        with shapefile.Writer(lineShpFile) as wt:
            wt.field('value', 'F', decimal=4)
            wt.field('id', 'N')
            wt.field('iso_area', 'F', decimal=3)
            for edgeId in self.graph['edges'].keys():
                # geom = [[list(value) for value in self.graph['edges'][edgeId]['geom']]]
                geom = self.graph['edges'][edgeId]['geom']
                isoArea = self.graph['edges'][edgeId]['iso_area']
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
                wt.record(isoValue, int(edgeId), isoArea)

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

        self.msg('> depth areas saved', 'info')

    # ====================================== #
    #
    #   Point Functions
    #
    # ====================================== #

    def ___POINTS___(self):
        # placeholder for Atom symbol-tree-view
        pass

    def load_pointfile(self, pointFile, fileType, delimiter, flip=False):
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

    def build_graph2(self):
        self.msg('> building triangle region graph...', 'info')
        self.msg('> splitting all triangles in regions...', 'info')
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
                break

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
        print(len(triangles))

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
                        # self.get_triangles(existingNode).intersection(triangle):
                        if triangle in self.get_triangles(existingNode):
                            self.add_triangle_to_node(triangle, existingNode)
                            # tempNodes[currentNode]['previous_nodes'].update(
                            #     oldTriangleInventory[triangle])
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
                        print('no queue left: ', len(indexedTriangles), triangleAmount)
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

        print('tempNodes: ', tempNodes)
        affectedNodes = tempNodes.copy()
        # self.add_triangle_to_new_node(interval, triangle)

        # print('tempDebug: ', len(tempDebugging))
        print('inserted triangles: ', insertedTriangles, len(
            insertedTrianglesSet), len(indexedTriangles))
        print('remove/insert diff: ', set(triangles).difference(insertedTrianglesSet))

        print('======\ntempNodes')
        # merge nodes with existing nodes if possible
        for tempNode in tempNodes:
            tempNodeInterval = self.get_interval_from_node(tempNode)
            previousNodes = oldEdges
            tempNodeTriangles = self.get_triangles(tempNode)
            print('------', tempNode, tempNodeInterval)
            print(previousNodes)
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
                print('need searching.. BUT should be in the previousedges??')
                # TODO first try to search the shallow/deeper nodes of the previous nodes, probably it is adjacent to that
                for oldEdgingNode in oldEdges:
                    if self.is_node(oldEdgingNode):
                        # for sameIntervalNode in self.regionNodes[str(tempNodeInterval)]:
                        # if tempNodeInterval == self.get_interval_from_node(oldEdgingNode)
                        if oldEdgingNode not in tempNodes and tempNodeInterval == self.get_interval_from_node(oldEdgingNode):
                            print(oldEdgingNode)
                            for tempNodeTriangle in tempNodeTriangles:
                                for adjacentTriangle in self.adjacent_triangles(tempNodeTriangle):
                                    if not self.saddle_test(tempNodeTriangle, adjacentTriangle, tempNodeInterval):
                                        # sameIntervalNode in oldTriangleInventory[adjacentTriangle]:
                                        if adjacentTriangle in self.get_triangles(oldEdgingNode):
                                            match = True
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
                print('im a completely new/rebuilt node')

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
        print('mergin nodes:', keepNode, mergeNode)

        trianglesToAdd = self.get_triangles(mergeNode)
        deepsToAdd = self.get_queue(mergeNode, 'deep')
        shallowsToAdd = self.get_queue(mergeNode, 'shallow')

        for triangle in trianglesToAdd:
            self.add_triangle_to_node(triangle, keepNode)
        for triangle in deepsToAdd:
            self.add_triangle_to_queue(triangle, keepNode, 'deep')
        for triangle in shallowsToAdd:
            self.add_triangle_to_queue(triangle, keepNode, 'shallow')

        self.delete_node(mergeNode)

    def check_deleted_nodes(self, listOfPossibleNodes):
        deletedNodes = set()
        for nodeId in listOfPossibleNodes:
            if len(self.get_triangles(nodeId)) == 0:
                deletedNodes.add(nodeId)
        return deletedNodes

    def delete_edge(self, edgeCombination):
        self.msg('deleting edge from graph: {}'.format(edgeCombination), 'warning')

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
                print('removed edge')
                break

    def remove_node_and_all_contents(self, nodeId):
        self.msg('deleting node from graph: {}'.format(nodeId), 'warning')
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
            self.triangleInventory.pop(triangle, None)

        # remove from regionNodes dict
        self.regionNodes[str(nodeInterval)].remove(nodeId)

        # remove node itself
        del self.graph['nodes'][nodeId]
        self.availableNodeIds.add(nodeId)

    def delete_node(self, nodeId):
        # from graph, from edges, pointers of neighbors
        self.msg('deleting node from graph: {}'.format(nodeId), 'warning')
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

        for updatedVertex in updatedVertices:
            self.vertexDict.remove_previous_z(self.triangulation.get_point(updatedVertex))

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
        print(affectedNodes)
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
        self.graph['nodes'][nodeId]['triangles'].remove(triangle)

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

        self.graph['nodes'][nodeId][queueType].remove(tuple(self.pseudo_triangle(triangle)))

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
        if len(edgeIds) == 0:
            edgeIds = list(self.graph['edges'].keys())

        for edge in edgeIds:
            # self.msg('--new edge', 'header')
            edgeObject = self.graph['edges'][edge]
            isoValue = edgeObject['value']
            # print('isoValue: ', isoValue, edgeObject['edge'], edge)
            # print('isoValue: ', isoValue, edge)

            edgeTriangles = self.get_edge_triangles(edge)

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
                print('not closed isobath, checking convex hull')

                print(startSegment, endSegment)

                if type(startSegment) == int:
                    print(self.triangulation.is_vertex_convex_hull(startSegment))
                else:
                    print('first ', self.triangulation.is_vertex_convex_hull(startSegment[0]))
                    print('second ', self.triangulation.is_vertex_convex_hull(startSegment[1]))
                if type(endSegment) == int:
                    print(self.triangulation.is_vertex_convex_hull(endSegment))
                else:
                    print('first ', self.triangulation.is_vertex_convex_hull(endSegment[0]))
                    print('second ', self.triangulation.is_vertex_convex_hull(endSegment[1]))

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
            # interval = self.get_interval_from_node(nodeId)
            # region = self.regions[interval]
            nodeEdgeIds = node['edges']
            # print('----new node ', nodeId, nodeEdgeIds)

            for edgeId in nodeEdgeIds:
                edge = self.graph['edges'][edgeId]

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

        print('smoothing ...')

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

        print('{} vertices added to update queue'.format(updates))

        return updatedVertices

        self.vertexDict.update_values_from_queue()
        self.update_region_graph(updatedVertices)

        # print(adjacentVertex, leftPseudoTriangle, rightPseudoTriangle)

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
            print('ring: ', ring)

            for triangle in allTriangles.copy():
                # print(triangle)
                ringTriangles = self.get_ring_around_triangle(triangle)
                # print(ringTriangles)

                allTriangles.update(ringTriangles)

            ring += 1

        print(len(allTriangles))
        return allTriangles

    def simple_smooth_and_rebuild(self, vertexSet):

        self.print_graph()

        allChangedVertices = set()
        for i in range(15):
            changedVertices = self.smooth_vertices(vertexSet)
            allChangedVertices.update(changedVertices)
            # print(allChangedVertices)
            self.vertexDict.update_previous_z_from_queue()  # stored the old zvalue in previous_z
            self.vertexDict.update_values_from_queue()  # updates the working z-value in z
            # queue is now empty again
        # may again smooth the vertices?

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
        self.print_graph()

    def smooth_vertices_helper2(self, vertexSet):
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

        # Updatin the region graph if necessary:
        changedTriangles, changedNodes = self.get_changed_triangles(
            allChangedVertices, oldTriangleInventory)
        print(changedNodes)

        # we need to update the entire node, so lets get all triangles in each node
        trianglesToBeDeleted = set()
        edgesToBeDeleted = set()
        for changedNode in changedNodes:
            print(changedNode, self.get_interval_from_node(changedNode))
            # print(changedNode, len(self.get_triangles(changedNode)))
            trianglesToBeDeleted.update(self.get_triangles(changedNode))
            shallowNeighbors = self.get_neighboring_nodes(changedNode, 'shallow')
            for shallowNeighbor in shallowNeighbors:
                edgesToBeDeleted.add((shallowNeighbor, changedNode))
            deepNeighbors = self.get_neighboring_nodes(changedNode, 'deep')
            for deepNeighbor in deepNeighbors:
                edgesToBeDeleted.add((changedNode, deepNeighbor))
        print(len(trianglesToBeDeleted), edgesToBeDeleted)

        # for tri in trianglesToBeDeleted:
        #     print(oldTriangleInventory[tri])

        # removes actual nodes and all its triangles inside
        for changedNode in changedNodes:
            self.remove_node_and_all_contents(changedNode)

        # removes actual edges
        possibleNeighboringEdges = set()
        for edgeCombination in edgesToBeDeleted:
            possibleNeighboringEdges.update({edgeCombination[0], edgeCombination[1]})
            self.delete_edge(edgeCombination)

        # remove previous_z because region graph is built again
        for changedVertex in allChangedVertices:
            self.vertexDict.remove_previous_z(self.triangulation.get_point(
                changedVertex))

        # self.build_graph2()

        # insert all deleted triangles back in the graph
        affectedNodes = self.insert_triangles_into_region_graph2(
            trianglesToBeDeleted, possibleNeighboringEdges)
        # newly inserted nodes are not connected yet
        print(affectedNodes)

        self.print_graph()
        # establish edges again
        self.establish_edges_on_affected_nodes(affectedNodes)

        self.print_graph()
        # self.make_network_graph()

    def smooth_vertices_helper(self, vertexSet):
        # contains pointers per triangle to which nodes it belonged to previously
        oldTriangleInventory = self.triangleInventory.copy()
        changedVertices = self.smooth_vertices(vertexSet)  # set
        # changed vertices are now in the vertexDict queue with a new z-value
        self.vertexDict.update_previous_z_from_queue()  # saves the previous known z-values
        self.vertexDict.update_values_from_queue()  # edits the interpolated z-value
        # queue is now empty
        # gets all the affected triangles, only if their interval is also changed
        changedTriangles = self.get_changed_triangles(changedVertices)

        for changedVertex in changedVertices:
            self.vertexDict.remove_previous_z(self.triangulation.get_point(
                changedVertex))  # cautieso, used in smooth_vertices()

        # self.update_region_graph(changedVertices)

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
        return (ux, uy)

    # ====================================== #
    #
    #   Metrics
    #
    # ====================================== #

    def ___METRICS___(self):
        # placeholder for Atom symbol-tree-view
        pass

    def angularity(self, ptHead, ptMid, ptTail):
        dx1, dy1 = ptMid[0] - ptHead[0], ptMid[1] - ptHead[1]
        dx2, dy2 = ptTail[0] - ptMid[0], ptTail[1] - ptMid[1]
        inner_product = dx1*dx2 + dy1*dy2
        len1 = math.hypot(dx1, dy1)
        len2 = math.hypot(dx2, dy2)
        return round(math.acos(inner_product/(len1*len2)), 4)

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

    def compute_node_area(self, nodeIds=[]):
        if not len(nodeIds):
            nodeIds = self.graph['nodes'].keys()

        for nodeId in nodeIds:
            print(nodeId, 'node_area ')
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

    def check_spurs_gullys(self, edgeIds=[], threshold=None, spurThreshold=None, gullyThreshold=None):

        if not len(edgeIds):
            # get all edges
            edgeIds = self.graph['edges'].keys()

        spurgullyPoints = set()

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

            spurs, gullys = edge['bend_detector'].get_spurs_and_gullys(
                gully_threshold=gullyThreshold, spur_threshold=spurThreshold)

            exportDict = {'spurs': spurs, 'gullys': gullys}
            edge['bend_detector'].export_triangles_shp(multi=exportDict)

            allInvalidTriangles = spurs.union(gullys)
            invalidIsoVertices = edge['bend_detector'].get_vertices_from_triangles(
                allInvalidTriangles)
            spurgullyPoints.update(invalidIsoVertices)

        return spurgullyPoints

        # exportDict = {'spurs': spurs, 'gullys': gullys}
        # edge['bend_detector'].export_triangles_shp(multi=exportDict)
        # edgeBends = BendDetector(edgeId, edge, self.projectName)

        pass

    def set_sharp_points_bins(self, breakpoints):
        # print(breakpoints)

        sharpPointRegions = []
        sharpPointRegions.append([0, breakpoints[0]])
        for i in range(len(breakpoints))[1:]:
            sharpPointRegions.append([breakpoints[i - 1], breakpoints[i]])
        sharpPointRegions.append([breakpoints[-1], 10])

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

        print(isoSegBins)

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
                # print(angularity)

                for bin, sharpBin in enumerate(self.sharpPointBins):
                    if angularity > sharpBin[0] and angularity <= sharpBin[1]:
                        sharp_points[str(sharpBin)[1:-1]] += 1
                        # print(str(sharpBin))
                        break

                # sharpPointAngles.add(angularity)

            for i in range(1, len(geom)-1):
                angularity = self.angularity(geom[i-1], geom[i], geom[i+1])
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

    def generate_statistics(self):

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

    def export_statistics(self):

        stats = self.statistics
        separator = ';'

        depare_header = 'SEP={}\ndepares'.format(separator)
        sharp_header = 'SEP={}\nsharps'.format(separator)
        abs_change_header = 'SEP={}\nabs_change'.format(separator)
        min_change_header = 'SEP={}\nmin_change'.format(separator)
        isoseg_header = 'SEP={}\nisoseg'.format(separator)

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
                    depare_rows[rowIndex] = row + \
                        '{}{}'.format(separator, value)

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
