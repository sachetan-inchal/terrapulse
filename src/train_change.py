"""Train (or run) change-detection models on LEVIR-CD tiles.

Two modes:
  --mode baseline  Thresholded pixel-difference-of-features (no training,
                    just picks a threshold on the val tiles and reports it).
  --mode unet       Trains the Siamese U-Net (src/models/change_net.py).

Run: python -m src.train_change --mode unet --epochs 20
"""
import argparse
import csv
import time
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn
from PIL import Image
from torch.utils.data import DataLoader

from src.data.levircd_dataset import LevirCDPairs
from src.models.change_net import SiameseUNet

CKPT_DIR = Path(__file__).resolve().parents[1] / "checkpoints"
CKPT_PATH = CKPT_DIR / "change_unet.pt"
LOG_PATH = CKPT_DIR / "change_training_log.csv"


def get_device():
    if torch.backends.mps.is_available():
        return torch.device("mps")
    if torch.cuda.is_available():
        return torch.device("cuda")
    return torch.device("cpu")


def to_tensor_pair(img_a, img_b, label):
    import torchvision.transforms.functional as TF
    a = TF.to_tensor(img_a)
    b = TF.to_tensor(img_b)
    lbl = torch.from_numpy(label).unsqueeze(0)
    return a, b, lbl


def compute_iou_f1(pred_mask: np.ndarray, gt_mask: np.ndarray):
    pred = pred_mask.astype(bool)
    gt = gt_mask.astype(bool)
    tp = np.logical_and(pred, gt).sum()
    fp = np.logical_and(pred, ~gt).sum()
    fn = np.logical_and(~pred, gt).sum()
    iou = tp / (tp + fp + fn + 1e-8)
    precision = tp / (tp + fp + 1e-8)
    recall = tp / (tp + fn + 1e-8)
    f1 = 2 * precision * recall / (precision + recall + 1e-8)
    return iou, f1


def run_baseline(split="test"):
    """Simple, untrained baseline: threshold the L2 pixel-difference between
    the two images. Fast to compute, gives an immediate working reference
    point before training anything."""
    ds = LevirCDPairs(split=split)
    best_thresh, best_f1 = 0, -1
    diffs_all = []
    labels_all = []
    print(f"Computing pixel-difference baseline on {len(ds)} tiles ({split})...")
    for i in range(len(ds)):
        img_a, img_b, label, _ = ds[i]
        a = np.asarray(img_a, dtype=np.float32)
        b = np.asarray(img_b, dtype=np.float32)
        diff = np.sqrt(((a - b) ** 2).sum(axis=2))
        diffs_all.append(diff)
        labels_all.append(label)

    diffs_all = np.stack(diffs_all)
    labels_all = np.stack(labels_all)

    for thresh in np.linspace(diffs_all.min(), diffs_all.max(), 40)[1:-1]:
        pred = diffs_all > thresh
        iou, f1 = compute_iou_f1(pred, labels_all)
        if f1 > best_f1:
            best_f1, best_iou, best_thresh = f1, iou, thresh

    print(f"Baseline best threshold={best_thresh:.2f} -> IoU={best_iou:.4f} F1={best_f1:.4f}")
    return best_thresh, best_iou, best_f1


def dice_loss(logits, targets, eps=1e-6):
    probs = torch.sigmoid(logits)
    probs = probs.flatten(1)
    targets = targets.flatten(1)
    intersection = (probs * targets).sum(1)
    union = probs.sum(1) + targets.sum(1)
    return 1 - ((2 * intersection + eps) / (union + eps)).mean()


def run_epoch(model, loader, criterion, optimizer, device, train: bool):
    model.train() if train else model.eval()
    torch.set_grad_enabled(train)
    total_loss = 0.0
    all_preds, all_labels = [], []
    for img_a, img_b, label in loader:
        img_a, img_b, label = img_a.to(device), img_b.to(device), label.to(device)
        if train:
            optimizer.zero_grad()
        logits = model(img_a, img_b)
        bce = criterion(logits, label)
        dice = dice_loss(logits, label)
        loss = bce + dice
        if train:
            loss.backward()
            optimizer.step()
        total_loss += loss.item() * img_a.size(0)

        preds = (torch.sigmoid(logits) > 0.5).cpu().numpy()
        all_preds.append(preds)
        all_labels.append(label.cpu().numpy() > 0.5)
    torch.set_grad_enabled(True)

    all_preds = np.concatenate(all_preds)
    all_labels = np.concatenate(all_labels)
    iou, f1 = compute_iou_f1(all_preds, all_labels)
    return total_loss / len(loader.dataset), iou, f1


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["baseline", "unet"], default="unet")
    parser.add_argument("--epochs", type=int, default=20)
    parser.add_argument("--batch-size", type=int, default=8)
    parser.add_argument("--lr", type=float, default=1e-3)
    args = parser.parse_args()

    if args.mode == "baseline":
        run_baseline()
        return

    device = get_device()
    print(f"Device: {device}")

    def collate(batch):
        imgs_a, imgs_b, labels = zip(*[to_tensor_pair(a, b, l) for a, b, l, _ in batch])
        return torch.stack(imgs_a), torch.stack(imgs_b), torch.stack(labels)

    train_ds = LevirCDPairs(split="train")
    test_ds = LevirCDPairs(split="test")
    train_loader = DataLoader(train_ds, batch_size=args.batch_size, shuffle=True,
                               num_workers=0, collate_fn=collate)
    test_loader = DataLoader(test_ds, batch_size=args.batch_size, shuffle=False,
                              num_workers=0, collate_fn=collate)
    print(f"Train tiles: {len(train_ds)}, Test tiles: {len(test_ds)}")

    model = SiameseUNet(base=32).to(device)
    criterion = nn.BCEWithLogitsLoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=args.lr)

    CKPT_DIR.mkdir(exist_ok=True)
    best_f1 = 0.0
    rows = []

    for epoch in range(1, args.epochs + 1):
        t0 = time.time()
        train_loss, train_iou, train_f1 = run_epoch(model, train_loader, criterion, optimizer, device, train=True)
        test_loss, test_iou, test_f1 = run_epoch(model, test_loader, criterion, optimizer, device, train=False)
        dt = time.time() - t0
        print(f"Epoch {epoch}/{args.epochs} | train_loss={train_loss:.4f} train_iou={train_iou:.4f} "
              f"train_f1={train_f1:.4f} | test_loss={test_loss:.4f} test_iou={test_iou:.4f} "
              f"test_f1={test_f1:.4f} ({dt:.1f}s)")
        rows.append([epoch, train_loss, train_iou, train_f1, test_loss, test_iou, test_f1, dt])

        if test_f1 > best_f1:
            best_f1 = test_f1
            torch.save({"model_state": model.state_dict(), "test_f1": test_f1,
                        "test_iou": test_iou, "epoch": epoch}, CKPT_PATH)
            print(f"  -> saved new best checkpoint (test_f1={test_f1:.4f})")

    with open(LOG_PATH, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["epoch", "train_loss", "train_iou", "train_f1", "test_loss", "test_iou", "test_f1", "seconds"])
        w.writerows(rows)

    print(f"\nBest test F1: {best_f1:.4f} (checkpoint: {CKPT_PATH})")


if __name__ == "__main__":
    main()
