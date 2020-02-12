from Hydropolator import Hydropolator
import os
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

# ======================== #
# surveyData = 'simulated_surface_points.txt'
surveyData = '../Data/operatorimplications/simulated_surface_points.txt'
# ======================== #

cwd = os.getcwd()
projectDir = os.path.join(cwd, 'projects')

#######################################################
# Process goes here

projectName = 'regiongraphtesttttp'

projectObject = Hydropolator()

# # possibly initiatie new project
# projectObject.init_project(projectName)
# projectObject.load_pointfile(surveyData, 'csv', ' ', flip=True)

# comment this if initiating
if projectObject.load_project(projectName) is True:
    msg('> loaded project', 'header')
    projectObject.summarize_project()

# cleaning files
hours = 12
minutes = 0
msg('> removing files older than: {} hours, {} minutes'.format(hours, minutes), 'warning')
projectObject.clean_files(60*hours + minutes)
msg('> removed all older files', 'info')

msg('> generating triangle region graph', 'info')
projectObject.generate_regions()
projectObject.build_graph2()


########
projectObject.generate_isobaths4()
sharpPoints = projectObject.check_isobath_angularity(edgeIds=[], threshold=0.6)
projectObject.export_all_angularities()
projectObject.export_all_isobaths()


# print(sharpPoints)
verticesToSmooth = set()
for point in sharpPoints:
    verticesToSmooth.update(projectObject.get_vertices_around_point(point, rings=1))
print('nr vertices: ', len(verticesToSmooth))

projectObject.simple_smooth_and_rebuild(verticesToSmooth)


########
projectObject.generate_isobaths4()
projectObject.check_isobath_angularity()
projectObject.export_all_angularities()

projectObject.export_all_isobaths()
projectObject.export_all_node_triangles()
projectObject.export_all_edge_triangles()
projectObject.export_shapefile('output')

projectObject.print_errors()

msg('\n> shutting down...', 'header')
projectObject.write_metafile()
if projectObject.vertexCount:
    projectObject.save_triangulation()
if projectObject.nrNodes:
    projectObject.save_trGraph()
