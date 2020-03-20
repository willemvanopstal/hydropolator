import os
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
projectName = 'new_graphing2'
projectObject = Hydropolator()

###############################
# Project management
###############################

cwd = os.getcwd()
projectsDir = os.path.join(cwd, 'projects')
projectDir = os.path.join(projectsDir, projectName)
projectExists = os.path.isdir(projectDir)

if projectExists:
    if projectObject.load_project(projectName) is True:
        msg('> loaded project', 'header')
        projectObject.summarize_project()
else:
    msg('> init new project', 'header')
    projectObject.init_project(projectName)
    projectObject.load_pointfile(surveyData, 'csv', ' ', flip=True)

###############################
# Process
###############################


startTime = datetime.now()

# delete entire graph
projectObject.graph = {'nodes': {}, 'edges': {}, 'shallowestNodes': set(), 'deepestNodes': set()}
projectObject.triangleInventory = dict()
projectObject.nrNodes = 0
projectObject.nrEdges = 0

projectObject.generate_regions()
projectObject.build_graph_new2()
projectObject.generate_isobaths5()

endTime = datetime.now()
print('elapsed time: ', endTime - startTime)


# projectObject.build_graph_new2()


projectObject.print_graph()

###############################
# Exporting shapefiles
###############################

# projectObject.export_all_isobaths()
# projectObject.export_depth_areas()  # nodeIds=innerNodes)
# projectObject.export_all_node_triangles()
# projectObject.export_all_edge_triangles()
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
