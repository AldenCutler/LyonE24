



import sqlite3
import geopandas as gpd
import json
from datetime import datetime
import pandas as pd
import folium
from folium.plugins import MarkerCluster
from folium.plugins import HeatMap

conn = sqlite3.connect('../itinerary-scraping/journeys.db')
cursor = conn.cursor()


cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
print(cursor.fetchall())





cursor.execute('SELECT * FROM outages')
outages = cursor.fetchall()

cursor.execute('SELECT * FROM journeys')
journeys = cursor.fetchall()

cursor.execute('SELECT * FROM stops')
stops = cursor.fetchall()

cursor.close()
conn.close()





outages_df = pd.DataFrame(outages, columns=['outage_id', 'stop_id', 'effect', 'updated_at', 'outage_data'])
stops_df = pd.DataFrame(stops, columns=['stop_id', 'stop_name', 'stop_coords', 'stop_acc'])


merged_df = pd.merge(outages_df, stops_df, on='stop_id')





tcl_metro = gpd.read_file('data/tcl_metro.json')
tcl_metro = tcl_metro.drop(columns=['date_debut', 'date_fin', 'last_update', 'last_update_fme'])




        
tcl_metro['style'] = [
    {
        "color": "black",
        "weight": 5,
        "opacity": 1
    }
    for i in range(len(tcl_metro))
]






merged_df['lon'] = merged_df['stop_coords'].apply(lambda x: x.split(',')[0][9:-1])
merged_df['lat'] = merged_df['stop_coords'].apply(lambda x: x.split(',')[1][9:-2])
merged_df = merged_df.drop(columns=['stop_coords'])


merged_df['outage_data'] = merged_df['outage_data'].apply(lambda x: json.loads(x))
merged_df['stop_acc'] = merged_df['stop_acc'].apply(lambda x: json.loads(x))
begin, end = [], []
cause, effect = [], []
for row in merged_df['outage_data']:
    
    
    
    times = row['periods']    
    begin.append(datetime.strptime(times[0]['begin'], '%Y%m%dT%H%M%S').isoformat() + '+02:00')
    end.append(datetime.strptime(times[0]['end'], '%Y%m%dT%H%M%S').isoformat() + '+02:00')
    
    
    cause.append(row['cause'])
    effect.append(row['effect'])
    
merged_df['begin'] = begin
merged_df['end'] = end
merged_df['cause'] = cause
merged_df['effect'] = effect

merged_df = merged_df.drop(columns=['outage_data'])


merged_df['effect'] = merged_df['effect'].apply(lambda x: x['label'])
merged_df['cause'] = merged_df['cause'].apply(lambda x: x['label'])
merged_df.head()



m = folium.Map(location=[45.75, 4.85], zoom_start=13, tiles='cartodb voyager')


heat_data = [[row['lat'], row['lon']] for _, row in merged_df.iterrows()]
HeatMap(heat_data).add_to(m)


marker_cluster = MarkerCluster().add_to(m)
for idx, row in merged_df.iterrows():
    tooltip = f"Stop Name: {row['stop_name']}<br>Outage ID: {row['outage_id']}<br>Start: {row['begin']}<br>End: {row['end']}<br>Cause: {row['cause']}<br>Effect: {row['effect']}"
                
    folium.Marker([row['lat'], row['lon']], tooltip=tooltip).add_to(marker_cluster)


folium.GeoJson(tcl_metro, style_function=lambda x: x['properties']['style']).add_to(m)


'''
Outage database only contains data on metro line/stop outages, so bus lines are not displayed by default.
The bus line data is still useful to see how metro lines are connected to bus lines and thus how outages on metro lines could affect bus lines.
Uncomment the following lines to display the bus lines.
'''




m.save('./data/outages_heatmap.html')



m = folium.Map(location=[45.75, 4.85], zoom_start=13, tiles='cartodb voyager')


heat_data = [[row['lat'], row['lon']] for _, row in merged_df.iterrows()]
HeatMap(heat_data).add_to(m)



                

    
folium.GeoJson(tcl_metro, style_function=lambda x: x['properties']['style']).add_to(m)
m.save('./data/outages_heatmap_no_cluster.html')



merged_df = merged_df[merged_df['effect'] != '.']
merged_df.head()



m = folium.Map(location=[45.75, 4.85], zoom_start=13, tiles='None')


heat_data = [[row['lat'], row['lon']] for _, row in merged_df.iterrows()]
HeatMap(heat_data).add_to(m)


marker_cluster = MarkerCluster().add_to(m)

for idx, row in merged_df.iterrows():
    tooltip = f"Stop Name: {row['stop_name']}<br>Outage ID: {row['outage_id']}<br>Start: {row['begin']}<br>End: {row['end']}<br>Cause: {row['cause']}<br>Effect: {row['effect']}"
                
    folium.Marker([row['lat'], row['lon']], tooltip=tooltip).add_to(marker_cluster)
    

folium.GeoJson(tcl_metro, style_function=lambda x: x['properties']['style']).add_to(m)

'''
Outage database only contains data on metro line/stop outages, so bus lines are not displayed by default.
The bus line data is still useful to see how metro lines are connected to bus lines and thus how outages on metro lines could affect bus lines.
Uncomment the following lines to display the bus lines.
'''




m.save('./out/filtered_effect_outages.html')





