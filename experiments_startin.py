from shapely import geometry, ops
import itertools
import startin
from datetime import datetime

print(help(startin.DT))

pts = []
pts.append([0.0, 0.0, 11.11])
pts.append([1.0, 0.0, 22.22])
pts.append([1.0, 1.0, 33.33])
pts.append([0.0, 1.0, 44])
pts.append([0.5, 0.49, 44])
pts.append([0.45, 0.69, 44])
# pts.append([-999.9, -999.9, -999.9])
pts.append([0.65, 0.49, 44])
# pts.append([-999.9, -999.9, -999.9])
pts.append([0.75, 0.29, 44])
pts.append([1.5, 1.49, 44])
pts.append([0.6, 0.2, 44])
pts.append([0.45, 0.4, 44])
pts.append([0.1, 0.8, 44])
# pts.append([-909, -1200, 33])

t = startin.DT()
t.insert(pts)

print(t.number_of_vertices(), t.number_of_triangles())
print(t.locate(1.01, 0.87))

print(datetime.now())
for vId in t.locate(1, 0.87):
    print(t.all_vertices()[vId])
print(datetime.now())

print(datetime.now())
for vId in t.locate(1, 0.87):
    print(t.get_point(vId))
print(datetime.now())


def adjacent_triangles(triangle):
    adjacentTriangles = []
    addedVertices = []
    for vId in triangle:
        if len(addedVertices) == 3:
            break
        else:
            for incidentTriangle in t.incident_triangles_to_vertex(vId):
                if len(set(triangle).intersection(incidentTriangle)) == 2 and set(incidentTriangle).difference(triangle) not in addedVertices:
                    adjacentTriangles.append(incidentTriangle)
                    addedVertices.append(set(incidentTriangle).difference(triangle))
    return adjacentTriangles


for tri in t.all_triangles():
    print(tri, adjacent_triangles(tri))
    for neighbor in adjacent_triangles(tri):
        print(t.is_triangle(neighbor))

# for triangle in t.all_triangles():
#     print('----------------')
#     print('tri: ', triangle)
#     adjacentTriangles = []
#     addedVertices = []
#     for vId in triangle:
#         if len(addedVertices) == 3:
#             break
#         else:
#             for incidentTriangle in t.incident_triangles_to_vertex(vId):
#                 if len(set(triangle).intersection(incidentTriangle)) == 2:
#                     # print(incidentTriangle)
#                     # print(set(triangle).intersection(incidentTriangle))
#                     if set(incidentTriangle).difference(triangle) not in addedVertices:
#                         adjacentTriangles.append(incidentTriangle)
#                         addedVertices.append(set(incidentTriangle).difference(triangle))
#     print('adj: ', adjacentTriangles)

print('---')
v = t.all_vertices()[3]
print(t.all_vertices()[3])
t.all_vertices()[3][2] = 25.9
print(t.all_vertices()[3])

dic = {}
dic[tuple(v)] = 8.0
print(dic)

setti = {'3', '5', '7'}
print(setti)
try:
    setti.remove('4')
except:
    pass

print(t.locate(0.75, 0.29))


# create three lines
line_a = geometry.LineString([[0, 0], [1, 1]])
line_b = geometry.LineString([[1, 1], [1, 0]])
line_c = geometry.LineString([[1, 0], [2, 0]])

# combine them into a multi-linestring
multi_line = geometry.MultiLineString([line_a, line_b, line_c])
print(multi_line)  # prints MULTILINESTRING ((0 0, 1 1), (1 1, 2 2), (2 2, 3 3))

# you can now merge the lines
merged_line = ops.linemerge(multi_line)
print(merged_line)  # prints LINESTRING (0 0, 1 1, 2 2, 3 3)

geom = []
for coords in merged_line.coords:
    print(coords)
    geom.append(list(coords))

print(geom)

# for line in merged_line:
#     print(line)
# print('----')
# # if your lines aren't contiguous
# line_a = geometry.LineString([[0, 0], [1, 1]])
# line_b = geometry.LineString([[1, 1], [1, 0]])
# line_c = geometry.LineString([[2, 0], [3, 0]])
#
# # combine them into a multi-linestring
# multi_line = geometry.MultiLineString([line_a, line_b, line_c])
# print(multi_line)  # prints MULTILINESTRING ((0 0, 1 1), (1 1, 1 0), (2 0, 3 0))
#
# # note that it will now merge only the contiguous portions into a component of a new multi-linestring
# merged_line = ops.linemerge(multi_line)
# print(merged_line)  # prints MULTILINESTRING ((0 0, 1 1, 1 0), (2 0, 3 0))
