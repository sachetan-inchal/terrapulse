import sys
sys.path.insert(0, 'c:/Users/rishi/Desktop/CCVR/terrapulse')
from backend.main import app
from fastapi.testclient import TestClient

client = TestClient(app)

print('1. Testing chronological...')
r1 = client.get('/api/scenes/chronological?location_id=bengaluru')
print('Status:', r1.status_code, 'Count:', len(r1.json()))

print('2. Testing related...')
r2 = client.get('/api/scenes/related?location_id=bengaluru')
print('Status:', r2.status_code, 'Counts:', r2.json().get('counts'))

print('3. Testing scenes and measurements...')
scenes = client.get('/api/scenes?location_id=bengaluru').json()
s2_scene = [s for s in scenes if 'Sentinel' in s['mission']][0]
print('Selected Sentinel-2 Scene:', s2_scene['id'])

r3 = client.get(f"/api/scenes/measurements?scene_id={s2_scene['id']}")
print('Status:', r3.status_code)
meas = r3.json()
print('NDVI:', meas.get('mean_ndvi'))
print('Veg %:', meas.get('vegetation_pct'))
print('NDWI:', meas.get('mean_ndwi'))
print('Water %:', meas.get('water_pct'))
print('NDBI:', meas.get('mean_ndbi'))
print('Built-up %:', meas.get('built_up_pct'))
print('Status:', meas.get('calculation_status'))

print('4. Testing georeferenced...')
r4 = client.get(f"/api/scenes/georeferenced?scene_id={s2_scene['id']}")
print('Status:', r4.status_code, 'Content-Length:', len(r4.content), 'Content-Type:', r4.headers.get('content-type'))

print('5. Testing SPA Index...')
r5 = client.get('/')
print('SPA Status:', r5.status_code, 'Has TerraPulse bundle:', 'index-CyNH1uPm.js' in r5.text or 'assets' in r5.text)

print('6. Testing Earth Texture static asset...')
r6 = client.get('/textures/earth.jpg')
print('Texture Status:', r6.status_code, 'Texture Size:', len(r6.content))

