from Hydropolator import Hydropolator
from hydroasci import cli_description
import argparse
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
surveyData = '../Data/operatorimplications/simulated_surface_points.txt'
# ======================== #

parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter,
                                 description=cli_description())

parser.add_argument('-init',
                    metavar='project_name',
                    type=str,
                    default=None,
                    help='create a new project')
parser.add_argument('-project',
                    metavar='project_name',
                    type=str,
                    default=None,
                    help='open an existing project')

parser.add_argument('-clean',
                    metavar='',
                    type=str,
                    default=None,
                    help='clean files older then hh:mm')

parser.add_argument('-pointfile',
                    metavar='input_point_file.csv',
                    type=str,
                    default=None,
                    help='path to initial point file')
parser.add_argument('-filetype',
                    choices=['csv', 'shp'],
                    type=str,
                    default='csv',
                    help='specify filetype of input')
parser.add_argument('-delimiter',
                    metavar=' ',
                    default=' ',
                    type=str,
                    help='specify delimiter fro csv files')
parser.add_argument('-flip',
                    metavar='False',
                    default='False',
                    type=str,
                    help='flip unit positive negative (heights/depths)')

parser.add_argument('-exportshp',
                    metavar='output_file_name',
                    type=str,
                    default=False,
                    help='name for output file')
parser.add_argument('-regions',
                    metavar='isobath series',
                    type=str,
                    default=False,
                    help='creates triangle regions')
parser.add_argument('-triangleregiongraph',
                    metavar=' ',
                    type=str,
                    default=False,
                    help='creates triangle region graph')
parser.add_argument('-isobaths',
                    metavar=' ',
                    type=str,
                    default=False,
                    help='creates isobaths')
parser.add_argument('-graph',
                    metavar=' ',
                    type=str,
                    default=False,
                    help='visualize graph')

parser.add_argument('-angularity',
                    metavar=' ',
                    type=str,
                    default=False,
                    help='check for angularity')

parser.add_argument('-nodearea',
                    metavar=' ',
                    type=str,
                    default=False,
                    help='computes full node areas')

args = parser.parse_args()
cwd = os.getcwd()
projectDir = os.path.join(cwd, 'projects')

if args.init:
    msg('> initializing new project...', 'info')
    projectObject = Hydropolator()
    print(projectObject.init_project(args.init))
    msg('> initialized new project', 'header')
elif args.project:
    msg('> opening existing project', 'info')
    projectObject = Hydropolator()
    if projectObject.load_project(args.project) == True:
        msg('> loaded project', 'header')
        projectObject.summarize_project()
        print(projectObject.insertions)

if args.clean:
    hours = int(args.clean.split(':')[0])
    minutes = int(args.clean.split(':')[1])
    msg('> removing files older than: {} hours, {} minutes'.format(hours, minutes), 'warning')
    projectObject.clean_files(60*hours + minutes)
    msg('> removed all older files', 'info')

if args.flip:
    flip = True
else:
    flip = False

if args.pointfile:
    msg('> inserting points from file', 'info')
    if args.pointfile == 'surveyData':
        projectObject.load_pointfile(surveyData, args.filetype, args.delimiter, flip)
    else:
        projectObject.load_pointfile(args.pointfile, args.filetype, args.delimiter, flip)
    projectObject.summarize_project()

if args.exportshp:
    msg('> exporting shapefiles', 'info')
    projectObject.summarize_project()
    projectObject.export_shapefile(args.exportshp)

if args.regions:
    msg('> generating regions', 'info')
    projectObject.summarize_project()
    projectObject.isoType = args.regions
    projectObject.generate_regions()
    projectObject.index_region_triangles()
    projectObject.export_region_triangles()
    # projectObject.summarize_project()

if args.triangleregiongraph:
    msg('> generating triangle region graph', 'info')
    # projectObject.summarize_project()
    projectObject.generate_regions()
    # projectObject.create_tr_graph()
    if projectObject.nrNodes:
        msg('> triangle region graph already generated', 'warning')
        projectObject.print_graph()
    else:
        projectObject.build_graph2()

    # projectObject.export_shapefile('outputting')


if args.isobaths:
    msg('> generating isobaths...', 'info')
    projectObject.generate_isobaths4()
    msg('> isobaths generated', 'info')
    projectObject.export_all_isobaths()
    # projectObject.make_network_graph()

if args.angularity:
    msg('> checking angularity in isobaths...', 'info')
    projectObject.check_isobath_angularity()
    msg('> checked angulariy in isobaths', 'info')
    projectObject.export_all_angularities()

if args.nodearea:
    msg('> computing area of nodes...', 'info')
    projectObject.compute_node_area()
    msg('> computed area of nodes', 'info')
    # projectObject.export_all_angularities()

if args.graph:
    msg('> visualizing graph...', 'info')
    projectObject.make_network_graph()
    msg('> visualized graph', 'info')

if projectObject:
    projectObject.export_all_edge_triangles()
    projectObject.export_all_node_triangles()
    projectObject.print_graph()
    projectObject.print_errors()

    msg('\n> shutting down...', 'header')
    projectObject.write_metafile()
    if projectObject.vertexCount:
        projectObject.save_triangulation()
    if projectObject.nrNodes:
        projectObject.save_trGraph()
