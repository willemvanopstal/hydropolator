Hydropolator is a program to interact with hydrographic survey data with the main purpose of generating and generalizing depth contours for different chart scales. Great attention is given to the fact these contours should be legible, safe, morphological and topological correct.

This conceptual implementation is a proof of concept for my MSc. Thesis in Geomatics: *Automatic isobath generalisation for navigational charts*. The report is available [here](https://repository.tudelft.nl).

#### Very simple example
```python
from Hydropolator import Hydropolator

# Project properties
projectName = 'newyork'
surveyData = '../Data/NOAA/newyork_5m_30k.csv'
x, y, z = 'x', 'y', 'depth'
epsg = '26918'
flipDepth = True

# Project initialisation
hpl = Hydropolator()
hpl.init_project(projectName)
hpl.load_pointfile(surveyData, 'csv', ' ', x, y, z, flip=flipDepth)
hpl.set_crs(epsg)

# Generalisation parameters
paramDict = {'prepass': 1,
             'densification': 1,
             'process': [],
             'densification_process': [],
             'maxiter': 10,
             'angularity_threshold': 1.6,
             'spurgully_threshold': None,
             'spur_threshold': 100,
             'gully_threshold': 100,
             'aspect_threshold': 0.5,
             'size_threshold': 5,
             'aggregation_threshold': 40,
             'min_ring': 1,
             'max_ring': 4
             }

paramDict['process'] = [['spurs', 0], ['gullys', 0], ['angularity', 0]]
paramDict['densification_process'] = [['angularity', 'r', 0],
                                      ['aspect-edges', 'r', 0],
                                      ['size-edges', 'r', 0]
                                      ]

# Process
hpl.generate_regions()
hpl.build_graph2()
hpl.start_routine_new(paramDict)

# Export
hpl.export_all_isobaths()
hpl.export_depth_areas()
hpl.rasterize(resolution=5.0)
```
#### TOC
- [Input](#input)
- [Output](#output)
- [Dependencies](#dependencies)
- [Expected File Structure](#expected-file-structure)
- [Implementation](#hydropolator)
    - [Methods](#methods)
    - [Arguments](#arguments)
    - [Variables](#variables)
    - [Attributes](#attributes)
- [Examples](#examples)


# Input
Main input is a simple xyz file of depth measurements or soundings. The data should be projected with meter units.


# Output

# Dependencies

Hydropolator is implemented in Python 3. For some metrics use is made of the non-Python library [*triangle*](https://www.cs.cmu.edu/~quake/triangle.html). This program should be downloaded separately en placed in the same directory. However, the main program will run without this extension, but some features will not work. It does rely on the following Python packages:

- [StarTIN](https://github.com/hugoledoux/startin_python)
- matplotlib
- networkx
- numpy
- shapefile / pyshp
- pickle
- tabulate
- subprocess
- colorama
- shapely (only for Aggregator.py)

# Expected file structure
```
Hydropolator
├── Hydropolator.py                # Main class file
├── ElevationDict.py               # handles the elevations at each vertex/point/sounding
├── Aggregator.py                  # needs Triangle
├── BendDetector.py                # needs Triangle
├── hydrolauncher.py               # CLI (experimental)
├── hydroshortcut.py               # simple interaction examples
├── triangle                       # triangle file must be downloaded from its own website first
├── projects
│   ├── [projectName]              # each project has its own directory with saved data and output.  
│   │   ├── metafile
│   │   ├── triangulationTracker
│   │   ├── triangleRegionGrap
│   │   ├── triangulationVertices
│   │   ├── vertexElevations
│   │   └── [all output files]     # depends on settings  
│   └── ...             
├── plots                          # plotting statistics
│   ├── stats_preparer_[..].py
│   ├── stats_visualizer_[..].py
│   ├── [outputs]
│   └── [stat data]
├── qgis_styles                    # default styles for qgis
│   ├── qgis_style_painter.py      # PyQGIS script, can be imported in qgis
│   └── ... .qml                   # various qgis style files
└── ...
```
*project directories will be created on initializing a new project. If you want to copy a directory, make sure the included files are present in the structure.*


# Hydropolator

## Methods

#### `load_pointfile(pointFile, fileType, delimiter, xName, yName, dName, flip) -> None`
This loads a .xyz pointfile, filters on snapping tolerance and triangulates the points for further use.
> `pointFile <- str/os.path (None)` path to pointfile  
> `fileType <- str ('csv')` can be csv or shapefile. Shapefile for now not supported  
> `delimiter <- str (None)` csv delimiter  
> `xName <- str ('x')` field for x-coordinate  
> `yName <- str ('y')` field for y-coordinate  
> `dName <- str ('depth')` field for depth value  
> `flip <- Bool (False)` depth is defined as watercolumn below sea-level. If there is water, depth value is positive. Is it is drying, depth value is negative. By setting `flip` to `True`, original depth values from datafile will be flipped.


---
#### `start_routine_new(paramDict, statistics) -> None`
This initiates the smoothing and densification routine. Make sure to pass all parameters needed. The function returns nothing, but changes the data in the parent class.
> `paramDict <- dict (None)` parameters for the process. (see paramDict)  
> `statistics <- Bool (False)` Generates statistics for each iteration

---

#### `start_routine_new(paramDict, statistics) -> None`
This initiates the smoothing and densification routine. Make sure to pass all parameters needed. The function returns nothing, but changes the data in the parent class.
> `paramDict <- dict (None)` parameters for the process. (see paramDict)  
> `statistics <- Bool (False)` Generates statistics for each iteration

---
## Arguments

#### `paramDict <- dict`
This dictionary is used to collect all parameters for the smoothing and densification process. It *must* have all these keys:
> `prepass <- int` number of smoothing iterations, applied on all vertices in the dataset  
> `densification <- int` number of densification iterations, applied after the overall smoothing  
> `maxiter <- int` maximum iteration count, including prepasses, excluding densification  
> `min_ring <- int` number of rings which is always added around identified conflicting triangles  
> `max_ring <- int` number of rings on which the smoothing process will stop. Conflicts are unlikely to be resolved further  
> `process <- dict` parameters dictating what metrics should be used in the smoothing routine (see process)  
> `densification_process <- dict` parameters dictating what metrics should be used in the densification routine (see densification_process)  
> `..._threshold <- float` threshold for ...  
> `..._threshold <- float` threshold for ...  
> `..._threshold <- float` threshold for ...  
> `..._threshold <- float` threshold for ...  
> `..._threshold <- float` threshold for ...  

##### `paramDict['process'] <- list`
Parameters dictating what metrics should be used in the smoothing routine.  
It must be a list with possible entries: `['angularity', 0], ['spurs', 0], ['gullys', 0]`. The second entry of each entry is deprecated, but may be activated manually.

##### `paramDict['densification_process'] <- list`
Parameters dictating what metrics should be used in the densification routine.  
It must be a list with possible entries: `['angularity', 'r', 0], ['aspect-edges', 'r', 0], ['size-edges', 'r', 0]`. The second entry in each entry (`'r'`) dictates how each identified conflicting triangle should be extended, and the third entry (`0`) dictates the amount of extension.

---

## Variables

#### `prepass`

## Attributes


# Examples

## hydroshortcut.py
 **Starting a project:**
 - Possibly need to create a directory `projects`
 - First initiate a new project with .init()
 - Directly load a pointfile with .load_pointfile()

```python
projectObject.init_project(projectName)
projectObject.load_pointfile(surveyData, 'csv', ' ', flip=True)
```

**Loading existing project:**
 - Make sure to comment out the initiation step
 - Load the project with .load_project()

``` python
projectObject.load_project(projectName)
```

**Saving a project**

``` python
if projectObject.vertexCount:
  projectObject.save_triangulation()
if projectObject.nrNodes:
  projectObject.save_trGraph()
```

**Triangle Region Graph**
```python
# adds every triangle to one or more regions which it belongs to
projectObject.generate_regions()
# builds the actual graph
projectObject.build_graph2()
# creates a pdf with a visualisation of the graph
projectObject.make_network_graph()
```

**Exporting to shapefiles**
``` python
# export all nodes in groups of triangles, with neighboring nodes etc.
projectObject.export_all_node_triangles()
# export only the edge-triangles, with its value
projectObject.export_all_edge_triangles()
# export all vertices and triangles
projectObject.export_shapefile('output')
```
**Isobaths**
```python
# generates lines through the edge-triangles
projectObject.generate_isobaths4()
# exports the lines to shapefile
projectObject.export_all_isobaths()

# isobaths should have been generated before this to work
# check the angularities in each isobath /
# if edgeIds is empty, all edges are handled
# threshold in radians determines which points are returned
sharpPoints = projectObject.check_isobath_angularity(edgeIds=[], threshold=0.6)
# export points with their angularity-unit
projectObject.export_all_angularities()
```

**Smoothing**
```python
# first define which vertices needs to be smoothened e.g.
sharpPoints = projectObject.check_isobath_angularity(edgeIds=[], threshold=0.6)
nodePoints = projectObject.get_vertices_from_node(nodeId)

verticesToSmooth = set()
# increase the numer of vertices by expanding to its neighbors
# rings define how many triangle-rings around the sharpPoint will be added
for point in sharpPoints:
    verticesToSmooth.update(projectObject.get_vertices_around_point(point, rings=1))
print('nr vertices: ', len(verticesToSmooth))

# smooth the indexed vertices and rebuild the entire graph
# within Hydropolator.simple_smooth_and_rebuild() an iteration-count is hard-coded
# this iteration-count smooths the given vertices only by a certain amount
projectObject.simple_smooth_and_rebuild(verticesToSmooth)

# now export all information of interest again for comparison
# isobaths have to be generated again as well
```

## hydrolauncher.py
This script can be used to interact with the projects in a terminal window. It is not fully functional yet, mainly used for quick experiments but has some more functionality than the hydroshortcut.py described above.
