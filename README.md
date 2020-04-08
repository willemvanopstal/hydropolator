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

#### `prepass

## Attributes


# Interaction

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
