import subprocess
import shapefile
import os
import math
from datetime import datetime


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

    # ====================================== #
    #
    #   Exports
    #
    # ====================================== #

    def now(self):
        return datetime.now().strftime("%Y%m%d_%H%M%S")

    def export_triangles_shp(self, triangle_ids=[]):
        if len(triangle_ids) == 0:
            triangle_ids = self.triangles.keys()

        triangleShpFile = os.path.join(
            self.projectPath, 'constrained_triangles_{}_{}.shp'.format(self.edgeId, self.now()))

        with shapefile.Writer(triangleShpFile) as wt:
            wt.field('triid', 'C')
            wt.field('vertices', 'C')
            wt.field('neighbors', 'C')
            for triangle in triangle_ids:
                geom = self.triangle_geom(triangle)
                vertices = str(self.triangles[triangle]['vertices'])
                neighbors = str(self.triangles[triangle]['neighbors'])
                wt.poly([geom])
                wt.record(triangle, vertices, neighbors)

    # ====================================== #
    #
    #   Triangulation
    #
    # ====================================== #

    def get_point(self, vertex_id):
        return self.vertices[vertex_id]  # tuple (x,y)

    def triangle_geom(self, triangle_id):
        # vertices = self.triangulation.all_vertices()
        triPoly = []
        for vId in self.triangles[triangle_id]['vertices']:
            vertex = self.get_point(vId)
            triPoly.append([vertex[0], vertex[1]])
            # elevations.append(vertex[2])
        triPoly.append(list(self.get_point(self.triangles[triangle_id]['vertices'][0])))

        return triPoly

    def adjacent_triangles(self, triangle_id):
        neighboringTriangles = self.triangles[triangle_id]['neighbors']
        finalNeighbors = []
        for tri in neighboringTriangles:
            if tri != '-1':
                finalNeighbors.append(tri)

        return finalNeighbors

    def has_three_neighbors(self, triangle_id):
        neighboringTriangles = self.triangles[triangle_id]['neighbors']
        for tri in neighboringTriangles:
            if tri == '-1':
                return False

        return True

    def number_neighbors(self, triangle_id):
        neighboringTriangles = self.triangles[triangle_id]['neighbors']
        validCounter = 0
        for tri in neighboringTriangles:
            if tri != '-1':
                validCounter += 1

        return validCounter

    def shared_edge(self, triangle_one_id, triangle_two_id):
        verticesOne = self.triangles[triangle_one_id]['vertices']
        verticesTwo = self.triangles[triangle_two_id]['vertices']
        # tuples

        sharedVertices = set(verticesOne).intersection(verticesTwo)

        return list(sharedVertices)

    def edge_length(self, edge_vertices):
        vertexOne = self.vertices[edge_vertices[0]]
        vertexTwo = self.vertices[edge_vertices[1]]

        dX = vertexTwo[0] - vertexOne[0]
        dY = vertexTwo[1] - vertexOne[1]
        # print(dX, dY)

        return math.hypot(dX, dY)

    def get_vertices_from_triangles(self, triangle_ids):
        allVertices = set()

        for tri in triangle_ids:
            for vertex in self.triangles[tri]['vertices']:
                vertexValue = self.vertices[vertex]
                allVertices.add(vertexValue)

        return allVertices

    # ====================================== #
    #
    #   Detection
    #
    # ====================================== #

    def all_sides_valid(self, triangle_id, length_threshold):
        vertices = self.triangles[triangle_id]['vertices']
        for i in [0, 1, 2]:
            edgeVertices = [vertices[i-1], vertices[i]]
            edgeLength = self.edge_length(edgeVertices)
            if edgeLength < length_threshold:
                return False

        return True

    def classify_bends(self, length_threshold):

        allTriangles = self.triangles.keys()
        visitedTriangles = set()
        queue = set()
        validQueue = set()
        invalidQueue = set()
        validTriangles = set()
        invalidTriangles = set()

        # special case, isobath only has three vertices
        if len(allTriangles) == 1:
            triangleId = allTriangles[0]
            if self.all_sides_valid(triangleId, length_threshold):
                validTriangles.add(triangleId)
            elif not self.all_sides_valid(triangleId, length_threshold):
                invalidTriangles.add(triangleId)

            return invalidTriangles
        # special case, isobath has four vertices, two adjacent triangles
        # all triangles should be large enough
        elif len(allTriangles) == 2:
            validCounter = 0
            for triangleId in allTriangles:
                if self.all_sides_valid(triangleId, length_threshold):
                    validCounter += 1
            if validCounter == 2:
                validTriangles = set(allTriangles)
            else:
                invalidTriangles = set(allTriangles)

            return invalidTriangles
        # end special cases

        foundThree = False
        for triangleId in allTriangles:
            if self.has_three_neighbors(triangleId):
                print(triangleId)
                # three-side tri is always valid, no overlap with isobath
                validTriangles.add(triangleId)
                validQueue.add(triangleId)
                visitedTriangles.add(triangleId)
                foundThree = True
                break

        if not foundThree:
            for triangleId in allTriangles:
                if self.number_neighbors(triangleId) == 2:
                    print(triangleId)
                    validQueue.add(triangleId)
                    break

        finished = False
        i = 0

        while not finished:

            # print('\nvalidQueue: ', validQueue)

            for triangle in validQueue.copy():
                for adjacentTriangle in self.adjacent_triangles(triangle):
                    # print('------\nValids', triangle, adjacentTriangle)
                    if adjacentTriangle in visitedTriangles:
                        # print('indexed')
                        continue
                    elif self.has_three_neighbors(adjacentTriangle):
                        # print('3 neighbors')
                        validTriangles.add(adjacentTriangle)
                        validQueue.add(adjacentTriangle)
                        visitedTriangles.add(adjacentTriangle)
                    else:
                        sharedEdge = self.shared_edge(triangle, adjacentTriangle)
                        if self.edge_length(sharedEdge) < length_threshold:
                            # print('smaller threshold', self.edge_length(sharedEdge))
                            invalidTriangles.add(adjacentTriangle)
                            invalidQueue.add(adjacentTriangle)
                            visitedTriangles.add(adjacentTriangle)
                        else:
                            # print('larger threshold')
                            validTriangles.add(adjacentTriangle)
                            validQueue.add(adjacentTriangle)
                            visitedTriangles.add(adjacentTriangle)

                validQueue.discard(triangle)

            # print('invalidQueue:, ', invalidQueue)
            for triangle in invalidQueue.copy():
                for adjacentTriangle in self.adjacent_triangles(triangle):
                    # print('------\nInvalids', triangle, adjacentTriangle)
                    if adjacentTriangle in visitedTriangles:
                        # print('indexed')
                        continue
                    elif self.has_three_neighbors(adjacentTriangle):
                        # print('3 neighbors')
                        validTriangles.add(adjacentTriangle)
                        validQueue.add(adjacentTriangle)
                        visitedTriangles.add(adjacentTriangle)
                    else:
                        sharedEdge = self.shared_edge(triangle, adjacentTriangle)
                        if self.edge_length(sharedEdge) < length_threshold:
                            # print('smaller threshold', self.edge_length(sharedEdge))
                            invalidTriangles.add(adjacentTriangle)
                            invalidQueue.add(adjacentTriangle)
                            visitedTriangles.add(adjacentTriangle)
                        else:
                            # print('larger threshold')
                            for neighboringTriangle in self.adjacent_triangles(adjacentTriangle):
                                if neighboringTriangle != triangle:
                                    sharedEdge = self.shared_edge(
                                        adjacentTriangle, neighboringTriangle)
                                    if self.edge_length(sharedEdge) < length_threshold:
                                        invalidTriangles.add(adjacentTriangle)
                                        invalidQueue.add(adjacentTriangle)
                                        visitedTriangles.add(adjacentTriangle)
                                    else:
                                        validTriangles.add(adjacentTriangle)
                                        validQueue.add(adjacentTriangle)
                                        visitedTriangles.add(adjacentTriangle)

                invalidQueue.discard(triangle)

                # for triangle in queue.copy():
                #     neighboringTriangles = self.triangles[triangle]['neighbors']
                #     for neighboringTriangle in neighboringTriangles:
                #         sharedEdge = self.shared_edge(triangle, neighboringTriangle)
                #         print(neighboringTriangle, sharedEdge, self.edge_length(sharedEdge))

            if len(visitedTriangles) == len(allTriangles):
                finished = True

            # i += 1
            # if i > 200:
            #     print('iter limit')
            #     finished = True

        return invalidTriangles

        # for triangle in allTriangles:
        #     neighboringTriangles = self.triangles[triangle]['neighbors']
        #     vertices = self.triangles[triangle]['vertices']
        #     print(triangle, vertices, neighboringTriangles)
        #
        #     edgesToTest = []
        #     for i, neighboringTriangle in enumerate(neighboringTriangles):
        #         if neighboringTriangle != '-1':
        #             # print(i)
        #             edgesToTest.append(i)
        #
        #     # print(edgesToTest)
        #     for edgeIndex in edgesToTest:
        #         # print('edgeIndex: ', edgeIndex)
        #         edge = vertices.copy()
        #         del edge[edgeIndex]
        #         # print('edge: ', edge)
        #
        #         if self.edge_length(edge) < length_threshold:
        #             print('im exceeding threshold!', self.edge_length(edge))
        #             invalidTriangles.add(triangle)
        #             continue
        #
        # self.export_triangles_shp(triangle_ids=invalidTriangles)

    # ====================================== #
    #
    #   Shewchuk
    #
    # ====================================== #

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

    def execute_constrained(self, pathToFile):
        print(pathToFile)
        subprocess.run('./triangle -pn "{}"'.format(pathToFile), shell=True)

    def parse_output(self, inputPath):
        outputFilePart = os.path.splitext(inputPath)[0]

        self.neighPath = outputFilePart + '.1.neigh'
        self.elePath = outputFilePart + '.1.ele'
        self.triangles = dict()

        with open(self.elePath) as elef:
            # print('\nele file:')
            for line in elef.readlines()[1:]:
                if not line.startswith('#'):
                    tri = line.split()
                    # print(line.split())
                    self.triangles[tri[0]] = {'vertices': [
                        tri[1], tri[2], tri[3]], 'neighbors': []}

        with open(self.neighPath) as neighf:
            # print('neighFile: ')
            for line in neighf.readlines()[1:]:
                if not line.startswith('#'):
                    neigh = line.split()
                    # print(neigh)
                    triangleNeighbors = self.triangles[neigh[0]]['neighbors']

                    for i in [1, 2, 3]:
                        # if neigh[i] != '-1':
                        triangleNeighbors.append(neigh[i])
