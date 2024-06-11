import json
import requests
import random
import time
import zipfile
import os
import sqlite3

# Function to process the journey data
def process_journey(data):
    stops = []
    for section in data.get('sections', []):
        if section.get('type') == 'public_transport':
            stops.append({
                "stop_point": section['from']['stop_point']['name'],
                "arrival_date_time": section['departure_date_time'],
                "departure_date_time": section['arrival_date_time']
            })
            stops.append({
                "stop_point": section['to']['stop_point']['name'],
                "arrival_date_time": section['arrival_date_time'],
                "departure_date_time": None
            })
    simplified_journey = {
        "total_duration": data.get("duration"),
        "departure_date_time": data.get("departure_date_time"),
        "arrival_date_time": data.get("arrival_date_time"),
        "co2_emission": data.get("co2_emission"),
        "air_pollutants": data.get("air_pollutants"),
        "durations": data.get("durations"),
        "distances": data.get("distances"),
        "stops": stops
    }
    return simplified_journey

# Function to extract non-journey-specific data
def extract_stops_data(data):
    stops_info = {}
    outages_info = {}
    for section in data.get('sections', []):
        stop_points = [section.get('from', {}).get('stop_point'), section.get('to', {}).get('stop_point')]
        for stop_point in stop_points:
            if not stop_point:
                continue
            stop_id = stop_point['id']
            if not stop_id in stops_info:
                stops_info[stop_id] = {
                    "id": stop_point.get("id"),
                    "name": stop_point.get("name"),
                    "coord": stop_point.get("coord"),
                    "equipments": stop_point.get("equipments"),
                }
                outage = stop_point.get("equipment_details")
                if outage:
                    outage = outage[0]
                    outage['stop_id'] = stop_id  # Ensure 'stop_id' is added to the outage data
                    if not outage['id'] in outages_info:
                        outages_info[outage['id']] = {
                            "id": outage['id'],
                            "stop_id": stop_id,
                            "status": outage['current_availability']['status'],
                            "updated_at": outage['current_availability']['updated_at'],
                            "info": {
                                "cause": outage['current_availability']['cause'],
                                "effect": outage['current_availability']['effect'],
                                "periods": outage['current_availability']['periods']
                            }
                        }
    return stops_info, outages_info

def get_itinerary(start_loc="4.8838;45.7475", end_loc="4.8852;45.7581", modes_transit="departure,metro,funiculaire,tramway,bus"):
    url = "https://carte.tcl.fr/api/itinerary"
    params = {
        "datetime": "now",
        "from": start_loc,
        "to": end_loc,
        "params": modes_transit,
        "walking": "0.5",
    }
    headers = {
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "en-US,en;q=0.9",
        "Cookie": "hasAuthorizedCookies=true",
        "Referer": "https://carte.tcl.fr/route-calculation?from=4.8838;45.7475&to=4.8852;45.7581",
        "sec-ch-ua": '"Chromium";v="124", "Google Chrome";v="124", "Not-A.Brand";v="99"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    }
    response = requests.get(url, headers=headers, params=params, timeout=600)
    return response.text

def generate_random_coordinates():
    min_lat, max_lat = 45.8092, 45.7155
    min_lon, max_lon = 4.7951, 4.9200
    lat = random.uniform(min_lat, max_lat)
    lon = random.uniform(min_lon, max_lon)
    return f"{round(lon, 4)};{round(lat, 4)}"

def add_raw_to_zip_and_rm(source, zipdest="raw.zip"):
    with zipfile.ZipFile(zipdest, "a", compression=zipfile.ZIP_DEFLATED) as zipf:
        dest_filename = os.path.basename(source)
        zipf.write(source, dest_filename)
    os.remove(source)

def create_db():
    conn = sqlite3.connect('journeys.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS journeys (
                    id INTEGER PRIMARY KEY,
                    total_duration INTEGER,
                    departure_date_time TEXT,
                    arrival_date_time TEXT,
                    co2_emission REAL,
                    air_pollutants TEXT,
                    durations TEXT,
                    distances TEXT,
                    stops TEXT
                )''')
    c.execute('''CREATE TABLE IF NOT EXISTS stops (
                    id TEXT PRIMARY KEY,
                    name TEXT,
                    coord TEXT,
                    equipments TEXT
                )''')
    c.execute('''CREATE TABLE IF NOT EXISTS outages (
                    id TEXT PRIMARY KEY,
                    stop_id TEXT,
                    status TEXT,
                    updated_at TEXT,
                    info TEXT
                )''')
    conn.commit()
    conn.close()

def save_journey_to_db(journey):
    conn = sqlite3.connect('journeys.db')
    c = conn.cursor()
    stops_str = json.dumps(journey['stops'])
    c.execute('''INSERT INTO journeys (total_duration, departure_date_time, arrival_date_time, co2_emission, air_pollutants, durations, distances, stops)
                 VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
              (journey['total_duration'], journey['departure_date_time'], journey['arrival_date_time'], json.dumps(journey['co2_emission']), json.dumps(journey['air_pollutants']), json.dumps(journey['durations']), json.dumps(journey['distances']), stops_str))
    conn.commit()
    conn.close()

def save_stop_to_db(stop):
    conn = sqlite3.connect('journeys.db')
    c = conn.cursor()
    c.execute('''INSERT OR IGNORE INTO stops (id, name, coord, equipments)
                 VALUES (?, ?, ?, ?)''',
              (stop['id'], stop['name'], json.dumps(stop['coord']), json.dumps(stop['equipments'])))
    conn.commit()
    conn.close()

def save_outage_to_db(outage):
    conn = sqlite3.connect('journeys.db')
    c = conn.cursor()
    c.execute('''INSERT OR IGNORE INTO outages (id, stop_id, status, updated_at, info)
                 VALUES (?, ?, ?, ?, ?)''',
              (outage['id'], outage['stop_id'], outage['status'], outage['updated_at'], json.dumps(outage['info'])))
    conn.commit()
    conn.close()

def journey_exists(journey):
    conn = sqlite3.connect('journeys.db')
    c = conn.cursor()
    stops_str = json.dumps(journey['stops'])
    c.execute('''SELECT id FROM journeys WHERE stops = ?''', (stops_str,))
    exists = c.fetchone() is not None
    conn.close()
    return exists

create_db()

while True:
    start = generate_random_coordinates()
    end = generate_random_coordinates()

    itin = get_itinerary(start_loc=start, end_loc=end)
    time_create = round(time.time())
    folder = f'responses/{time_create}'
    os.makedirs(folder)
    with open(f'{folder}/{time_create}_raw.json', 'w+') as f:
        f.write(itin)
    add_raw_to_zip_and_rm(f'{folder}/{time_create}_raw.json')
    itin = json.loads(itin)
    
    if 'message' in itin.keys():
        time.sleep(3)
        continue
    
    for journey in itin['journeys']:
        simplified = process_journey(journey)
        if not journey_exists(simplified):
            save_journey_to_db(simplified)
        
        stops, outages = extract_stops_data(journey)
        
        for stop_id, stop in stops.items():
            save_stop_to_db(stop)
        
        for outage_id, outage in outages.items():
            save_outage_to_db(outage)
    print(f"Got {len(itin['journeys'])} journeys!")

    time.sleep(random.randint(5, 15))
