from ElevationDict import ElevationDict
import os
from datetime import datetime
import shapefile
import bisect
import startin
import pickle
import colorama
colorama.init()

# from TriangleRegionGraph import TriangleRegionGraph

# from CGAL.CGAL_Kernel import Point_2, Point_3
# from CGAL.CGAL_Triangulation_2 import Triangulation_2, Delaunay_triangulation_2
# from CGAL.CGAL_Triangulation_2 import Triangulation_2_Vertex_circulator
# from CGAL.CGAL_Triangulation_2 import Triangulation_2_Vertex_handle


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
    nrNodes = 0
    nrEdges = 0
    unfinishedDeep = set()
    unfinishedShallow = set()
    nodeQueue = set()

    # isobaths
    isoType = 'standard'
    standardSeries = [0, 1, 2, 5, 8, 10, 15, 20, 25, 30, 35, 40, 45, 50, 100, 200]
    meterSeries = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14,
                   15, 16, 17, 18, 19, 20, 25, 30, 35, 40, 45, 50, 100, 200]
    hdSeries = range(0, 100)
    testingSeries = [0, 2, 4, 6, 8, 10, 12, 15, 20, 25, 30, 35, 40, 45, 50]
    isobathValues = []
    regions = []
    triangleRegions = []

    projectName = None
    initDate = None
    modifiedDate = None

    def __init__(self):
        return

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
            # self.vertexDict[tuple(vertex)] = {'z': vertex[2]}
            self.vertexDict.add_new(vertex)

        self.pointQueue = []
        print('new insertionslist: ', self.insertions)

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

    def bounds(self):
        return [self.xMin, self.xMax, self.yMin, self.yMax, self.zMin, self.zMax]

    def parse_bounds(self, boundsString):
        boundsList = boundsString.strip().strip('[').strip(']').split(',')
        boundsListFloat = [float(value) for value in boundsList]
        return boundsListFloat

    def now(self):
        return datetime.now().strftime("%Y%m%d%H%M%S")

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

    def write_metafile(self):
        self.msg('> writing metafile...', 'info')
        metaFile = os.path.join(os.getcwd(), 'projects', self.projectName, 'metafile')
        # self.triangulation.write_to_file(triFile)
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
        triFile = os.path.join(os.getcwd(), 'projects', self.projectName, 'triangulationObject')
        # self.triangulation.read_from_file(triFile)
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
                elif line.split('\t')[0] == 'nrNodes':
                    self.nrNodes = int(line.split('\t')[1])
                elif line.split('\t')[0] == 'nrEdges':
                    self.nrEdges = int(line.split('\t')[1])
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
                # print(vertex)
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
                # print('insertion: ', insertion)
                for line in tf.readlines()[insertionTracker:insertion]:
                    point = [float(value) for value in line.split(';')]
                    # print(point)
                    self.pointQueue.append(point)
                self.triangulation_insert()
                insertionTracker = insertion

        with open(elevationFile, 'rb') as ef:
            self.vertexDict = pickle.load(ef)
        self.msg('> triangulation loaded', 'info')

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
            self.load_trGraph()
            return True
        else:
            print('> project does not exist, load another or initialise a new project with -init')

    def summarize_project(self):
        self.msg('> project summary', 'header')
        print('initialisation: {}'.format(self.initDate))
        print('modified: {}'.format(self.modifiedDate))
        print('pointCount: {}'.format(self.pointCount))
        print('bounds: {}'.format(self.bounds()))
        print('vertices: {}'.format(self.vertexCount))
        print('isoType: {}'.format(self.isoType))

    def get_z(self, vertex):
        # return self.vertexDict[tuple(vertex)]['z']
        return self.vertexDict.get_z(vertex)

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

    def adjacent_triangle_in_set(self, triangle, lookupSet):
        adjacentTriangles = []
        addedVertices = []
        for vId in triangle:
            if len(addedVertices) == 3:
                break
            else:
                for incidentTriangle in self.triangulation.incident_triangles_to_vertex(vId):
                    if len(set(triangle).intersection(incidentTriangle)) == 2 and set(incidentTriangle).difference(triangle) not in addedVertices:
                        if self.pseudo_triangle(incidentTriangle) in lookupSet:
                            adjacentTriangles.append(self.pseudo_triangle(incidentTriangle))
                            addedVertices.append(set(incidentTriangle).difference(triangle))

        return adjacentTriangles

    def locate_point_in_set(self, point, lookupSet):

        pass

    def adjacent_triangles(self, triangle):
        adjacentTriangles = []
        addedVertices = []
        for vId in triangle:
            if len(addedVertices) == 3:
                break
            else:
                for incidentTriangle in self.triangulation.incident_triangles_to_vertex(vId):
                    if len(set(triangle).intersection(incidentTriangle)) == 2 and set(incidentTriangle).difference(triangle) not in addedVertices:
                        adjacentTriangles.append(self.pseudo_triangle(incidentTriangle))
                        addedVertices.append(set(incidentTriangle).difference(triangle))

        return adjacentTriangles

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
        # self.trGraph.triangleRegions = self.triangleRegions

        # print(self.triangleRegions, regions, isobathValues)
        self.msg('> regions-list established', 'info')

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

    def export_all_edge_triangles(self):
        self.msg('> saving all edge triangles...', 'info')
        triangleShpName = 'edge_triangles_{}.shp'.format(self.now())
        triangleShpFile = os.path.join(os.getcwd(), 'projects', self.projectName, triangleShpName)
        print('edge triangles file: ', triangleShpFile)

        with shapefile.Writer(triangleShpFile) as wt:
            wt.field('value', 'N')
            for edgeId in self.graph['edges'].keys():
                geom = []
                for triangle in self.get_edge_triangles(edgeId):
                    geom.append(self.poly_from_triangle(triangle))
                wt.poly(geom)
                isoValue = self.get_edge_value(edgeId)
                wt.record(isoValue)

        self.msg('> edge triangles saved', 'info')

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
            for node in nodeIds:
                geom = []
                for triangle in self.graph['nodes'][node]['triangles']:
                    geom.append(self.poly_from_triangle(list(triangle)))

                region = self.get_interval_from_node(node)
                interval = str(self.regions[region])
                shallowNeighbors = str(self.get_neighboring_nodes(node, 'shallow'))
                deepNeighbors = str(self.get_neighboring_nodes(node, 'deep'))

                wt.poly(geom)
                wt.record(int(node), region, interval, shallowNeighbors, deepNeighbors)

        self.msg('> selected node triangles saved', 'info')

    # def create_tr_graph(self):
    #     self.trGraph.initialize_graph(self.triangulation)
    #     self.trGraph.vertexDict = self.vertexDict
    #     self.trGraph.build_graph()

    def pseudo_triangle(self, triangle):
        # rotates the triangle_list so the smallest index is in front
        # so we can easily compare and not store duplicates
        n = triangle.index(min(triangle))
        if not n:
            return triangle
        else:
            return triangle[n:] + triangle[:n]
        # print(self.triangulation.is_triangle(pseudoTriangle))
        # return pseudoTriangle

    def add_triangle_to_node(self, triangle, nodeId):
        self.graph['nodes'][nodeId]['triangles'].add(tuple(self.pseudo_triangle(triangle)))

    def add_triangle_to_new_node(self, interval, triangle):
        # self.graph['nodes'][str(self.nrNodes)] = {'region': tuple(interval), 'triangles': {
        #     tuple(self.pseudo_triangle(triangle))}, 'edges': set()}
        nodeId = str(self.nrNodes)
        self.graph['nodes'][nodeId] = {'region': interval, 'triangles': {tuple(self.pseudo_triangle(
            triangle))}, 'deepNeighbors': set(), 'shallowNeighbors': set(), 'currentQueue': set(), 'shallowQueue': set(), 'deepQueue': set()}
        self.nrNodes += 1
        # print('new node: ', nodeId)
        return nodeId

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

    def triangle_in_queue(self, triangle, nodeId, type):
        queueType = type + 'Queue'
        if tuple(self.pseudo_triangle(triangle)) in self.graph['nodes'][nodeId][queueType]:
            return True
        else:
            return False

    def add_new_edge(self, shallowNode, deepNode):
        edgeId = str(self.nrEdges)
        self.graph['edges'][edgeId] = {}
        self.graph['edges'][edgeId]['edge'] = [shallowNode, deepNode]
        self.graph['nodes'][str(shallowNode)]['deepNeighbors'].add(deepNode)
        self.graph['nodes'][str(deepNode)]['shallowNeighbors'].add(shallowNode)
        self.graph['edges'][edgeId]['value'] = self.get_edge_value(edgeId)
        self.nrEdges += 1
        # print('new edge: ', edgeId)

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
        nodeList = self.graph['edges'][edgeId]['edge']
        trianglesOne = self.get_triangles(nodeList[0])
        trianglesTwo = self.get_triangles(nodeList[1])
        return trianglesOne.intersection(trianglesTwo)

    def print_graph(self):
        self.msg('\n======GRAPH======', 'header')
        self.msg('NODES', 'header')
        # print('\n======GRAPH======\nNODES')
        for nodeId in self.graph['nodes'].keys():
            # print(nodeId, self.graph['nodes'][nodeId])
            print('id: ', nodeId, 'interval: ', self.graph['nodes'][nodeId]['region'], 'triangles: ', len(self.graph['nodes'][nodeId]['triangles']), 'deepNeighbors: ', self.graph['nodes'][nodeId]['deepNeighbors'], 'shallowNeighbors: ', self.graph['nodes'][nodeId]['shallowNeighbors'], '\ncurrent: ',
                  len(self.graph['nodes'][nodeId]['currentQueue']), 'deep: ', len(
                      self.graph['nodes'][nodeId]['deepQueue']), 'shallow: ', len(self.graph['nodes'][nodeId]['shallowQueue']))
        self.msg('\nEDGES', 'header')
        for edgeId in self.graph['edges'].keys():
            print(edgeId, self.graph['edges'][edgeId])

    # def generate_walker_graph(self, triangle, interval, nodeId):
    #     # NOT IN USE ANYMORE: Max recursion limit
    #     for neighbor in self.adjacent_triangles(triangle):
    #         if interval in self.find_intervals(neighbor) and not self.triangle_in_node(neighbor, nodeId):
    #             # print(neighbor)
    #             self.add_triangle_to_node(neighbor, nodeId)
    #             self.generate_walker_graph(neighbor, interval, nodeId)

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
                    if tuple(neighbor) not in visitedTriangles:
                        visitedTriangles.add(tuple(neighbor))
                        # print(neighbor)

                        # same interval
                        if nodeInterval in self.find_intervals(neighbor) and not self.triangle_in_node(neighbor, nodeId):
                            self.add_triangle_to_node(neighbor, nodeId)
                            addedTriangles += 1

                        # deeper interval
                        deepTracker = False
                        if nodeInterval + 1 in self.find_intervals(neighbor):
                            for deeperNode in self.get_neighboring_nodes(nodeId, 'deep'):
                                if self.triangle_in_queue(neighbor, deeperNode, 'shallow'):
                                    self.remove_triangle_from_queue(neighbor, deeperNode, 'shallow')
                                    deepTracker = True
                            if not deepTracker:
                                self.add_triangle_to_queue(neighbor, nodeId, 'deep')
                                addedTriangles += 1

                        # shallower interval
                        shallowTracker = False
                        if nodeInterval - 1 in self.find_intervals(neighbor):
                            for shallowerNode in self.get_neighboring_nodes(nodeId, 'shallow'):
                                if self.triangle_in_queue(neighbor, shallowerNode, 'deep'):
                                    self.remove_triangle_from_queue(neighbor, shallowerNode, 'deep')
                                    shallowTracker = True
                            if not shallowTracker:
                                self.add_triangle_to_queue(neighbor, nodeId, 'shallow')
                                addedTriangles += 1

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
                print('==============\nresolving node: ', node)
                print('nodeQueue: ', self.nodeQueue)
                self.resolve_queues(node)
                # i += 1
                # if i == 30:
                #     finished = True
            if not len(self.nodeQueue):
                finished = True

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

        # self.export_node_triangles(['0'])

    def generate_isobaths(self):
        edgeIds = self.graph['edges'].keys()
        for edge in edgeIds:
            edgeTriangles = self.get_edge_triangles(edge)

            for startingTriangle in edgeTriangles:
                break
            print(startingTriangle)

            # print(edgeTriangles)

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
            # for point in self.triangulation.all_vertices()[1:]:
            for point in self.vertices[1:]:  # remove the infinite vertex in startTIN
                wp.point(point[0], point[1])
                wp.record(point[2])
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
