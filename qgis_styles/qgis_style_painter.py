# https://gis.stackexchange.com/a/199458

from qgis.core import QgsProject
from qgis.utils import iface


def style_painter():
    qgis_style_files_path = '/Users/Bonny/Documents/Thesis/Hydropolator/qgis_styles/'
    style_path_isobaths = qgis_style_files_path + 'isobaths' + '.qml'
    style_path_node_triangles = qgis_style_files_path + 'node_triangles_style' + '.qml'
    style_path_edge_triangles = qgis_style_files_path + 'edge_triangles_style' + '.qml'
    style_path_angularities = qgis_style_files_path + 'angularities' + '.qml'
    print(style_path_isobaths)
    for layer in QgsProject.instance().mapLayers().values():
        if 'edge_triangles' in layer.name():
            layer.loadNamedStyle(style_path_edge_triangles)
            layer.triggerRepaint()
            iface.layerTreeView().refreshLayerSymbology(layer.id())
        elif 'node_triangles' in layer.name():
            layer.loadNamedStyle(style_path_node_triangles)
            layer.triggerRepaint()
            iface.layerTreeView().refreshLayerSymbology(layer.id())
        elif 'isobaths_' in layer.name():
            layer.loadNamedStyle(style_path_isobaths)
            layer.triggerRepaint()
            iface.layerTreeView().refreshLayerSymbology(layer.id())
        elif 'angularities' in layer.name():
            layer.loadNamedStyle(style_path_angularities)
            layer.triggerRepaint()
            iface.layerTreeView().refreshLayerSymbology(layer.id())
