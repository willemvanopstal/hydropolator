from Hydropolator import Hydropolator
from datetime import datetime
import math
import colorama
colorama.init()


def msg(string, type):
    if type == 'warning':
        colColor = colorama.Fore.RED
    elif type == 'info':
        colColor = colorama.Fore.YELLOW  # + colorama.Style.DIM
    elif type == 'infoheader':
        colColor = colorama.Fore.YELLOW + colorama.Style.BRIGHT
    elif type == 'header':
        colColor = colorama.Fore.GREEN

    print(colColor + string + colorama.Style.RESET_ALL)


print('\n\n')

###############################
# Input
###############################

surveyData = '../Data/operatorimplications/simulated_surface_points.txt'
projectName = 'newisobaths'
projectObject = Hydropolator()

# innerNodes = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18,
#               19, 20, 21, 22, 23, 24, 25, 27, 28, 29, 31, 32, 33, 34, 35, 36, 37]
# innerNodes = [str(val) for val in innerNodes]

sharpPointsBreakpoints = [5, 10, 15, 20, 25, 30, 35, 40, 45,
                          50, 55, 60, 65, 70, 75, 80, 85, 90, 100, 120, 140, 160, 180]
sharpPointsBreakpoints = [round(math.radians(val), 3) for val in sharpPointsBreakpoints]
absoluteChangedPointsBreakpoints = [0.2, 0.4, 0.6, 0.8, 1.0, 1.2, 1.4, 1.6, 1.8, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5, 5.0, 6.0,
                                    7.0, 8.0, 9.0, 10.0, 11.0, 12.0, 13.0, 14.0, 15.0, 20.0, 25.0, 30.0, 35.0, 40.0, 45.0, 50.0, 60.0, 70.0, 80.0, 90.0, 100.0]
minChangedPointsBreakpoints = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10,
                               12, 14, 16, 18, 20, 25, 30, 35, 40, 45, 50, 60, 70, 80, 90, 100]
isoLengthBreakpoints = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14,
                        15, 20, 25, 30, 35, 40, 50, 60, 70, 80, 90, 100, 200, 300, 400, 500]
###############################
# Project management
###############################

# possibly initiate new project
# projectObject.init_project(projectName)
# projectObject.load_pointfile(surveyData, 'csv', ' ', flip=True)

# comment this if initiating
if projectObject.load_project(projectName) is True:
    msg('> loaded project', 'header')
    projectObject.summarize_project()

projectObject.set_sharp_points_bins(sharpPointsBreakpoints)
projectObject.set_abs_change_bins(absoluteChangedPointsBreakpoints)
projectObject.set_min_change_bins(minChangedPointsBreakpoints)
projectObject.set_iso_seg_bins(isoLengthBreakpoints)

###############################
# Process
###############################

projectObject.generate_regions()
projectObject.build_graph2()

# projectObject.export_all_node_triangles()
# projectObject.export_all_edge_triangles()
projectObject.generate_isobaths5()

paramDict = {'prepass': 0,
             'densification': 0,
             'angularity_threshold': 1.5,
             'spurgully_threshold': None,
             'spur_threshold': 5,
             'gully_threshold': 5,
             'process': [],
             'maxiter': 100
             }
# prepass if always first if >0
# 'r' defines rings around extracted triangle
# 'n' will define the entire node should be smoothened
# 'nn' will define neighboruing nodes
# [0] defines the process step is stopped if no vertices are updated anymore
# [>0] defines the repeated amount per process, so if [1] the process-line is only done once
paramDict['process'] = [[['angularity', 'r', 1], ['spurs', 'r', 1], ['gullys', 'r', 1], 0],
                        [['angularity', 'r', 2], ['spurs', 'r', 2], ['gullys', 'r', 2], 0],
                        [['angularity', 'r', 4], 3],
                        ]

startTime = datetime.now()

projectObject.start_routine(paramDict, statistics=False)
# sharpPointsDict, allSharpPoints = projectObject.check_isobath_angularity(edgeIds=[], threshold=1.0)
# print('sharp points: ', len(allSharpPoints))
# sharpTriangles = projectObject.get_all_immediate_triangles(sharpPointsDict)
# sharpTriangleVertices = projectObject.get_vertices_from_triangles(sharpTriangles)
#
# projectObject.smooth_vertices_helper2(sharpTriangleVertices)

endTime = datetime.now()
print('elapsed time: ', endTime - startTime)


# for i in range(50):
#     projectObject.generate_isobaths5(edgeIds=[])
#     projectObject.generate_statistics()
#
#     sharpPointsDict, allSharpPoints = projectObject.check_isobath_angularity(
#         edgeIds=[], threshold=1.0)
#     immediateTriangles = projectObject.get_all_immediate_triangles(sharpPointsDict)
#     ringTriangles = projectObject.get_triangle_rings_around_triangles(immediateTriangles, rings=1)
#     ringVertices = projectObject.get_vertices_from_triangles(ringTriangles)
#     print('len vertices: ', len(ringVertices))
#     verticesAreUpdated = projectObject.simple_smooth_and_rebuild(ringVertices)
#
#     if not verticesAreUpdated:
#         break

# projectObject.export_triangles(list(immediateTriangles), 'immediateTriangles')
# projectObject.export_points(allSharpPoints, 'sharpPoints')
#
# ringTriangles = projectObject.get_triangle_rings_around_triangles(immediateTriangles, rings=1)
# projectObject.export_triangles(list(ringTriangles), 'ringTriangles')
#
# ringTriangles = projectObject.get_triangle_rings_around_triangles(immediateTriangles, rings=2)
# projectObject.export_triangles(list(ringTriangles), 'ringTriangles2')


# for point in sharpPointsDict[edgeId]:
#     # print(point)
#     projectObject.get_triangles_to_isopoint_in_edge(point, edgeId)


# projectObject.print_graph()

# projectObject.generate_isobaths5(edgeIds=[])
# projectObject.generate_statistics()

###############################
# Exporting shapefiles
###############################

# projectObject.export_all_isobaths()
# projectObject.export_depth_areas()  # nodeIds=innerNodes)
projectObject.export_all_node_triangles()
projectObject.export_all_edge_triangles()
# projectObject.export_shapefile('output')
# projectObject.export_statistics()


###############################
# Closing project
###############################

projectObject.print_errors()

msg('\n> shutting down...', 'header')
projectObject.write_metafile()
if projectObject.vertexCount:
    projectObject.save_triangulation()
if projectObject.nrNodes:
    projectObject.save_trGraph()
