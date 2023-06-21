import qgis
from qgis.core import QgsProject, QgsVectorLayer, QgsRasterLayer
import processing

def process_municipio(municipio):
    path_to_gpkg = '/home/alex/Documents/gis/divisions administratives/Municipios.gpkg'
    layer_name = 'Municipios'
    municipios = QgsVectorLayer(f'{path_to_gpkg}|layername={layer_name}', layer_name, 'ogr')
    # Add the layer to the map.
    QgsProject.instance().addMapLayer(municipios)

    query = f'"NAMEUNIT"=\'{municipio}\''
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
    canvas.setLayers([output_layer, municipios])

    # Zoom to the extent of the output raster layer
    canvas.setExtent(output_layer.extent())

    # Refresh the canvas to show the new layer
    canvas.refresh()

    params = {
        'ALPHA_BAND': False,
        'CROP_TO_CUTLINE': True,
        'DATA_TYPE': 0,
        'EXTRA': '',
        'INPUT': output_layer,
        'KEEP_RESOLUTION': False,
        'MASK': municipios,
        'MULTITHREADING': False,
        'NODATA': None,
        'OPTIONS': '',
        'OUTPUT': 'TEMPORARY_OUTPUT',
        'SET_RESOLUTION': False,
        'SOURCE_CRS': None,
        'TARGET_CRS': None,
        'X_RESOLUTION': None,
        'Y_RESOLUTION': None
    }

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
        'LAYERS': Clipped,
        'OUTPUT': 'TEMPORARY_OUTPUT'
    }

    calculated = processing.run('qgis:rastercalculator', paramsc)

    Calculated = QgsRasterLayer(calculated['OUTPUT'], 'calculated')

    QgsProject.instance().addMapLayer(Calculated)

    params2 = {
        'BAND': 1,
        'EIGHT_CONNECTEDNESS': False,
        'EXTRA': '',
        'FIELD': 'DN',
        'INPUT': Calculated,
        'OUTPUT': 'TEMPORARY_OUTPUT'
    }

    vectorized = processing.run("gdal:polygonize", params2)

    Vector = QgsVectorLayer(vectorized['OUTPUT'], "vectorized")

    QgsProject.instance().addMapLayer(Vector)

    canvas = iface.mapCanvas()
    canvas.setExtent(Vector.extent())
    canvas.refresh()

    query2 = '"DN"=1'
    Vector.setSubsetString(query2)

    params3 = {
        'DISSOLVE': True,
        'DISTANCE': 50,
        'END_CAP_STYLE': 0,
        'INPUT': Vector,
        'JOIN_STYLE': 0,
        'MITER_LIMIT': 2,
        'OUTPUT': 'TEMPORARY_OUTPUT',
        'SEGMENTS': 5
    }

    buffer1 = processing.run("gdal:buffervectors", params3)
    buffer1 = QgsVectorLayer(buffer1['OUTPUT'], "Buffer1")
    QgsProject.instance().addMapLayer(buffer1)

    params4 = {
        'DISSOLVE': True,
        'DISTANCE': -50,
        'END_CAP_STYLE': 0,
        'INPUT': buffer1,
        'JOIN_STYLE': 0,
        'MITER_LIMIT': 2,
        'OUTPUT': 'TEMPORARY_OUTPUT',
        'SEGMENTS': 5
    }

    buffer2 = processing.run("gdal:buffervectors", params4)
    buffer2 = QgsVectorLayer(buffer2['OUTPUT'], "Buffer2")
    QgsProject.instance().addMapLayer(buffer2)

    # Run the simplify geometries algorithm
    params = {
        'INPUT': buffer2,
        'METHOD': 0,
        'OUTPUT': 'TEMPORARY_OUTPUT2',
        'TOLERANCE': 5
    }
    result = processing.run("native:simplifygeometries", params)

    # Get the output file path and create a QgsVectorLayer object
    output_path = result['OUTPUT']
    simple_layer = QgsVectorLayer(output_path, 'Simplified', 'ogr')
    QgsProject.instance().addMapLayer(simple_layer)

    params6 = {
        'INPUT': simple_layer,
        'OUTPUT': 'TEMPORARY_OUTPUT6'
    }
    multi = processing.run("native:multiparttosingleparts", params6)
    output_path6 = multi['OUTPUT']
    multi_layer = QgsVectorLayer(output_path6, 'Multi', 'ogr')
    
    
    # Remove the DN column from the multi_layer
    dn_field_index = multi_layer.fields().indexFromName('DN')
    multi_layer.dataProvider().deleteAttributes([dn_field_index])
    multi_layer.updateFields()
# Add an index column with the municipio name and row number
    index_expression = f'{municipio}_$rownum'
    multi_layer.dataProvider().addAttributes([QgsField('index', QVariant.String)])
    multi_layer.updateFields()

    index_field_index = multi_layer.fields().indexFromName('index')
    multi_layer.startEditing()
    for i, feature in enumerate(multi_layer.getFeatures()):
        index_value = index_expression.replace('$rownum', str(i + 1))
        multi_layer.changeAttributeValue(feature.id(), index_field_index, index_value)
    multi_layer.commitChanges()
    
    
    # Add a municipio column
    municipio_field_name = 'municipio'
    municipio_field_type = QVariant.String

    # Check if the field already exists, if not, add it
    if municipio_field_name not in multi_layer.fields().names():
        multi_layer.startEditing()
        multi_layer.dataProvider().addAttributes([QgsField(municipio_field_name, municipio_field_type)])
        multi_layer.updateFields()
        multi_layer.commitChanges()

    # Get the index of the municipio field
    municipio_field_index = multi_layer.fields().indexFromName(municipio_field_name)

    # Update the municipio field with the municipio variable value
    multi_layer.startEditing()
    for feature in multi_layer.getFeatures():
        municipio_value = f'{municipio}'
        multi_layer.changeAttributeValue(feature.id(), municipio_field_index, municipio_value)
    multi_layer.commitChanges()
    
    QgsProject.instance().addMapLayer(multi_layer)
    
    
    
    
    
    # Add a column for the area
    area_field_name = 'area'
    area_field_type = QVariant.Double

    # Check if the field already exists, if not, add it
    if area_field_name not in multi_layer.fields().names():
        multi_layer.startEditing()
        multi_layer.dataProvider().addAttributes([QgsField(area_field_name, area_field_type)])
        multi_layer.updateFields()
        multi_layer.commitChanges()

    # Get the index of the area field
    area_field_index = multi_layer.fields().indexFromName(area_field_name)

    # Calculate and update the area for each feature
    multi_layer.startEditing()
    for feature in multi_layer.getFeatures():
        area_value = feature.geometry().area()
        multi_layer.changeAttributeValue(feature.id(), area_field_index, area_value)
    multi_layer.commitChanges()
    
    # Define the output file path
    output_path = '/home/alex/Documents/gis/aoi_mun/' + municipio + '.gpkg'

    # Save the layer to GeoPackage
    options = QgsVectorFileWriter.SaveVectorOptions()
    options.driverName = 'GPKG'
    options.layerName = municipio
    QgsVectorFileWriter.writeAsVectorFormatV2(multi_layer, output_path, QgsCoordinateTransformContext(), options)


    project = QgsProject.instance()
    project.removeAllMapLayers()
# Call the function with a municipality name

municipio = "Bagà"
process_municipio(municipio)
