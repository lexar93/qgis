Municipios = QgsVectorLayer('/home/alex/Documents/gis/divisions administratives/Municipios.gpkg', 'Municipios', 'ogr')
QgsProject.instance().addMapLayer(Municipios)

query = f'"COMARCA"=\'Vallès Oriental\''
Municipios.setSubsetString(query)

nameunit_field_index = Municipios.fields().indexFromName("NAMEUNIT")

# Get a list of unique values in the "NAMEUNIT" column
nameunit_values = Municipios.dataProvider().uniqueValues(nameunit_field_index)

for i in nameunit_values:
    print(i)