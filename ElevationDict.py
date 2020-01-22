
class ElevationDict:

    elevationDict = {}

    def __init__(self):
        pass

    def add_new(self, vertex_tuple):
        self.elevationDict[tuple(vertex_tuple)] = {
            'z': vertex_tuple[2], 'z_original': vertex_tuple[2]}

    def get_z(self, vertex_tuple):
        return self.elevationDict[tuple(vertex_tuple)]['z']

    def get_original_z(self, vertex_tuple):
        return self.elevationDict[tuple(vertex_tuple)]['z_original']
