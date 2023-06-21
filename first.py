# Import required modules

import qgis
from qgis.core import QgsProject
from qgis.core import QgsRasterLayer
import processing


Municipio = "Bagà"
path_to_gpkg = '/home/alex/Documents/gis/divisions administratives/Municipios.gpkg'
layer_name = 'Municipios'
municipios = QgsVectorLayer(f'{path_to_gpkg}|layername={layer_name}', layer_name, 'ogr')
# Add the layer to the map.
QgsProject.instance().addMapLayer(municipios)

query = f'"NAMEUNIT"=\'{Municipio}\''
municipios.setSubsetString(query)


# Define the XYZ tile layer URL
url = "https://mt1.google.com/vt/lyrs%3Dr%26x%3D%7Bx%7D%26y%3D%7By%7D%26z%3D%7Bz%7D&zmax=18&zmin=0"

# Create the layer object
Gmaps = QgsRasterLayer("type=xyz&url=" + url, 'Google Maps', "wms")

crs = QgsCoordinateReferenceSystem('EPSG:3857')
Gmaps.setCrs(crs)
# Add the layer to the project
QgsProject.instance().addMapLayer(Gmaps)

# Run the native:rasterize algorithm
xmin, ymin, xmax, ymax = municipios.extent().toRectF().getCoords()
output_extent = f"{xmin},{xmax},{ymin},{ymax}[EPSG:4326]"

params = {
    'EXTENT': output_extent,
    'EXTENT_BUFFER': 0,
    'LAYERS': Gmaps,
    'MAKE_BACKGROUND_TRANSPARENT': False,
    'MAP_THEME': None,
    'MAP_UNITS_PER_PIXEL': 2,
    'OUTPUT': 'TEMPORARY_OUTPUT',
    'TILE_SIZE': 1024
}

result = processing.run("native:rasterize", params)

# Load the output raster layer as a temporary layer
output_layer = QgsRasterLayer(result["OUTPUT"], "Output Layer")
QgsProject.instance().addMapLayer(output_layer, True)

# Get the current map canvas
canvas = iface.mapCanvas()

# Add the output raster layer to the canvas
canvas.setLayers([output_layer,municipios])

# Zoom to the extent of the output raster layer
canvas.setExtent(output_layer.extent())

# Refresh the canvas to show the new layer
canvas.refresh()

params = { 'ALPHA_BAND' : False,
'CROP_TO_CUTLINE' : True,
'DATA_TYPE' : 0,
'EXTRA' : '',
'INPUT' : output_layer,
'KEEP_RESOLUTION' : False,
'MASK' : municipios,
'MULTITHREADING' : False,
'NODATA' : None,
'OPTIONS' : '',
'OUTPUT' : 'TEMPORARY_OUTPUT',
'SET_RESOLUTION' : False,
'SOURCE_CRS' : None,
'TARGET_CRS' : None,
'X_RESOLUTION' : None,
'Y_RESOLUTION' : None }


result = processing.run('gdal:cliprasterbymasklayer', params)

# Load the output raster layer as a temporary layer
Clipped = QgsRasterLayer(result['OUTPUT'], 'Clipped Raster Layer')
QgsProject.instance().addMapLayer(Clipped)

# Zoom to the extent of the clipped raster layer
canvas = iface.mapCanvas()
canvas.setExtent(Clipped.extent())
canvas.refresh()


expression = '"Clipped Raster Layer@1" = 254 AND "Clipped Raster Layer@2" = 249 AND "Clipped Raster Layer@3" = 232'

paramsc = {
    'EXPRESSION': expression,
    'LAYERS':Clipped,
    'OUTPUT': 'TEMPORARY_OUTPUT'
}

calculated = processing.run('qgis:rastercalculator', paramsc)

Calculated = QgsRasterLayer(calculated['OUTPUT'], 'calculated')

QgsProject.instance().addMapLayer(Calculated)

params2= { 'BAND' : 1,
'EIGHT_CONNECTEDNESS' : False,
'EXTRA' : '', 'FIELD' : 'DN',
'INPUT' : Calculated,
'OUTPUT' : 'TEMPORARY_OUTPUT' }

vectorized = processing.run("gdal:polygonize", params2)

Vector = QgsVectorLayer(vectorized['OUTPUT'],"vectorized")

QgsProject.instance().addMapLayer(Vector)

canvas = iface.mapCanvas()
canvas.setExtent(Vector.extent())
canvas.refresh()

query2 = '"DN"=1'
Vector.setSubsetString(query2)


params3 = {'DISSOLVE' : True,
'DISTANCE' : 50,
'END_CAP_STYLE' : 0,
'INPUT' : Vector,
'JOIN_STYLE' : 0,
'MITER_LIMIT' : 2,
'OUTPUT' : 'TEMPORARY_OUTPUT',
'SEGMENTS' : 5
}

buffer1 = processing.run("gdal:buffervectors", params3)
buffer1 = QgsVectorLayer(buffer1['OUTPUT'],"Buffer1")
QgsProject.instance().addMapLayer(buffer1)

params4 = {'DISSOLVE' : True,
'DISTANCE' : -50,
'END_CAP_STYLE' : 0,
'INPUT' : buffer1,
'JOIN_STYLE' : 0,
'MITER_LIMIT' : 2,
'OUTPUT' : 'TEMPORARY_OUTPUT',
'SEGMENTS' : 5
}

buffer2 = processing.run("gdal:buffervectors", params4)
buffer2 = QgsVectorLayer(buffer2['OUTPUT'],"Buffer2")
QgsProject.instance().addMapLayer(buffer2)


# Run the simplify geometries algorithm
params = { 'INPUT' : buffer2, 'METHOD' : 0, 'OUTPUT' : 'TEMPORARY_OUTPUT2', 'TOLERANCE' : 5 }
result = processing.run("native:simplifygeometries", params)

# Get the output file path and create a QgsVectorLayer object
output_path = result['OUTPUT']
simple_layer = QgsVectorLayer(output_path, 'Simplified', 'ogr')
QgsProject.instance().addMapLayer(simple_layer)


