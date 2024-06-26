import geopandas as gpd
import folium
from folium.plugins import HeatMap
import os
import requests
import json
import numpy as np
import pandas as pd
import math
from scipy.spatial import KDTree

def generate_building_heatmap(percentile_distances=99, residential=True, show_arrondissements=True, show_metro_lines=False, show_bus_lines=False, show_tram_lines=False, show_funicular_lines=False, export_csv=False, show_stops=False, filename='lyon_stops_distance_heatmap_no_markers.html', show_iris=False):
    # Load GeoJSON data
    if show_arrondissements:
        print("Using Arrondissements Regions")
        arrondissements = gpd.read_file('data/arrondissements-lyon.geojson')
        
    if show_iris:
        print("Using IRIS Regions")
        arrondissements = gpd.read_file('data/IRIS.geojson')
        
    stops = gpd.read_file('data/stops.geojson')

    # Ensure both GeoDataFrames have the same CRS
    arrondissements = arrondissements.to_crs(stops.crs)

    # Perform a spatial join to filter stops within arrondissements
    stops_within_arrondissements = gpd.sjoin(stops, arrondissements, how='inner', op='within')

    # Extract coordinates for the heatmap
    heatmap_data = [[point.y, point.x] for point in stops_within_arrondissements.geometry]

    # Define the bounding box for the Lyon Metropolis
    minx, miny, maxx, maxy = arrondissements.total_bounds
    
    # Overpass API query for Lyon, France
    overpass_url = "http://overpass-api.de/api/interpreter"
    if residential:
        overpass_query = f"""
        [out:json];
        (
        way["building"="residential"]({miny},{minx},{maxy},{maxx});
        way["building"="apartments"]({miny},{minx},{maxy},{maxx});
        way["building"="house"]({miny},{minx},{maxy},{maxx});
        way["building"="detached"]({miny},{minx},{maxy},{maxx});
        way["building"="terrace"]({miny},{minx},{maxy},{maxx});
        way["building"="semidetached_house"]({miny},{minx},{maxy},{maxx});
        way["building"="bungalow"]({miny},{minx},{maxy},{maxx});
        way["building"="static_caravan"]({miny},{minx},{maxy},{maxx});
        );
        out body;
        >;
        out skel qt;
        """
    else:
        overpass_query = f"""
        [out:json];
        (
        way["building"]({miny},{minx},{maxy},{maxx});

        );
        out body;
        >;
        out skel qt;
        """
        

    # Fetch data from Overpass API
    response = requests.get(overpass_url, params={'data': overpass_query})
    data = response.json()


    buildings_coords = []

    for element in data['elements']:
        if element['type'] == "node":
            buildings_coords.append([element['lat'], element['lon'], -1, ''])

    # Convert buildings_coords to a GeoDataFrame
    buildings_gdf = gpd.GeoDataFrame(
        buildings_coords,
        columns=['lat', 'lon', 'distance', 'nearest_station'],
        geometry=gpd.points_from_xy([coord[1] for coord in buildings_coords], [coord[0] for coord in buildings_coords]),
        crs=arrondissements.crs
    )

    # Perform a spatial join to filter buildings within arrondissements
    buildings_within_arrondissements = gpd.sjoin(buildings_gdf, arrondissements, how='inner', op='within')

    # Get list of station coords and names
    station_coords = []
    station_names = []
    stops_json = json.loads(open('data/stops.geojson', 'r').read())

    for stop in stops_json['features']:
        station_coords.append(stop['geometry']['coordinates'])
        station_names.append(stop['properties']['name'])

    print(f"Got {len(buildings_coords)} buildings and {len(station_coords)} stops")

    def haversine(lat1, lon1, lat2, lon2):
        R = 6371000  # radius of Earth in meters
        phi1 = math.radians(lat1)
        phi2 = math.radians(lat2)
        delta_phi = math.radians(lat2 - lat1)
        delta_lambda = math.radians(lon2 - lon1)
        a = math.sin(delta_phi / 2.0) ** 2 + \
            math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        meters = R * c  # output distance in meters
        return meters

    def compute_closest_stations(buildings_coords, station_coords, station_names):
        # Convert station coordinates to a numpy array for KDTree
        station_coords_np = np.array(station_coords)
        
        # Create KDTree for station coordinates
        station_tree = KDTree(station_coords_np)
        i = 0
        for building in buildings_coords:
            i+=1
            if i % 50000 == 0:
                print(f"{round(i/len(buildings_coords)*100)}% of distances computed..")
            building_lat, building_lon = building[:2]
            distance, index = station_tree.query([building_lon, building_lat])
            closest_station = station_coords_np[index]
            distance = haversine(building_lat, building_lon, closest_station[1], closest_station[0])
            building[2] = distance
            building[3] = station_names[index]
        
        return buildings_coords

    buildings_within_arrondissements = compute_closest_stations(
        buildings_within_arrondissements[['lat', 'lon', 'distance', 'nearest_station']].values.tolist(),
        station_coords,
        station_names
    )

    # Filter out the lowest N% of distance points
    distances = [building[2] for building in buildings_within_arrondissements]
    threshold = np.percentile(distances, percentile_distances)
    print(f"Showing buildings over {threshold} meters from closest station.")
    filtered_buildings_coords = [building for building in buildings_within_arrondissements if building[2] > threshold]
    print(len(filtered_buildings_coords))
    # Create the base map centered on Lyon
    m = folium.Map(location=[(miny + maxy) / 2, (minx + maxx) / 2], zoom_start=11)




    # Metro line vis
    tcl_metro = gpd.read_file('data/tcl_metro.json')
    tcl_metro = tcl_metro.drop(columns=['date_debut', 'date_fin', 'last_update', 'last_update_fme'])
    colors = []
    for index, row in tcl_metro.iterrows():
        if row['ligne'] == 'D': # green line
            colors.append('#029C41')
        elif row['ligne'] == 'A':   # pink line
            colors.append('#E62E86')
        elif row['ligne'] == 'B':   # blue line
            colors.append('#0065B1')
        elif row['ligne'] == 'C':   # yellow line
            colors.append('#F48E06')
        else:   # furnicular line, light green
            colors.append("#93BF38")
            
    tcl_metro['style'] = [
        {
            "color": colors[i],
            "weight": 4,
            "opacity": 1
        }
        for i in range(len(tcl_metro))
    ]


    if show_metro_lines:
        folium.GeoJson(tcl_metro, style_function=lambda x: x['properties']['style']).add_to(m)

    # bus line vis
    tcl_bus = gpd.read_file('data/tcl_bus.json')
    tcl_bus = tcl_bus.drop(columns=['date_debut', 'date_fin', 'last_update', 'last_update_fme'])

    bus_style = {
            "color": 'grey',
            "weight": 2,
            "opacity": 0.25 }

    if show_bus_lines:
        folium.GeoJson(tcl_bus, style=bus_style).add_to(m)

    if show_arrondissements:
        # Add the regions to the map with the style column
        arrondissements['style'] = [{
            "fillColor": 'black',  # color for the region
            "color": "black",
            "weight": 2,
            "fillOpacity": 0  # opacity for the region
        } for _ in range(len(arrondissements))]

        folium.GeoJson(
            arrondissements,
            name='geojson',
            style_function=lambda x: x['properties']['style'],
            tooltip=folium.GeoJsonTooltip(fields=[], aliases=[])
        ).add_to(m)

    # Add the filtered heatmap to the map
    HeatMap([[building[0], building[1], building[2]] for building in filtered_buildings_coords]).add_to(m)

    if show_stops:
        stops_within_arrondissements = gpd.sjoin(stops, arrondissements, how='inner', op='within')
        for idx, row in stops_within_arrondissements.iterrows():
            folium.RegularPolygonMarker(
                location=[row.geometry.y, row.geometry.x],
                color='purple',
                num_sides=3,
                radius=2
            ).add_to(m)

    # Save the map
    m.save(f'out/{filename}')




    if export_csv:
        # Create a DataFrame from the buildings_within_arrondissements list
        buildings_df = pd.DataFrame(buildings_within_arrondissements, columns=['lat', 'long', 'distance', 'nearest_station'])

        # Save to CSV
        buildings_df.to_csv('out/building_distances_greater_lyon_region_all_buildings.csv', index=False)


if __name__ == "__main__":
    percentile_distances=99
    residential=False
    show_arrondissements=False
    show_metro_lines=False
    show_bus_lines=False
    show_tram_lines=False
    show_funicular_lines=False
    export_csv=True
    show_stops=True
    show_iris=True
    filename='lyon_stops_distance_region_all_buildings_heatmap.html'
    generate_building_heatmap(percentile_distances=percentile_distances, residential=residential, show_arrondissements=show_arrondissements, show_metro_lines=show_metro_lines, show_bus_lines=show_bus_lines, show_tram_lines=show_tram_lines, show_funicular_lines=show_funicular_lines, export_csv=export_csv, show_stops=show_stops, filename=filename, show_iris=show_iris)