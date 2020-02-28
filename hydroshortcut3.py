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
projectObject.export_all_isobaths()
# projectObject.print_graph()


###############################
# Exporting shapefiles
###############################

# projectObject.export_all_isobaths()
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
