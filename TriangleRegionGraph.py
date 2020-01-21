# import startin
import bisect


class TriangleRegionGraph:

    # Graph
    graph = {}
    nrNodes = 0
    nrEdges = 0

    regions = []
    isobathValues = []

    # Triangulation
    triangulation = None
    vertices = []
    triangles = []
    triangleRegions = []

    def __init__(self):
        return

    def minmax_from_triangle(self, vertex_list):
        elevations = []
        for vId in vertex_list:
            elevations.append(self.triangulation.get_point(vId)[2])
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

    def find_intervals(self, triangle):
        min, max = self.minmax_from_triangle(triangle)
        # print(min, max)
        intervals = []
        for index in range(bisect.bisect_left(self.isobathValues, min), bisect.bisect_left(self.isobathValues, max) + 1):
            # print(self.regions[index])
            intervals.append(self.regions[index])
            # self.triangleRegions[index].append(triangle)
        return intervals

    def initialize_graph(self, triangulation):
        print('> initializing graph')
        self.triangulation = triangulation
        self.vertices = triangulation.all_vertices()
        self.triangles = triangulation.all_triangles()

        # for triangle in self.triangles:
        #     print(triangle, self.minmax_from_triangle(triangle))

    def add_node(self, triangle, region):
        pass

    def build_graph(self):
        startingTriangle = self.triangles[25]

        print('=======starter=======')
        print(self.minmax_from_triangle(startingTriangle))
        print(self.find_intervals(startingTriangle))
        print('----neighbors----')
        for neighbor in self.adjacent_triangles(startingTriangle):
            print(neighbor, self.find_intervals(neighbor))

        pass
