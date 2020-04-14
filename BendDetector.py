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


import subprocess
import shapefile
import os
import math
from datetime import datetime
import numpy as np


class BendDetector():

    def __init__(self, edge_id, edge_dict, project_name):

        self.edgeId = edge_id
        self.geom = edge_dict['geom']
        self.closed = edge_dict['closed']
        self.projectName = project_name

        # print('closed: ', self.closed)
        # print('geom: ', self.geom)

        geomLength = len(self.geom)
        # self.nrVertices = len(self.geom)
        # self.nrSegments = len(self.geom) - 1
        if self.closed:
            self.nrVertices = geomLength - 1
            self.nrSegments = geomLength - 1
        if not self.closed:
            self.nrVertices = geomLength
            self.nrSegments = geomLength - 1

        self.projectPath = os.path.join(os.getcwd(), 'projects', project_name)
        self.get_bounds()

    def get_bounds(self):
        xMin = 10e9
        xMax = -10e9
        yMin = 10e9
        yMax = -10e9

        for vertex in self.geom:
            vX, vY = vertex[0], vertex[1]
            if vX > xMax:
                xMax = vX
            if vX < xMin:
                xMin = vX
            if vY > yMax:
                yMax = vY
            if vY < yMin:
                yMin = vY

        self.xMin = xMin
        self.xMax = xMax
        self.yMin = yMin
        self.yMax = yMax

    def clean_output_files(self):
        outputFiles = ['ele', 'neigh', 'node', 'poly']
        for fileType in outputFiles:
            fileName = '{}.1.{}'.format(self.edgeId, fileType)
            filePath = os.path.join(self.projectPath, fileName)
            os.remove(filePath)

    def clean_input_file(self):
        fileName = '{}.poly'.format(self.edgeId)
        filePath = os.path.join(self.projectPath, fileName)
        os.remove(filePath)

    # ====================================== #
    #
    #   Exports
    #
    # ====================================== #

    def now(self):
        return datetime.now().strftime("%Y%m%d_%H%M%S")

    def get_triangle_geoms(self, triangle_ids=[]):
        if triangle_ids == []:
            triangle_ids = self.triangles.keys()

        geoms = []

        for triangleId in triangle_ids:
            triangleGeom = self.triangle_geom(triangleId)
            geoms.append([triangleGeom])

        return geoms

    def export_triangles_shp(self, triangle_ids=[], name='tris', multi=None):
        # multi = { 'name': {triangle_ids} }
        if len(triangle_ids) == 0:
            triangle_ids = self.triangles.keys()
        exportDict = {name: triangle_ids}
        if multi:
            exportDict = multi

        for multiName in exportDict.keys():
            multiTriangles = exportDict[multiName]
            triangleShpFile = os.path.join(
                self.projectPath, 'constrained_triangles_{}_{}_{}.shp'.format(multiName, self.edgeId, self.now()))

            with shapefile.Writer(triangleShpFile) as wt:
                wt.field('triid', 'C')
                wt.field('vertices', 'C')
                wt.field('neighbors', 'C')
                for triangle in multiTriangles:
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

        if type(edge_vertices[0]) == int:
            edge_vertices = [str(value) for value in edge_vertices]

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

    def distance_between_points(self, ptA, ptB):

        dX = ptB[0] - ptA[0]
        dY = ptB[1] - ptA[1]

        distance = math.hypot(dX, dY)

        return distance

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

    def get_spurs_and_gullys2(self, gully_threshold=0, spur_threshold=0):

        allTriangles = self.triangles.keys()
        spurTriangles = set()
        gullyTriangles = set()

        for triangleId in allTriangles:
            # print(triangleId, self.triangles[triangleId])
            triangleVertices = self.triangles[triangleId]['vertices']

            # print('\n', triangleId, triangleVertices)

            leftOfSegment = False
            rightOfSegment = False
            edgeLengths = []
            isoSeg = None

            for i in [0, 1, 2]:
                # edgeIndices = [i, (i+1)%3]
                edge = (int(triangleVertices[i]), int(triangleVertices[(i+1) % 3]))
                # print(edge)
                if not leftOfSegment and edge in self.segments:
                    rightOfSegment = True
                    isoSeg = (str(edge[0]), str(edge[1]))
                elif not rightOfSegment and tuple(reversed(edge)) in self.segments:
                    leftOfSegment = True
                    isoSeg = (str(edge[0]), str(edge[1]))
                else:
                    edgeLength = self.edge_length(edge)
                    edgeLengths.append(edgeLength)
            # print(rightOfSegment, leftOfSegment)

            # print('edgeLengths: ', edgeLengths)

            if len(edgeLengths) == 1:
                # triangle bounded by two iso-segments
                # not checking for orthogonality
                if leftOfSegment:
                    if edgeLengths[0] < gully_threshold:
                        gullyTriangles.add(triangleId)
                elif rightOfSegment:
                    if edgeLengths[0] < spur_threshold:
                        spurTriangles.add(triangleId)

            elif len(edgeLengths) == 2:
                # triangles touches one isosegment
                # need to check what kind of triangle it is
                # print('isoSeg: ', isoSeg)
                isoLine = [self.get_point(vId) for vId in isoSeg]
                isoLineXs = [isoLine[0][0], isoLine[1][0]]
                isoLineYs = [isoLine[0][1], isoLine[1][1]]
                # print('isoLine: ', isoLine)

                openPoint = list(set(triangleVertices).difference(isoSeg))
                openPointVals = self.get_point(openPoint[0])
                # print(openPoint, openPointVals)

                # https://stackoverflow.com/a/49073142
                # project point onto line segment
                x = np.array(openPointVals)
                u = np.array(isoLine[0])
                v = np.array(isoLine[1])
                n = v - u
                n /= np.linalg.norm(n, 2)
                P = u + n*np.dot(x - u, n)

                projectedPoint = [P[0], P[1]]
                # print('projectedPoint: ', projectedPoint)

                if min(isoLineXs) <= projectedPoint[0] <= max(isoLineXs) and min(isoLineYs) <= projectedPoint[1] <= max(isoLineYs):
                    # print('projected on line')
                    minDistance = self.distance_between_points(openPointVals, projectedPoint)
                    # print(minDistance)
                else:
                    # print('projected outside line')
                    # print(min(edgeLengths))
                    minDistance = min(edgeLengths)

                if leftOfSegment:
                    if minDistance < gully_threshold:
                        gullyTriangles.add(triangleId)
                elif rightOfSegment:
                    if minDistance < spur_threshold:
                        spurTriangles.add(triangleId)

            # if leftOfSegment:
            #     # deeper than contour, gully
            #     invalidCounter = 0
            #     for l in edgeLengths:
            #         if l < gully_threshold:
            #             invalidCounter += 1
            #     if invalidCounter >= nrInvalidEdges:
            #         gullyTriangles.add(triangleId)
            #
            # elif rightOfSegment:
            #     # shallower than contour, spur
            #     invalidCounter = 0
            #     for l in edgeLengths:
            #         if l < spur_threshold:
            #             invalidCounter += 1
            #     if invalidCounter >= nrInvalidEdges:
            #         spurTriangles.add(triangleId)

            # if leftOfSegment or rightOfSegment:
            #     # print('im directly adjacent to isobath')
            #     invalidCounter = 0
            #     for l in edgeLengths:
            #         if l < length_threshold:
            #             invalidCounter += 1
            #
            #     if invalidCounter >= nrInvalidEdges:  # input amount of invalid edges needed to trigger
            #         # print('im invalid triangle')
            #         if leftOfSegment:
            #             # print('left, deeper, gully')
            #             gullyTriangles.add(triangleId)
            #         elif rightOfSegment:
            #             # print('right, shallower, spur')
            #             spurTriangles.add(triangleId)

            # print(edgeLengths)

        return spurTriangles, gullyTriangles

    def get_spurs_and_gullys(self, gully_threshold=0, spur_threshold=0, nrInvalidEdges=1):

        allTriangles = self.triangles.keys()
        spurTriangles = set()
        gullyTriangles = set()

        for triangleId in allTriangles:
            # print(triangleId, self.triangles[triangleId])
            triangleVertices = self.triangles[triangleId]['vertices']

            # print(triangleId, triangleVertices)

            leftOfSegment = False
            rightOfSegment = False
            edgeLengths = []
            for i in [0, 1, 2]:
                # edgeIndices = [i, (i+1)%3]
                edge = (int(triangleVertices[i]), int(triangleVertices[(i+1) % 3]))
                # print(edge)
                if not leftOfSegment and edge in self.segments:
                    rightOfSegment = True
                elif not rightOfSegment and tuple(reversed(edge)) in self.segments:
                    leftOfSegment = True
                else:
                    edgeLength = self.edge_length(edge)
                    edgeLengths.append(edgeLength)
            # print(rightOfSegment, leftOfSegment)

            # print('edgeLengths: ', edgeLengths)

            if leftOfSegment:
                # deeper than contour, gully
                invalidCounter = 0
                for l in edgeLengths:
                    if l < gully_threshold:
                        invalidCounter += 1
                if invalidCounter >= nrInvalidEdges:
                    gullyTriangles.add(triangleId)

            elif rightOfSegment:
                # shallower than contour, spur
                invalidCounter = 0
                for l in edgeLengths:
                    if l < spur_threshold:
                        invalidCounter += 1
                if invalidCounter >= nrInvalidEdges:
                    spurTriangles.add(triangleId)

            # if leftOfSegment or rightOfSegment:
            #     # print('im directly adjacent to isobath')
            #     invalidCounter = 0
            #     for l in edgeLengths:
            #         if l < length_threshold:
            #             invalidCounter += 1
            #
            #     if invalidCounter >= nrInvalidEdges:  # input amount of invalid edges needed to trigger
            #         # print('im invalid triangle')
            #         if leftOfSegment:
            #             # print('left, deeper, gully')
            #             gullyTriangles.add(triangleId)
            #         elif rightOfSegment:
            #             # print('right, shallower, spur')
            #             spurTriangles.add(triangleId)

            # print(edgeLengths)

        return spurTriangles, gullyTriangles

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
                # print(triangleId)
                # three-side tri is always valid, no overlap with isobath
                validTriangles.add(triangleId)
                validQueue.add(triangleId)
                visitedTriangles.add(triangleId)
                foundThree = True
                break

        if not foundThree:
            for triangleId in allTriangles:
                if self.number_neighbors(triangleId) == 2:
                    # print(triangleId)
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

        pass

    # ====================================== #
    #
    #   Shewchuk
    #
    # ====================================== #

    def write_poly_file(self):
        # only takes into account one simple closed isobath
        polyName = '{}.poly'.format(self.edgeId)
        polyPath = os.path.join(self.projectPath, polyName)
        # print(polyPath)

        if not self.closed:
            # print(self.geom, self.nrVertices, self.nrSegments)
            vertexHeader = '{} 2 0 1\n'.format(self.nrVertices)
            segmentHeader = '{} 1\n'.format(self.nrSegments)
            holeHeader = '{}\n'.format(0)

            counter = 1
            vertexList = ''
            segmentList = ''

            self.vertices = dict()
            self.segments = set()

            for v in self.geom:
                vertexEntry = '{} {} {} 2\n'.format(counter, v[0], v[1])
                self.vertices[str(counter)] = (v[0], v[1])
                vertexList = vertexList + vertexEntry

                # segmentEnd = (counter + 1) % (self.nrVertices + 1)
                # if segmentEnd == 0:
                #     segmentEnd = 1
                if not counter == self.nrSegments:
                    segmentEntry = '{} {} {} 2\n'.format(
                        counter, counter, counter + 1)
                    self.segments.add((counter, counter + 1))
                    # print((counter, segmentEnd))
                    segmentList = segmentList + segmentEntry

                counter += 1

        if self.closed:
            vertexHeader = '{} 2 0 1\n'.format(self.nrVertices)
            segmentHeader = '{} 1\n'.format(self.nrSegments)
            holeHeader = '{}\n'.format(0)

            counter = 1
            vertexList = ''
            segmentList = ''

            self.vertices = dict()
            self.segments = set()

            for v in self.geom[:-1]:
                vertexEntry = '{} {} {} 2\n'.format(counter, v[0], v[1])
                self.vertices[str(counter)] = (v[0], v[1])
                vertexList = vertexList + vertexEntry

                segmentEnd = (counter + 1) % (self.nrVertices + 1)
                if segmentEnd == 0:
                    segmentEnd = 1
                segmentEntry = '{} {} {} 2\n'.format(
                    counter, counter, segmentEnd)
                self.segments.add((counter, segmentEnd))
                # print((counter, segmentEnd))
                segmentList = segmentList + segmentEntry

                counter += 1

        with open(polyPath, 'w') as of:
            of.write(vertexHeader)
            of.write(vertexList)
            of.write(segmentHeader)
            of.write(segmentList)
            of.write(holeHeader)
        # print(vertexHeader)
        # print(vertexList)
        # print(segmentHeader)
        # print(segmentList)

    def triangulate(self):
        # only takes into account one simple closed isobath
        polyName = '{}.poly'.format(self.edgeId)
        polyPath = os.path.join(self.projectPath, polyName)
        # print(polyPath)

        self.execute_constrained(polyPath)

        self.parse_output(polyPath)
        # print(self.vertices)
        # print(self.triangles)
        pass

    def execute_constrained(self, pathToFile):
        # print(pathToFile)
        FNULL = open(os.devnull, 'w')

        runCommand = './triangle -pcn "{}"'.format(pathToFile)
        # print(runCommand)
        subprocess.run(runCommand, shell=True, stdout=FNULL)

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

        self.clean_output_files()
