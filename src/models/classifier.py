"""ResNet18 (ImageNet-pretrained) fine-tuned for EuroSAT's 10 land-cover classes."""
import torch.nn as nn
from torchvision.models import resnet18, ResNet18_Weights


def build_classifier(num_classes: int = 10, pretrained: bool = True) -> nn.Module:
    weights = ResNet18_Weights.IMAGENET1K_V1 if pretrained else None
    model = resnet18(weights=weights)
    model.fc = nn.Linear(model.fc.in_features, num_classes)
    return model
