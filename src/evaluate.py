"""Manual sanity-check script: classify a single image and print prediction.

Run: python -m src.evaluate --image path/to/image.jpg
With no --image, picks a random test-set image.
"""
import argparse
import json
import random
from pathlib import Path

import torch
from PIL import Image
from torchvision import transforms

from src.data.eurosat_dataset import IMAGENET_MEAN, IMAGENET_STD, SPLITS_PATH
from src.models.classifier import build_classifier

CKPT_PATH = Path(__file__).resolve().parent.parent / "checkpoints" / "classifier_resnet18.pt"


def get_device():
    if torch.backends.mps.is_available():
        return torch.device("mps")
    if torch.cuda.is_available():
        return torch.device("cuda")
    return torch.device("cpu")


def load_model(device):
    ckpt = torch.load(CKPT_PATH, map_location=device)
    model = build_classifier(num_classes=len(ckpt["classes"]))
    model.load_state_dict(ckpt["model_state"])
    model.to(device).eval()
    return model, ckpt["classes"]


def predict(model, classes, image_path, device):
    tf = transforms.Compose([
        transforms.ToTensor(),
        transforms.Normalize(IMAGENET_MEAN, IMAGENET_STD),
    ])
    img = Image.open(image_path).convert("RGB")
    x = tf(img).unsqueeze(0).to(device)
    with torch.no_grad():
        logits = model(x)
        probs = torch.softmax(logits, dim=1)[0]
    top_idx = probs.argmax().item()
    return classes[top_idx], probs[top_idx].item(), probs


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--image", type=str, default=None)
    args = parser.parse_args()

    device = get_device()
    model, classes = load_model(device)

    if args.image:
        image_path = args.image
    else:
        with open(SPLITS_PATH) as f:
            data = json.load(f)
        sample = random.choice(data["splits"]["test"])
        image_path = sample["path"]
        print(f"(no --image given, using random test image) true label: "
              f"{classes[sample['label']]}")

    pred_class, confidence, probs = predict(model, classes, image_path, device)
    print(f"Image: {image_path}")
    print(f"Predicted: {pred_class}  (confidence {confidence:.2%})")
    print("\nAll class probabilities:")
    for c, p in sorted(zip(classes, probs.tolist()), key=lambda x: -x[1]):
        print(f"  {c:25s} {p:.2%}")


if __name__ == "__main__":
    main()
