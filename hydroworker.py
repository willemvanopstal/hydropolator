import os
from datetime import datetime
import shapefile
import startin

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

    projectName = None
    initDate = None
    modifiedDate = None

    def __init__(self):
        return

    def load_pointfile(self, pointFile, fileType, delimiter):
        pointFilePath = os.path.normpath(os.path.join(os.getcwd(), pointFile))
        print(pointFilePath)

        if fileType == 'csv':
            with open(pointFile) as fi:
                for line in fi.readlines()[:5000]:
                    point = line.split(delimiter)
                    point = [float(point[0]), float(point[1]), float(point[2])]

                    self.check_minmax(point)
                    # self.pointQueue.append(Point_2(point[0], point[1]))
                    self.pointQueue.append(point)
                    self.pointCount += 1

        elif fileType == 'shapefile':
            print('> ShapeFile not supported yet.')

        self.triangulation_insert()

        self.modifiedDate = self.now()
        self.write_metafile()

    def triangulation_insert(self):
        self.triangulation.insert(self.pointQueue)
        self.vertexCount = self.triangulation.number_of_vertices()
        self.pointQueue = []

        # for v in self.triangulation.finite_vertices():
        #     print(v.point()

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
        triFile = os.path.join(os.getcwd(), 'projects', self.projectName, 'triangulationObject')
        # self.triangulation.write_to_file(triFile)
        with open(metaFile, 'w') as mf:
            mf.write('projectName\t{}\n'.format(self.projectName))
            mf.write('initialisation\t{}\n'.format(self.initDate))
            mf.write('modified\t{}\n'.format(self.modifiedDate))
            mf.write('pointCount\t{}\n'.format(self.pointCount))
            mf.write('bounds\t{}\n'.format(self.bounds()))
            mf.write('vertices\t{}\n'.format(self.vertexCount))

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
                elif line.split('\t')[0] == 'bounds':
                    self.xMin, self.xMax, self.yMin, self.yMax, self.zMin, self.zMax = self.parse_bounds(line.split('\t')[
                        1])

    def init_project(self, projectName):
        cwd = os.getcwd()
        projectDir = os.path.join(cwd, 'projects', projectName)
        print('project directory: ', projectDir)

        if not os.path.exists(projectDir):
            os.mkdir(projectDir)
            self.projectName = projectName
            self.initDate = self.now()
            self.modifiedDate = self.now()
            self.write_metafile()
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
            return True
        else:
            print('> project does not exist, load another or initialise a new project with -init')

    def summarize_project(self):
        print('initialisation: {}'.format(self.initDate))
        print('modified: {}'.format(self.modifiedDate))
        print('pointCount: {}'.format(self.pointCount))
        print('bounds: {}'.format(self.bounds()))
        print('vertices: {}'.format(self.vertexCount))

    def poly_from_triangle(self, vertex_list):
        vertices = self.triangulation.all_vertices()
        triPoly = []
        for vId in vertex_list:
            triPoly.append([vertices[vId][0], vertices[vId][1]])
        triPoly.append([vertices[vertex_list[0]][0], vertices[vertex_list[0]][1]])
        return [triPoly]

    def polystats_from_triangle(self, vertex_list):
        vertices = self.triangulation.all_vertices()
        triPoly = []
        elevations = []
        for vId in vertex_list:
            triPoly.append([vertices[vId][0], vertices[vId][1]])
            elevations.append(vertices[vId][2])
        triPoly.append([vertices[vertex_list[0]][0], vertices[vertex_list[0]][1]])

        return [triPoly], min(elevations), max(elevations), sum(elevations)/3

    def minmaxavg_from_triangle(self, vertex_list):
        vertices = self.triangulation.all_vertices()
        elevations = []
        for vId in vertex_list:
            elevations.append(vertices[vId][2])
        return min(elevations), max(elevations), sum(elevations)/3

    def export_shapefile(self, shpName):
        pointShpName = 'points_{}_{}.shp'.format(shpName, self.now())
        triangleShpName = 'triangles_{}_{}.shp'.format(shpName, self.now())
        pointShpFile = os.path.join(os.getcwd(), 'projects', self.projectName, pointShpName)
        triangleShpFile = os.path.join(os.getcwd(), 'projects', self.projectName, triangleShpName)

        with shapefile.Writer(pointShpFile) as wp:
            wp.field('depth', 'F', decimal=4)
            for point in self.triangulation.all_vertices()[1:]:
                wp.point(point[0], point[1])
                wp.record(point[2])

        with shapefile.Writer(triangleShpFile) as wt:
            wt.field('min_depth', 'F', decimal=4)
            wt.field('max_depth', 'F', decimal=4)
            wt.field('avg_depth', 'F', decimal=4)
            for triangle in self.triangulation.all_triangles():
                geom, min, max, avg = self.polystats_from_triangle(triangle)
                # wt.poly(self.poly_from_triangle(triangle))
                # min, max, avg = 10, 10, 10  # self.minmaxavg_from_triangle(triangle)
                wt.poly(geom)
                wt.record(min, max, avg)
