import os
from qgis.core import QgsApplication, QgsProject, QgsRasterLayer, QgsVectorLayer, QgsCoordinateReferenceSystem
from qgis import processing

os.environ['LD_LIBRARY_PATH'] = '/usr/lib/qgis:/usr/share/qgis/lib:' + os.environ.get('LD_LIBRARY_PATH', '')
os.environ['QGIS_PREFIX_PATH'] = '/usr'

# Set the prefix path of your QGIS installation
QgsApplication.setPrefixPath('/usr/bin/qgis.bin', True)

# Create an instance of the QgsApplication
qgs = QgsApplication([], False)
qgs.initQgis()

# Load a QGIS vector layer
Municipios = QgsVectorLayer('/home/alex/Documents/gis/divisions administratives/Municipios.gpkg', 'Municipios', 'ogr')
QgsProject.instance().addMapLayer(Municipios)

# Rest of your code...

# Clean up and exit
qgs.exitQgis()
