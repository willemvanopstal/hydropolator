from Hydropolator import Hydropolator
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
# print(sharpPointsBreakpoints)

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

###############################
# Process
###############################

projectObject.generate_regions()
projectObject.build_graph2()

projectObject.generate_isobaths5()
# projectObject.generate_depth_areas()  # nodeIds=innerNodes)

projectObject.set_sharp_points_bins(sharpPointsBreakpoints)
projectObject.set_abs_change_bins(absoluteChangedPointsBreakpoints)
projectObject.set_min_change_bins(minChangedPointsBreakpoints)
projectObject.set_iso_seg_bins(isoLengthBreakpoints)


# projectObject.check_all_iso_lengths()
# projectObject.check_all_sharp_points()
# projectObject.check_all_point_diffs()
projectObject.generate_statistics()
# projectObject.generate_statistics()

projectObject.export_statistics()

# projectObject.print_graph()


###############################
# Exporting shapefiles
###############################

# projectObject.export_all_isobaths()
# projectObject.export_depth_areas()  # nodeIds=innerNodes)
# projectObject.export_all_node_triangles()
# projectObject.export_all_edge_triangles()
# projectObject.export_shapefile('output')

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
