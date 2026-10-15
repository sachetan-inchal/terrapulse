from pathlib import Path

import pytest

from src.data.eurosat_dataset import SPLITS_PATH, EuroSATSplit
from src.data.levircd_dataset import LevirCDPairs

pytestmark_eurosat = pytest.mark.skipif(not SPLITS_PATH.exists(), reason="EuroSAT not downloaded")


@pytest.mark.skipif(not SPLITS_PATH.exists(), reason="EuroSAT not downloaded")
def test_eurosat_split_item_shape():
    ds = EuroSATSplit("test")
    assert len(ds) > 0
    img, label = ds[0]
    assert img.size == (64, 64)
    assert isinstance(label, int)


LEVIRCD_TRAIN_DIR = Path(__file__).resolve().parents[1] / "data" / "levircd" / "train"


@pytest.mark.skipif(not LEVIRCD_TRAIN_DIR.exists(), reason="LEVIR-CD not prepared")
def test_levircd_pair_shapes_match():
    ds = LevirCDPairs("train")
    assert len(ds) > 0
    img_a, img_b, label, name = ds[0]
    assert img_a.size == img_b.size
    assert label.shape == img_a.size[::-1]
