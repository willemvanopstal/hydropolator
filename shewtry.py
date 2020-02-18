from Hydropolator import Hydropolator
from BendDetector import BendDetector
import os

print('\n\n')

surveyData = 'simulated_surface_points.txt'

cwd = os.getcwd()
projectDir = os.path.join(cwd, 'projects')
projectName = 'shewtest'

projectObject = Hydropolator()

# projectObject.init_project(projectName)
# projectObject.load_pointfile(surveyData, 'csv', ' ', flip=True)

if projectObject.load_project(projectName) is True:
    projectObject.summarize_project()

projectObject.generate_regions()
projectObject.build_graph2()
projectObject.generate_isobaths4()

###########################################

getId = '21'
print('getId: ', getId)
edge = projectObject.graph['edges'][getId]

edgeBends = BendDetector(getId, edge, projectName)
edgeBends.write_poly_file()
edgeBends.triangulate()
edgeBends.export_triangles_shp()

invalidTriangles = edgeBends.classify_bends(35.0)
invalidVertices = edgeBends.get_vertices_from_triangles(triangle_ids=invalidTriangles)
edgeBends.export_triangles_shp(triangle_ids=invalidTriangles)

print(invalidVertices)


###########################################

projectObject.export_all_isobaths()
projectObject.export_all_node_triangles()
projectObject.export_all_edge_triangles()
projectObject.export_shapefile('output')

projectObject.print_errors()

print('\n> shutting down...')
projectObject.write_metafile()
if projectObject.vertexCount:
    projectObject.save_triangulation()
if projectObject.nrNodes:
    projectObject.save_trGraph()
