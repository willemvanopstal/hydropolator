from Hydropolator import Hydropolator
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

innerNodes = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18,
              19, 20, 21, 22, 23, 24, 25, 27, 28, 29, 31, 32, 33, 34, 35, 36, 37]
innerNodes = [str(val) for val in innerNodes]

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
projectObject.generate_depth_areas()  # nodeIds=innerNodes)
# projectObject.print_graph()


###############################
# Exporting shapefiles
###############################

projectObject.export_all_isobaths()
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
