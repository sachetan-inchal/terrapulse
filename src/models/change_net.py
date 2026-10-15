"""Siamese U-Net for binary change detection.

Two weight-sharing encoders process the before/after images; their feature
maps are combined by absolute difference at each scale and fed to a U-Net
style decoder with skip connections to predict a per-pixel change mask.
"""
import torch
import torch.nn as nn


def conv_block(in_ch, out_ch):
    return nn.Sequential(
        nn.Conv2d(in_ch, out_ch, 3, padding=1),
        nn.BatchNorm2d(out_ch),
        nn.ReLU(inplace=True),
        nn.Conv2d(out_ch, out_ch, 3, padding=1),
        nn.BatchNorm2d(out_ch),
        nn.ReLU(inplace=True),
    )


class Encoder(nn.Module):
    def __init__(self, in_ch=3, base=32):
        super().__init__()
        self.enc1 = conv_block(in_ch, base)
        self.enc2 = conv_block(base, base * 2)
        self.enc3 = conv_block(base * 2, base * 4)
        self.enc4 = conv_block(base * 4, base * 8)
        self.pool = nn.MaxPool2d(2)

    def forward(self, x):
        f1 = self.enc1(x)
        f2 = self.enc2(self.pool(f1))
        f3 = self.enc3(self.pool(f2))
        f4 = self.enc4(self.pool(f3))
        return f1, f2, f3, f4


class SiameseUNet(nn.Module):
    def __init__(self, base=32):
        super().__init__()
        self.encoder = Encoder(in_ch=3, base=base)

        self.up3 = nn.ConvTranspose2d(base * 8, base * 4, 2, stride=2)
        self.dec3 = conv_block(base * 4 * 2, base * 4)
        self.up2 = nn.ConvTranspose2d(base * 4, base * 2, 2, stride=2)
        self.dec2 = conv_block(base * 2 * 2, base * 2)
        self.up1 = nn.ConvTranspose2d(base * 2, base, 2, stride=2)
        self.dec1 = conv_block(base * 2, base)

        self.out_conv = nn.Conv2d(base, 1, kernel_size=1)

    def forward(self, img_a, img_b):
        a1, a2, a3, a4 = self.encoder(img_a)
        b1, b2, b3, b4 = self.encoder(img_b)

        d4 = torch.abs(a4 - b4)
        d3 = torch.abs(a3 - b3)
        d2 = torch.abs(a2 - b2)
        d1 = torch.abs(a1 - b1)

        x = self.up3(d4)
        x = self.dec3(torch.cat([x, d3], dim=1))
        x = self.up2(x)
        x = self.dec2(torch.cat([x, d2], dim=1))
        x = self.up1(x)
        x = self.dec1(torch.cat([x, d1], dim=1))

        return self.out_conv(x)  # logits, shape (B, 1, H, W)
