"""Download EuroSAT (RGB) via torchvision and build train/val/test splits.

Run: python -m src.data.prepare_eurosat
Produces data/eurosat/splits.json listing (path, class_idx) for each split
and prints per-class counts so class balance can be checked by eye.
"""
import json
import random
from collections import Counter
from pathlib import Path

from torchvision.datasets import EuroSAT
from torchvision.datasets.utils import download_and_extract_archive

DATA_ROOT = Path(__file__).resolve().parents[2] / "data"
SPLIT_SEED = 42
TRAIN_FRAC, VAL_FRAC = 0.70, 0.15  # remaining 0.15 -> test

# The official host (madm.dfki.de) is frequently unreachable/times out from
# some networks. This is a byte-identical mirror (same MD5) hosted by the
# torchgeo project on Hugging Face, used as a fallback.
MIRROR_URL = "https://huggingface.co/datasets/torchgeo/eurosat/resolve/main/EuroSAT.zip"
EUROSAT_MD5 = "c8fa014336c82ac7804f0398fcb19387"


def _download_with_fallback(base_folder: Path):
    try:
        download_and_extract_archive(
            "https://madm.dfki.de/files/sentinel/EuroSAT.zip",
            download_root=str(base_folder),
            md5=EUROSAT_MD5,
        )
    except Exception as e:
        print(f"Official host failed ({e}); falling back to mirror: {MIRROR_URL}")
        download_and_extract_archive(
            MIRROR_URL,
            download_root=str(base_folder),
            filename="EuroSAT.zip",
            md5=EUROSAT_MD5,
        )


def main():
    DATA_ROOT.mkdir(parents=True, exist_ok=True)
    base_folder = DATA_ROOT / "eurosat"
    data_folder = base_folder / "2750"
    if not data_folder.exists():
        print(f"Downloading EuroSAT into {DATA_ROOT} ...")
        base_folder.mkdir(parents=True, exist_ok=True)
        _download_with_fallback(base_folder)
    else:
        print(f"EuroSAT already present at {data_folder}")
    ds = EuroSAT(root=str(DATA_ROOT), download=False)
    classes = ds.classes
    print(f"Loaded {len(ds)} images across {len(classes)} classes: {classes}")

    # group sample indices by class for a stratified split
    by_class = {c: [] for c in range(len(classes))}
    for path, label in ds.samples:
        by_class[label].append(path)

    rng = random.Random(SPLIT_SEED)
    splits = {"train": [], "val": [], "test": []}
    counts = {"train": Counter(), "val": Counter(), "test": Counter()}

    for label, paths in by_class.items():
        rng.shuffle(paths)
        n = len(paths)
        n_train = int(n * TRAIN_FRAC)
        n_val = int(n * VAL_FRAC)
        parts = {
            "train": paths[:n_train],
            "val": paths[n_train:n_train + n_val],
            "test": paths[n_train + n_val:],
        }
        for split, split_paths in parts.items():
            for p in split_paths:
                splits[split].append({"path": p, "label": label})
            counts[split][classes[label]] += len(split_paths)

    out_path = DATA_ROOT / "eurosat" / "splits.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w") as f:
        json.dump({"classes": classes, "splits": splits}, f)

    print(f"\nWrote splits to {out_path}")
    for split in ("train", "val", "test"):
        total = sum(counts[split].values())
        print(f"\n{split} ({total} images):")
        for c in classes:
            print(f"  {c:25s} {counts[split][c]}")


if __name__ == "__main__":
    main()
