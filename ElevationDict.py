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


class ElevationDict:

    elevationDict = {}
    updateQueue = {}

    def __init__(self):
        pass

    def add_new(self, vertex_tuple):
        if not tuple(vertex_tuple) in self.elevationDict:
            self.elevationDict[tuple(vertex_tuple)] = {
                'z': vertex_tuple[2], 'z_original': vertex_tuple[2], 'previous_z': None, 'updates': 0}

    def update_z(self, vertex_tuple, new_z):
        # self.elevationDict[tuple(vertex_tuple)]['previous_z'] = self.get_z(vertex_tuple)
        vertexEntry = self.elevationDict[tuple(vertex_tuple)]
        vertexEntry['z'] = new_z
        vertexEntry['updates'] = vertexEntry['updates'] + 1

    def update_previous_z(self, vertex_tuple):
        self.elevationDict[tuple(vertex_tuple)]['previous_z'] = self.get_z(vertex_tuple)

    def get_z(self, vertex_tuple):
        return self.elevationDict[tuple(vertex_tuple)]['z']

    def get_updates(self, vertex_tuple):
        return self.elevationDict[tuple(vertex_tuple)]['updates']

    def get_previous_z(self, vertex_tuple):
        previousZ = self.elevationDict[tuple(vertex_tuple)]['previous_z']
        if previousZ is None:
            return self.get_z(vertex_tuple)
        else:
            return previousZ

    def get_queued_z(self, vertex_tuple):
        if tuple(vertex_tuple) in self.updateQueue:
            queuedZ = self.updateQueue[tuple(vertex_tuple)]
            return queuedZ
        else:
            return False

        # previousZ = self.elevationDict[tuple(vertex_tuple)]['previous_z']
        # if previousZ is None:
        #     return self.get_z(vertex_tuple)
        # else:
        #     return previousZ

    # def get_original_z(self, vertex_tuple):
    #     originalZ = self.elevationDict[tuple(vertex_tuple)]['original_z']
    #     return originalZ

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
