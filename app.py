from flask import Flask, jsonify, make_response, request
from flask_cors import CORS
from shapely.ops import polygonize
from shapely.geometry import asShape
from shapely.geometry import mapping
import osm2geojson
import requests
import json

import geojson

app = Flask(__name__)
cors = CORS(app, resources={r"/*": {"origins": "*"}})



def bbox(coord_list):
    box = []
    for i in (0,1):
        res = sorted(coord_list, key=lambda x:x[i])
        box.append((res[0][i],res[-1][i]))
    ret = f"{box[0][0]},{box[1][0]},{box[0][1]},{box[1][1]}"
    return ret

def PolygonToBBox(value):
    data = value
    polygon = []
    for latLng in data:
        polygon.append((latLng['lng'], latLng['lat']))
    print()
    poly=geojson.Polygon([polygon])
    line = bbox(list(geojson.utils.coords(poly)))
    return line

def getQuadras(value):
    highway_whitelist = {'LineString'}
    streets = value
    streets['features'] = [feat for feat in streets['features'] if feat['geometry']['type'] in highway_whitelist]
    geojson = {
        "type": "FeatureCollection",
        "features": []
    }
    for feature in streets['features']:
        coords = feature['geometry']['coordinates']
        for i in range(0, len(coords) - 1):
            geojson['features'].append({
                "type": "Feature",
                "properties": feature['properties'],  # or just {}
                "geometry": {
                    "type": "LineString",
                    "coordinates": [coords[i], coords[i + 1]]
                }
        })
    lines = []
    for feature in geojson['features']:
        lines.append(asShape(feature['geometry']))
    polys = list(polygonize(lines))
    geojsonB = {
        "type": "FeatureCollection",
        "features": []
    }
    for poly in polys:
        geojsonB['features'].append({
            "type": "Feature",
            "properties": {},
            "geometry": mapping(poly)
        })
    return geojsonB

@app.route("/")
def hello_from_root():
    return jsonify(message='Hello from root!')

@app.route("/merge", methods=['POST'])
def mergPolygons():
    data = request.json
    shapes = []
    geojson = {
        "type": "FeatureCollection",
        "features": []
    }
    for item in data:
        geojson["features"].append({
      "type": "Feature",
      "properties": {},
      "geometry": item
    })
    polygon = []
    for feature in geojson['features']:
        polygon.append(asShape(feature['geometry']))
    
    i = 0
    polygonAtual = polygon[0]
    while i < len(polygon):
        polygonAtual = polygonAtual.union(polygon[i])
        i+=1
    
    print()

    return make_response(jsonify({
            "type": "Feature",
            "properties": {},
            "geometry": mapping(polygonAtual)
        }), 200)

@app.route("/osmclear")
def osmclear():
    return jsonify(0)

@app.route("/convert", methods=['POST'])
def convert():
    geojson = osm2geojson.xml2geojson(request.data, filter_used_refs=False, log_level='INFO')
    return jsonify(geojson)


@app.route("/map", methods=['POST'])
def map():
    bbox = PolygonToBBox(request.json)
    response = requests.get(f'https://overpass-api.de/api/map?bbox={bbox}')
    osm = response.text
    xmltogeojson = osm2geojson.xml2geojson(osm, filter_used_refs=False, log_level='INFO')
    quadras = getQuadras(xmltogeojson)
    #json.dump(quadras, open('gean.json', 'w'))
    return make_response(quadras)

@app.route("/convertPolygonToBBox", methods=['POST'])
def convertPolygonToBBox():
    return make_response(jsonify(bbox=PolygonToBBox(request.json)), 200)

@app.route("/overpass", methods=['POST'])
def overpass():
    response = requests.get('https://overpass-api.de/api/interpreter?data=[out:xml][timeout:25];(rel(51800););out geom;')
    string = response.text.replace("\n","")
    geojson = osm2geojson.xml2geojson(string)
    return jsonify(geojson)

@app.route("/mapping", methods=['POST'])
def mappingblock():   
    return jsonify(getQuadras(request.json))

@app.errorhandler(404)
def resource_not_found(e):
    return make_response(jsonify(error='Not found!'), 404)


if __name__ == "__main__":
    app.run(debug=True)