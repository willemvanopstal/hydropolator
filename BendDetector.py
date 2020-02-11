import subprocess as sp
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
            vertexHeader = '{} 2 0 0\n'.format(self.nrVertices)
            segmentHeader = '{} 0\n'.format(self.nrSegments)
            holeHeader = '{}\n'.format(0)

            counter = 1
            vertexList = ''
            segmentList = ''
            for v in self.geom[:-1]:
                vertexEntry = '{} {} {}\n'.format(counter, v[0], v[1])
                vertexList = vertexList + vertexEntry

                segmentEnd = (counter + 1) % (self.nrVertices + 1)
                if segmentEnd == 0:
                    segmentEnd = 1
                segmentEntry = '{} {} {}\n'.format(
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
