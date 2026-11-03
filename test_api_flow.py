import requests
import json

BASE = 'http://127.0.0.1:8000'

# 1. Search Bengaluru
loc_res = requests.get(f'{BASE}/api/locations/search?q=Bengaluru').json()
print('=== 1. Location Search Bengaluru ===')
print('Name:', loc_res[0]['name'])
print('BBox:', loc_res[0]['bbox'])

# 2. Retrieve actual Sentinel-2 scenes
scenes = requests.get(f'{BASE}/api/scenes?location_id=bengaluru').json()
print('\n=== 2. Retrieved Actual STAC Scenes ===')
print(f'Total scenes returned: {len(scenes)}')
s2_scenes = [s for s in scenes if 'Sentinel' in s['mission']]
print(f'Sentinel-2 scenes: {len(s2_scenes)}')
print('First 3 scenes:')
for s in scenes[:3]:
    print(f' - ID: {s["id"]}')
    print(f'   Mission: {s["mission"]}, Date: {s["acquisition_date"]}, Cloud: {s["cloud_cover"]}%, Res: {s["spatial_resolution_m"]}m')
    print(f'   Thumbnail: {s["thumbnail_url"][:90]}...')
    print(f'   Footprint present: {s.get("footprint") is not None}')

# 3. Retrieve Chronological Timeline
chrono = requests.get(f'{BASE}/api/scenes/chronological?location_id=bengaluru').json()
print('\n=== 3. Chronological Timeline Scenes ===')
print(f'Total timeline items: {len(chrono)}')
print('Earliest:', chrono[0]['mission'], chrono[0]['acquisition_date'])
print('Latest:', chrono[-1]['mission'], chrono[-1]['acquisition_date'])

# 4. Related imagery counts and groups
related = requests.get(f'{BASE}/api/scenes/related?location_id=bengaluru').json()
print('\n=== 4. Dynamic Related Imagery ===')
print('Counts:', related['counts'])
print('Asset counts:', related['asset_counts'])
for g in related['groups']:
    print(f' - Group "{g["title"]}": {len(g["items"])} items')

# 5. Calculate real NDVI & measurements on top scene
top_scene_id = s2_scenes[0]['id']
print(f'\n=== 5. Real Environmental Analysis for {top_scene_id} ===')
meas = requests.get(f'{BASE}/api/scenes/measurements?scene_id={top_scene_id}').json()
print(json.dumps(meas, indent=2))

# 6. Georeferenced image overlay
georef = requests.get(f'{BASE}/api/scenes/georeferenced?scene_id={top_scene_id}')
print(f'\n=== 6. Georeferenced Image ===')
print(f'Status: {georef.status_code}, Content-Type: {georef.headers.get("content-type")}, Size: {len(georef.content)} bytes')

