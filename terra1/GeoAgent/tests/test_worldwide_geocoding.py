import sys
import requests
import json

sys.stdout.reconfigure(encoding='utf-8')

test_queries = [
    'Washington DC',
    'Tokyo',
    'London',
    'New York',
    'Amazon Rainforest',
    'Lake Victoria',
    'River Thames',
    'Bellandur Lake',
    'Varthur Lake',
    'Mount Everest',
    'Great Barrier Reef',
    'Black Forest',
    '40.7128, -74.0060',
    '-3.4653, -62.2159'
]

print("=== Testing Live /api/locations/search Worldwide API ===")
for q in test_queries:
    try:
        res = requests.get('http://127.0.0.1:8000/api/locations/search', params={'q': q, 'limit': 3}, timeout=10)
        data = res.json()
        print(f"\n[QUERY] '{q}' -> {len(data)} results returned (Status {res.status_code}):")
        if not data:
            print("   (No results)")
        for item in data[:2]:
            print(f"   • Name: {item['name']}")
            print(f"     Lat: {item['latitude']}, Lon: {item['longitude']} | Category: {item.get('feature_type')} | BBox: {item['bbox']} | UTM: {item['target_utm']}")
    except Exception as e:
        print(f"   Error querying '{q}': {e}")

