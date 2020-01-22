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
