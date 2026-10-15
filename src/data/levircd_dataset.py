"""Dataset for LEVIR-CD change-detection pairs.

Expects a directory layout (per split) of:
  <split>/A/<name>.png   - "before" image
  <split>/B/<name>.png   - "after" image
  <split>/label/<name>.png - binary change mask (0/255)
which matches the standard LEVIR-CD release layout.
"""
from pathlib import Path

import numpy as np
from PIL import Image
from torch.utils.data import Dataset

DATA_ROOT = Path(__file__).resolve().parents[2] / "data" / "levircd"


class LevirCDPairs(Dataset):
    def __init__(self, split: str = "val", transform=None, limit: int | None = None):
        split_dir = DATA_ROOT / split
        self.dir_a = split_dir / "A"
        self.dir_b = split_dir / "B"
        self.dir_label = split_dir / "label"
        self.names = sorted(p.name for p in self.dir_a.glob("*.png") if not p.name.startswith("."))
        if limit:
            self.names = self.names[:limit]
        self.transform = transform

    def __len__(self):
        return len(self.names)

    def __getitem__(self, idx):
        name = self.names[idx]
        img_a = Image.open(self.dir_a / name).convert("RGB")
        img_b = Image.open(self.dir_b / name).convert("RGB")
        label = Image.open(self.dir_label / name).convert("L")
        label = (np.array(label) > 127).astype(np.float32)

        if self.transform:
            img_a, img_b, label = self.transform(img_a, img_b, label)

        return img_a, img_b, label, name
