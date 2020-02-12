import subprocess
import shapefile
import os


class BendDetector():

    def __init__(self, edge_id, edge_dict, project_name):

        self.edgeId = edge_id
        self.geom = edge_dict['geom']
        self.closed = edge_dict['closed']
        self.projectName = project_name

        # print('closed: ', self.closed)
        # print('geom: ', self.geom)

        self.nrVertices = len(self.geom)
        self.nrSegments = len(self.geom) - 2
        if self.closed:
            self.nrVertices -= 1
            self.nrSegments += 1

        self.projectPath = os.path.join(os.getcwd(), 'projects', project_name)

    def write_poly_file(self):
        # only takes into account one simple closed isobath
        polyName = '{}.poly'.format(self.edgeId)
        polyPath = os.path.join(self.projectPath, polyName)
        print(polyPath)

        if self.closed:
            vertexHeader = '{} 2 0 1\n'.format(self.nrVertices)
            segmentHeader = '{} 1\n'.format(self.nrSegments)
            holeHeader = '{}\n'.format(0)

            counter = 1
            vertexList = ''
            segmentList = ''

            self.vertices = dict()

            for v in self.geom[:-1]:
                vertexEntry = '{} {} {} 2\n'.format(counter, v[0], v[1])
                self.vertices[str(counter)] = (v[0], v[1])
                vertexList = vertexList + vertexEntry

                segmentEnd = (counter + 1) % (self.nrVertices + 1)
                if segmentEnd == 0:
                    segmentEnd = 1
                segmentEntry = '{} {} {} 2\n'.format(
                    counter, counter, segmentEnd)
                segmentList = segmentList + segmentEntry

                counter += 1

        with open(polyPath, 'w') as of:
            of.write(vertexHeader)
            of.write(vertexList)
            of.write(segmentHeader)
            of.write(segmentList)
            of.write(holeHeader)
        print(vertexHeader)
        print(vertexList)
        print(segmentHeader)
        print(segmentList)

    def export_triangles_shp(self):

        triangleShpFile = os.path.join(
            self.projectPath, 'constrained_triangles_{}.shp'.format(self.edgeId))

        with shapefile.Writer(triangleShpFile) as wt:
            wt.field('triid', 'C')
            for triangle in self.triangles.keys():
                geom = self.triangle_geom(triangle)
                wt.poly([geom])
                wt.record(triangle)

    def get_point(self, vertex_id):
        return self.vertices[vertex_id]  # tuple (x,y)

    def triangle_geom(self, triangleId):
        # vertices = self.triangulation.all_vertices()
        triPoly = []
        for vId in self.triangles[triangleId]['vertices']:
            vertex = self.get_point(vId)
            triPoly.append([vertex[0], vertex[1]])
            # elevations.append(vertex[2])
        triPoly.append(list(self.get_point(self.triangles[triangleId]['vertices'][0])))

        return triPoly

    def execute_constrained(self, pathToFile):
        print(pathToFile)
        subprocess.run('./triangle -pn "{}"'.format(pathToFile), shell=True)

    def parse_output(self, inputPath):
        outputFilePart = os.path.splitext(inputPath)[0]

        self.neighPath = outputFilePart + '.1.neigh'
        self.elePath = outputFilePart + '.1.ele'
        self.triangles = dict()

        with open(self.elePath) as elef:
            print('\nele file:')
            for line in elef.readlines()[1:]:
                if not line.startswith('#'):
                    tri = line.split()
                    # print(line.split())
                    self.triangles[tri[0]] = {'vertices': (
                        tri[1], tri[2], tri[3]), 'neighbors': []}

        with open(self.neighPath) as neighf:
            print('neighFile: ')
            for line in neighf.readlines()[1:]:
                if not line.startswith('#'):
                    neigh = line.split()
                    # print(neigh)
                    triangleNeighbors = self.triangles[neigh[0]]['neighbors']

                    for i in [1, 2, 3]:
                        if neigh[i] != '-1':
                            triangleNeighbors.append(neigh[i])

    def triangulate(self):
        # only takes into account one simple closed isobath
        polyName = '{}.poly'.format(self.edgeId)
        polyPath = os.path.join(self.projectPath, polyName)
        print(polyPath)

        self.execute_constrained(polyPath)

        self.parse_output(polyPath)
        # print(self.vertices)
        # print(self.triangles)
        pass
