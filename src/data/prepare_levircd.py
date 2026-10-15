"""Tile LEVIR-CD 1024x1024 pairs into smaller patches and split train/test.

The dashboard's bundled demo pair is also copied out here for offline use.

Run: python -m src.data.prepare_levircd
"""
import json
import random
from pathlib import Path

import numpy as np
from PIL import Image

DATA_ROOT = Path(__file__).resolve().parents[2] / "data" / "levircd"
SRC_DIR = DATA_ROOT / "val_extracted"
TILE_SIZE = 256
SEED = 42
TEST_FRACTION = 0.2


def tile_image(img: Image.Image, tile_size: int):
    w, h = img.size
    tiles = []
    for y in range(0, h - tile_size + 1, tile_size):
        for x in range(0, w - tile_size + 1, tile_size):
            tiles.append((x, y, img.crop((x, y, x + tile_size, y + tile_size))))
    return tiles


def clean_pngs(pattern="**/*.png"):
    for p in DATA_ROOT.glob(pattern):
        if p.name.startswith("."):
            p.unlink()


def main():
    clean_pngs()
    names = sorted(p.stem for p in (SRC_DIR / "A").glob("*.png") if not p.name.startswith("."))
    print(f"Found {len(names)} full-resolution pairs")

    rng = random.Random(SEED)
    rng.shuffle(names)
    n_test = max(1, int(len(names) * TEST_FRACTION))
    test_names = set(names[:n_test])
    train_names = set(names[n_test:])

    for split, split_names in (("train", train_names), ("test", test_names)):
        for sub in ("A", "B", "label"):
            (DATA_ROOT / split / sub).mkdir(parents=True, exist_ok=True)

        n_tiles = 0
        for name in split_names:
            img_a = Image.open(SRC_DIR / "A" / f"{name}.png").convert("RGB")
            img_b = Image.open(SRC_DIR / "B" / f"{name}.png").convert("RGB")
            label = Image.open(SRC_DIR / "label" / f"{name}.png").convert("L")

            tiles_a = tile_image(img_a, TILE_SIZE)
            tiles_b = tile_image(img_b, TILE_SIZE)
            tiles_l = tile_image(label, TILE_SIZE)

            for (x, y, ta), (_, _, tb), (_, _, tl) in zip(tiles_a, tiles_b, tiles_l):
                tile_name = f"{name}_{x}_{y}.png"
                ta.save(DATA_ROOT / split / "A" / tile_name)
                tb.save(DATA_ROOT / split / "B" / tile_name)
                tl.save(DATA_ROOT / split / "label" / tile_name)
                n_tiles += 1

        change_fracs = []
        for p in (DATA_ROOT / split / "label").glob("*.png"):
            if p.name.startswith("."):
                continue
            arr = np.array(Image.open(p))
            change_fracs.append((arr > 127).mean())

        print(f"{split}: {len(split_names)} source pairs -> {n_tiles} tiles of "
              f"{TILE_SIZE}x{TILE_SIZE}, mean changed-pixel fraction "
              f"{np.mean(change_fracs):.4f}")

    with open(DATA_ROOT / "split_manifest.json", "w") as f:
        json.dump({"train_source_pairs": sorted(train_names),
                    "test_source_pairs": sorted(test_names),
                    "tile_size": TILE_SIZE}, f, indent=2)

    # bundle one demo pair (full-res) for the offline dashboard
    demo_dir = DATA_ROOT / "demo"
    demo_dir.mkdir(exist_ok=True)
    demo_name = sorted(test_names)[0]
    for sub in ("A", "B", "label"):
        src = SRC_DIR / sub / f"{demo_name}.png"
        dst = demo_dir / f"{sub}.png"
        Image.open(src).save(dst)
    print(f"\nBundled demo pair '{demo_name}' -> {demo_dir}")


if __name__ == "__main__":
    main()
