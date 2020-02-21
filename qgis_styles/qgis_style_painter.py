# https://gis.stackexchange.com/a/199458
from qgis.core import QgsProject, QgsSymbol, QgsRuleBasedRenderer, QgsFillSymbol
from qgis.utils import iface
from PyQt5.QtGui import QColor


def rule_based_style(layer, symbol, renderer, label, expression, color):
    root_rule = renderer.rootRule()
    rule = root_rule.children()[0].clone()
    rule.setLabel(label)
    rule.setFilterExpression(expression)
    rule.symbol().setColor(QColor(color[0], color[1], color[2], 255))
    symbolProps = rule.symbol().symbolLayer(0).properties()
    symbolProps['outline_style'] = 'no'
    rule.setSymbol(QgsFillSymbol.createSimple(symbolProps))
    root_rule.appendChild(rule)
    layer.setRenderer(renderer)
    layer.triggerRepaint()


def color_depares(layer, isoBreaks):
    # https://gis.stackexchange.com/a/282345
    # DEPARE COLORS and LIMITS
    # [land, intertidal, danger, shallow, deep]
    limits = [0, 2, 5, 8]
    limits = isoBreaks
    landLimit = [-10e9, limits[0]]
    intertidalLimit = [limits[0], limits[1]]
    dangerLimit = [limits[1], limits[2]]
    shallowLimit = [limits[2], limits[3]]
    deepLimit = [limits[3], 10e9]
    landColor = [248, 243, 161]
    intertidalColor = [187, 217, 146]
    dangerColor = [190, 229, 238]
    shallowColor = [232, 246, 249]
    deepColor = [255, 255, 255]
    #
    fullList = [[landLimit, landColor, 'land'],
                [intertidalLimit, intertidalColor, 'intertidal'],
                [dangerLimit, dangerColor, 'danger'],
                [shallowLimit, shallowColor, 'shallow'],
                [deepLimit, deepColor, 'deep']]
    fullList.reverse()
    #
    print('depare!')
    # layer = iface.activeLayer()
    symbol = QgsSymbol.defaultSymbol(layer.geometryType())
    renderer = QgsRuleBasedRenderer(symbol)
    #
    for pair in fullList:
        expression = ' if(\"dep_min\" < {}, True, None) '.format(pair[0][1])
        color = pair[1]
        label = '{} (>{})'.format(pair[2], pair[0][1])
        rule_based_style(layer, symbol, renderer, label, expression, color)
    renderer.rootRule().removeChildAt(0)
    iface.layerTreeView().refreshLayerSymbology(layer.id())


def style_painter(isoBreaks=[0, 2, 5, 10]):
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
        elif 'DEPARE' in layer.name():
            color_depares(layer, isoBreaks)
