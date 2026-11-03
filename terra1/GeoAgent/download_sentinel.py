
import planetary_computer
from pystac_client import Client
import rasterio
from rasterio.windows import from_bounds
from rasterio.warp import transform_bounds
import matplotlib.pyplot as plt

catalog = Client.open(
    "https://planetarycomputer.microsoft.com/api/stac/v1",
    modifier=planetary_computer.sign_inplace
)

search = catalog.search(
    collections=["sentinel-2-l2a"],
    bbox=[77.45, 12.90, 77.70, 13.10],
    datetime="2025-01-01/2025-12-31",
    query={"eo:cloud_cover": {"lt": 20}}
)

items = sorted(
    search.items(),
    key=lambda x: x.properties.get("eo:cloud_cover", 100)
)

if not items:
    raise RuntimeError("No Sentinel-2 scenes found")

scene = items[0]
print("Selected scene:", scene.id)
print("Date:", scene.datetime)

asset = scene.assets["visual"]
url = asset.href

with rasterio.open(url) as src:
    bounds = transform_bounds(
        "EPSG:4326",
        src.crs,
        77.45, 12.90, 77.70, 13.10
    )

    window = from_bounds(*bounds, transform=src.transform)
    image = src.read(
        [1, 2, 3],
        window=window,
        out_shape=(3, 800, 800)
    )

    image = image.transpose(1, 2, 0)

plt.figure(figsize=(10, 10))
plt.imshow(image)
plt.title(f"Sentinel-2: {scene.datetime.date()}")
plt.axis("off")
plt.tight_layout()
plt.savefig("sentinel_bengaluru.png", dpi=150)
plt.show()

print("Satellite image saved as sentinel_bengaluru.png")
