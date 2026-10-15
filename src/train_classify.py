"""Fine-tune ResNet18 on EuroSAT land-cover classification.

Run: python -m src.train_classify [--epochs N] [--subset N] [--batch-size N]
"""
import argparse
import csv
import time
from pathlib import Path

import torch
import torch.nn as nn
from torch.utils.data import DataLoader, Subset
from torchvision import transforms

from src.data.eurosat_dataset import EuroSATSplit, load_classes, IMAGENET_MEAN, IMAGENET_STD
from src.models.classifier import build_classifier

CKPT_DIR = Path(__file__).resolve().parents[1] / "checkpoints"
CKPT_PATH = CKPT_DIR / "classifier_resnet18.pt"
LOG_PATH = CKPT_DIR / "classify_training_log.csv"


def get_device():
    if torch.backends.mps.is_available():
        return torch.device("mps")
    if torch.cuda.is_available():
        return torch.device("cuda")
    return torch.device("cpu")


def build_loaders(batch_size: int, subset: int | None, workers: int = 0):
    train_tf = transforms.Compose([
        transforms.RandomHorizontalFlip(),
        transforms.RandomVerticalFlip(),
        transforms.RandomRotation(15),
        transforms.ToTensor(),
        transforms.Normalize(IMAGENET_MEAN, IMAGENET_STD),
    ])
    eval_tf = transforms.Compose([
        transforms.ToTensor(),
        transforms.Normalize(IMAGENET_MEAN, IMAGENET_STD),
    ])

    train_ds = EuroSATSplit("train", transform=train_tf)
    val_ds = EuroSATSplit("val", transform=eval_tf)

    if subset:
        train_ds = Subset(train_ds, list(range(min(subset, len(train_ds)))))
        val_ds = Subset(val_ds, list(range(min(max(subset // 5, 50), len(val_ds)))))

    train_loader = DataLoader(train_ds, batch_size=batch_size, shuffle=True,
                               num_workers=workers, persistent_workers=workers > 0)
    val_loader = DataLoader(val_ds, batch_size=batch_size, shuffle=False,
                             num_workers=workers, persistent_workers=workers > 0)
    return train_loader, val_loader


def run_epoch(model, loader, criterion, optimizer, device, train: bool):
    model.train() if train else model.eval()
    total_loss, correct, total = 0.0, 0, 0
    torch.set_grad_enabled(train)
    for images, labels in loader:
        images, labels = images.to(device), labels.to(device)
        if train:
            optimizer.zero_grad()
        outputs = model(images)
        loss = criterion(outputs, labels)
        if train:
            loss.backward()
            optimizer.step()
        total_loss += loss.item() * images.size(0)
        correct += (outputs.argmax(1) == labels).sum().item()
        total += images.size(0)
    torch.set_grad_enabled(True)
    return total_loss / total, correct / total


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--epochs", type=int, default=10)
    parser.add_argument("--subset", type=int, default=None,
                         help="limit train set size for a quick smoke run")
    parser.add_argument("--batch-size", type=int, default=64)
    parser.add_argument("--lr", type=float, default=1e-3)
    args = parser.parse_args()

    device = get_device()
    print(f"Device: {device}")

    classes = load_classes()
    train_loader, val_loader = build_loaders(args.batch_size, args.subset)
    print(f"Train batches: {len(train_loader)}, Val batches: {len(val_loader)}")

    model = build_classifier(num_classes=len(classes)).to(device)
    criterion = nn.CrossEntropyLoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=args.lr)

    CKPT_DIR.mkdir(exist_ok=True)
    best_val_acc = 0.0
    rows = []

    for epoch in range(1, args.epochs + 1):
        t0 = time.time()
        train_loss, train_acc = run_epoch(model, train_loader, criterion, optimizer, device, train=True)
        val_loss, val_acc = run_epoch(model, val_loader, criterion, optimizer, device, train=False)
        dt = time.time() - t0
        print(f"Epoch {epoch}/{args.epochs} | train_loss={train_loss:.4f} train_acc={train_acc:.4f} "
              f"val_loss={val_loss:.4f} val_acc={val_acc:.4f} ({dt:.1f}s)")
        rows.append([epoch, train_loss, train_acc, val_loss, val_acc, dt])

        if val_acc > best_val_acc:
            best_val_acc = val_acc
            torch.save({"model_state": model.state_dict(), "classes": classes,
                        "val_acc": val_acc, "epoch": epoch}, CKPT_PATH)
            print(f"  -> saved new best checkpoint (val_acc={val_acc:.4f})")

    with open(LOG_PATH, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["epoch", "train_loss", "train_acc", "val_loss", "val_acc", "seconds"])
        w.writerows(rows)

    print(f"\nBest val_acc: {best_val_acc:.4f} (checkpoint: {CKPT_PATH})")


if __name__ == "__main__":
    main()
