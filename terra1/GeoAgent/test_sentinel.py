
import planetary_computer
from pystac_client import Client

print("Connecting to Microsoft Planetary Computer...")

catalog = Client.open(
    "https://planetarycomputer.microsoft.com/api/stac/v1",
    modifier=planetary_computer.sign_inplace
)

print("Connected successfully!")

search = catalog.search(
    collections=["sentinel-2-l2a"],
    bbox=[77.45, 12.90, 77.70, 13.10],
    datetime="2025-01-01/2025-12-31",
    query={"eo:cloud_cover": {"lt": 20}}
)

items = list(search.items())

print("\nTotal Sentinel-2 scenes found:", len(items))

for item in items[:5]:
    print("\nScene ID:", item.id)
    print("Date:", item.datetime)
    print("Cloud cover:", item.properties.get("eo:cloud_cover"), "%")
