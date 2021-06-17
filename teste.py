from shapely.ops import polygonize
from shapely.geometry import asShape
from shapely.geometry import mapping
import osm2geojson
import json

if __name__ == '__main__':
    #xmltogeojson = osm2geojson.xml2geojson("", filter_used_refs=False, log_level='INFO')
    #quadras = getQuadras(xmltogeojson)
    json.dump('teste', open('retorno.json', 'w'))