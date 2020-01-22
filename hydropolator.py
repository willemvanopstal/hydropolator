import os
from datetime import datetime
import shapefile
import bisect
import startin
import pickle

from TriangleRegionGraph import TriangleRegionGraph
from ElevationDict import ElevationDict

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
    graph = {}
    nrNodes = 0
    nrEdges = 0

    # isobaths
    isoType = None
    standardSeries = [0, 1, 2, 5, 8, 10, 15, 20, 25, 30, 35, 40, 45, 50, 100, 200]
    meterSeries = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14,
                   15, 16, 17, 18, 19, 20, 25, 30, 35, 40, 45, 50, 100, 200]
    hdSeries = range(0, 100)
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
                for line in fi.readlines()[:500]:
                    point = line.split(delimiter)
                    if flip:
                        point = [float(point[0]), float(point[1]), round(-1*float(point[2])+18, 4)]
                    elif not flip:
                        point = [float(point[0]), float(point[1]), round(float(point[2])+18, 4)]

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

    def write_metafile(self):
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

    def load_metafile(self):
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
                elif line.split('\t')[0] == 'vertices':
                    self.vertexCount = int(line.split('\t')[1].strip())
                elif line.split('\t')[0] == 'isoType':
                    self.isoType = line.split('\t')[1].strip()
                elif line.split('\t')[0] == 'bounds':
                    self.xMin, self.xMax, self.yMin, self.yMax, self.zMin, self.zMax = self.parse_bounds(line.split('\t')[
                        1])

    def save_triangulation(self):
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

        print('> triangulation saved')

    def load_triangulation(self):
        print('> loading triangulation')
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
                print('insertion: ', insertion)
                for line in tf.readlines()[insertionTracker:insertion]:
                    point = [float(value) for value in line.split(';')]
                    print(point)
                    self.pointQueue.append(point)
                self.triangulation_insert()
                insertionTracker = insertion

        with open(elevationFile, 'rb') as ef:
            self.vertexDict = pickle.load(ef)

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
            self.load_triangulation()
            return True
        else:
            print('> project does not exist, load another or initialise a new project with -init')

    def summarize_project(self):
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

    def adjacent_triangles(self, triangle):
        adjacentTriangles = []
        addedVertices = []
        for vId in triangle:
            if len(addedVertices) == 3:
                break
            else:
                for incidentTriangle in self.triangulation.incident_triangles_to_vertex(vId):
                    if len(set(triangle).intersection(incidentTriangle)) == 2 and set(incidentTriangle).difference(triangle) not in addedVertices:
                        adjacentTriangles.append(incidentTriangle)
                        addedVertices.append(set(incidentTriangle).difference(triangle))

        return adjacentTriangles

    def generate_regions(self):
        # self.isoType = isobathSeries
        if self.isoType == 'standard':
            isobathValues = self.standardSeries
        elif self.isoType == 'meter':
            isobathValues = self.meterSeries
        elif self.isoType == 'hd':
            isobathValues = self.hdSeries

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

    def index_region_triangles(self):
        for triangle in self.triangles:
            min, max = self.minmax_from_triangle(triangle)
            # print(min, max)
            for index in range(bisect.bisect_left(self.isobathValues, min), bisect.bisect_left(self.isobathValues, max) + 1):
                # print(self.regions[index])
                self.triangleRegions[index].append(triangle)
        # print(self.triangleRegions)

    def find_intervals(self, triangle):
        min, max = self.minmax_from_triangle(triangle)
        # print(min, max)
        intervals = []
        for index in range(bisect.bisect_left(self.isobathValues, min), bisect.bisect_left(self.isobathValues, max) + 1):
            # print(self.regions[index])
            intervals.append(self.regions[index])
            # self.triangleRegions[index].append(triangle)
        return intervals

    def export_region_triangles(self):
        triangleShpName = 'region_triangles_{}.shp'.format(self.now())
        triangleShpFile = os.path.join(os.getcwd(), 'projects', self.projectName, triangleShpName)

        with shapefile.Writer(triangleShpFile) as wt:
            wt.field('region', 'N')
            for i, region in enumerate(self.triangleRegions):
                if len(region):
                    geom = []
                    for triangle in region:
                        geom.append(self.poly_from_triangle(triangle))
                    wt.poly(geom)
                    wt.record(i)

    # def create_tr_graph(self):
    #     self.trGraph.initialize_graph(self.triangulation)
    #     self.trGraph.vertexDict = self.vertexDict
    #     self.trGraph.build_graph()

    def build_graph(self):
        startingTriangle = self.triangles[25]

        print('=======starter=======')
        print(self.minmax_from_triangle(startingTriangle))
        print(self.find_intervals(startingTriangle))
        print('----neighbors----')
        for neighbor in self.adjacent_triangles(startingTriangle):
            print(neighbor, self.find_intervals(neighbor))

        pass

    def export_shapefile(self, shpName):
        pointShpName = 'points_{}_{}.shp'.format(shpName, self.now())
        triangleShpName = 'triangles_{}_{}.shp'.format(shpName, self.now())
        pointShpFile = os.path.join(os.getcwd(), 'projects', self.projectName, pointShpName)
        triangleShpFile = os.path.join(os.getcwd(), 'projects', self.projectName, triangleShpName)

        with shapefile.Writer(pointShpFile) as wp:
            wp.field('depth', 'F', decimal=4)
            # for point in self.triangulation.all_vertices()[1:]:
            for point in self.vertices[1:]:  # remove the infinite vertex in startTIN
                wp.point(point[0], point[1])
                wp.record(point[2])

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
