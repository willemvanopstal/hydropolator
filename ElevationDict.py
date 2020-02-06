
class ElevationDict:

    elevationDict = {}
    updateQueue = {}

    def __init__(self):
        pass

    def add_new(self, vertex_tuple):
        self.elevationDict[tuple(vertex_tuple)] = {
            'z': vertex_tuple[2], 'z_original': vertex_tuple[2]}

    def update_z(self, vertex_tuple, new_z):
        self.elevationDict[tuple(vertex_tuple)]['z'] = new_z

    def get_z(self, vertex_tuple):
        return self.elevationDict[tuple(vertex_tuple)]['z']

    def get_original_z(self, vertex_tuple):
        return self.elevationDict[tuple(vertex_tuple)]['z_original']

    def add_to_queue(self, vertex_tuple, new_z):
        self.updateQueue[tuple(vertex_tuple)] = new_z

    def update_values_from_queue(self):
        for vertex in self.updateQueue.keys():
            self.update_z(vertex, self.updateQueue[vertex])

        self.updateQueue = dict()
