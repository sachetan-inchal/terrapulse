import torch

from src.models.classifier import build_classifier
from src.models.change_net import SiameseUNet


def test_classifier_forward_shape():
    model = build_classifier(num_classes=10, pretrained=False)
    x = torch.randn(2, 3, 64, 64)
    out = model(x)
    assert out.shape == (2, 10)


def test_change_net_forward_shape():
    model = SiameseUNet(base=8)
    a = torch.randn(2, 3, 64, 64)
    b = torch.randn(2, 3, 64, 64)
    out = model(a, b)
    assert out.shape == (2, 1, 64, 64)


def test_change_net_is_symmetric_in_ab_order():
    # abs(encoder(a) - encoder(b)) == abs(encoder(b) - encoder(a)), so a true
    # Siamese (weight-shared) encoder must give identical output regardless
    # of before/after order.
    model = SiameseUNet(base=8)
    model.eval()
    a = torch.randn(1, 3, 64, 64)
    b = torch.randn(1, 3, 64, 64)
    with torch.no_grad():
        out_ab = model(a, b)
        out_ba = model(b, a)
    assert torch.allclose(out_ab, out_ba, atol=1e-5)
