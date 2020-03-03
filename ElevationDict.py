
class ElevationDict:

    elevationDict = {}
    updateQueue = {}

    def __init__(self):
        pass

    def add_new(self, vertex_tuple):
        self.elevationDict[tuple(vertex_tuple)] = {
            'z': vertex_tuple[2], 'z_original': vertex_tuple[2], 'previous_z': None}

    def update_z(self, vertex_tuple, new_z):
        # self.elevationDict[tuple(vertex_tuple)]['previous_z'] = self.get_z(vertex_tuple)
        self.elevationDict[tuple(vertex_tuple)]['z'] = new_z

    def update_previous_z(self, vertex_tuple):
        self.elevationDict[tuple(vertex_tuple)]['previous_z'] = self.get_z(vertex_tuple)

    def get_z(self, vertex_tuple):
        return self.elevationDict[tuple(vertex_tuple)]['z']

    def get_previous_z(self, vertex_tuple):
        previousZ = self.elevationDict[tuple(vertex_tuple)]['previous_z']
        if previousZ is None:
            return self.get_z(vertex_tuple)
        else:
            return previousZ

    def get_original_z(self, vertex_tuple):
        originalZ = self.elevationDict[tuple(vertex_tuple)]['original_z']
        return originalZ

    def remove_previous_z(self, vertex_tuple):
        self.elevationDict[tuple(vertex_tuple)]['previous_z'] = None

    def get_original_z(self, vertex_tuple):
        return self.elevationDict[tuple(vertex_tuple)]['z_original']

    def add_to_queue(self, vertex_tuple, new_z):
        self.updateQueue[tuple(vertex_tuple)] = new_z

    def update_previous_z_from_queue(self):
        for vertex in self.updateQueue.keys():
            if not self.elevationDict[tuple(vertex)]['previous_z']:
                # print('previous updating! ', vertex)
                self.update_previous_z(vertex)

    def update_values_from_queue(self):
        for vertex in self.updateQueue.keys():
            self.update_z(vertex, self.updateQueue[vertex])

        self.updateQueue = dict()
