"""PyTorch Dataset that reads the split lists produced by prepare_eurosat.py."""
import json
from pathlib import Path

from PIL import Image
from torch.utils.data import Dataset

DATA_ROOT = Path(__file__).resolve().parents[2] / "data"
SPLITS_PATH = DATA_ROOT / "eurosat" / "splits.json"

IMAGENET_MEAN = [0.485, 0.456, 0.406]
IMAGENET_STD = [0.229, 0.224, 0.225]


def load_classes():
    with open(SPLITS_PATH) as f:
        return json.load(f)["classes"]


class EuroSATSplit(Dataset):
    def __init__(self, split: str, transform=None):
        assert split in ("train", "val", "test")
        with open(SPLITS_PATH) as f:
            data = json.load(f)
        self.classes = data["classes"]
        self.samples = data["splits"][split]
        self.transform = transform

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, idx):
        item = self.samples[idx]
        img = Image.open(item["path"]).convert("RGB")
        if self.transform:
            img = self.transform(img)
        return img, item["label"]
