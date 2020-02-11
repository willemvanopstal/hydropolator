import subprocess as sp
import os


class BendDetector():

    def __init__(self, edge_id, edge_dict, project_name):

        self.edgeId = edge_id
        self.geom = edge_dict['geom']
        self.closed = edge_dict['closed']
        self.projectName = project_name

        print('closed: ', self.closed)
        print('geom: ', self.geom)

        self.nrVertices = len(self.geom)
        if self.closed:
            self.nrVertices -= 1

        self.projectPath = os.path.join(os.getcwd(), 'projects', project_name)

    def write_poly_file(self):
        polyName = '{}.poly'.format(self.edgeId)
        polyPath = os.path.join(self.projectPath, polyName)
