from hydroworker import Hydropolator
from hydroasci import cli_description
import argparse
import os


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
                    default=None,
                    help='name for output file')
parser.add_argument('-regions',
                    metavar='isobath series',
                    type=str,
                    default=None,
                    help='creates triangle regions')

args = parser.parse_args()
cwd = os.getcwd()
projectDir = os.path.join(cwd, 'projects')

if args.init:
    print('> initializing new project')
    projectObject = Hydropolator()
    print(projectObject.init_project(args.init))
elif args.project:
    print('> opening existing project')
    projectObject = Hydropolator()
    if projectObject.load_project(args.project) == True:
        projectObject.summarize_project()

if args.flip:
    flip = True
else:
    flip = False

if args.pointfile:
    print('> inserting points from file')
    if args.pointfile == 'surveyData':
        projectObject.load_pointfile(surveyData, args.filetype, args.delimiter, flip)
    else:
        projectObject.load_pointfile(args.pointfile, args.filetype, args.delimiter, flip)
    projectObject.summarize_project()

if args.exportshp:
    print('> exporting shapefiles')
    projectObject.summarize_project()
    projectObject.export_shapefile(args.exportshp)

if args.regions:
    print('> generating regions')
    projectObject.summarize_project()
    projectObject.generate_regions(args.regions)
    projectObject.index_region_triangles()
    projectObject.export_region_triangles()

# parser.add_argument('-dft', action='store_true',
#                     help='get db credentials from default file')
# parser.add_argument('-db', default=None, type=str, help='database name')
# parser.add_argument('-u', default=None, type=str, help='database user')
# parser.add_argument('-pw', default=None, type=str, help='database password')
# parser.add_argument('-load', metavar='input.shp', default=None, type=str,
#                     help='load measurements from shapefile, inputfile.shp')
# parser.add_argument('-loadmask', metavar='input.shp', default=None, type=str,
#                     help='load mask polygon from shapefile, inputfile.shp')
# parser.add_argument('-status', default=None, type=str, help='retrieve status')
# parser.add_argument("-vis", choices=["m", "d", "v"], type=str, help="visualize features")
# parser.add_argument('-tri', action='store_true', help='constructs the delaunay triangulation')
# parser.add_argument('-vor', action='store_true', help='constructs the voronoi diagram')
# parser.add_argument('-wt', action='store_true', help='establishes the worker table')
# parser.add_argument('-cont', action='store_true', help='contours')
# parser.add_argument('-inter', default=None, type=int, help='interpolate')
# parser.add_argument('-resetinter', action='store_true', help='reset interpolation')
#
# parser.add_argument('-cout', default=None, type=str,
#                     help='contour shapefile', metavar='contour_output.shp')
# parser.add_argument('-c', nargs='+', type=float, help='isobaths values')
#
#
# args = parser.parse_args()
# dbName = args.db
# dbUser = args.u
# dbPass = args.pw
# if args.dft:
#     dbName, dbUser, dbPass = get_default_database()
#     print('accessing database: {}\nuser: {}\n'.format(dbName, dbUser))
#
# if args.load:
#     print('> loading measurements')
#     load_measurements(dbName, dbUser, dbPass, args.load)
# if args.loadmask:
#     print('> loading mask')
#     load_mask(dbName, dbUser, dbPass, args.loadmask)
# if args.tri:
#     print('> constructing Delaunay triangulation')
#     construct_delaunay(dbName, dbUser, dbPass)
# if args.vor:
#     print('> constructing Voronoi diagram')
#     construct_voronoi(dbName, dbUser, dbPass)
# if args.wt:
#     print('> establishing worker table')
#     establish_worker_table(dbName, dbUser, dbPass)
# if args.cont:
#     print('> establishing contours')
#     establish_contours(dbName, dbUser, dbPass)
# if args.inter:
#     print('> interpolating')
#     interpolate(dbName, dbUser, dbPass, args.inter)
# if args.resetinter:
#     print('> resetting')
#     reset_interpolate(dbName, dbUser, dbPass)
#
# if args.status == 'm':
#     print('> retrieving status of measurements')
#     status_measurements(get_measurements(dbName, dbUser, dbPass))
# if args.vis == 'm':
#     print('> visualizing measurements')
#     visualize_measurements(get_measurements(dbName, dbUser, dbPass))
# if args.vis in ['d', 'v']:
#     if args.vis == 'd':
#         print('> visualizing delaunay triangles')
#         visualize_delaunay_voronoi(dbName, dbUser, dbPass, 'delaunay_cells')
#     elif args.vis == 'v':
#         print('> visualizing voronoi cells')
#         visualize_delaunay_voronoi(dbName, dbUser, dbPass, 'voronoi_cells')
#
# if args.cout and args.c:
#     if args.c == [99901]:
#         cList = [15.01, 14.01, 13.01, 12.01, 11.01, 10.01, 9.01, 8.01, 7.01,
#                  6.01, 5.01, 4.01, 3.01, 2.01, 1.01, 0.01, -1.01, -2.01, -3.01]
#     elif args.c == [99900]:
#         cList = [15, 14, 13, 12, 11, 10, 9, 8, 7, 6, 5, 4, 3, 2, 1, 0, -1, -2, -3]
#     elif args.c == [99905]:
#         cList = [50, 40, 30, 20, 15, 10, 7.5, 5, 2.5, 1, 0.5, 0.0]
#     else:
#         cList = args.c
#     print('> constructing and exporting contours\n  output: {}\n  isobaths: {}'.format(args.cout, cList))
#     #export_contours(dbName, dbUser, dbPass, args.cout, args.c)
#     manual_contours(dbName, dbUser, dbPass, args.cout, cList)
