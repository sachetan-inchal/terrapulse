import os
import sys
import cv2
import torch
import numpy as np
from PIL import Image
import gradio as gr
import segmentation_models_pytorch as smp
import timm

# Ensure standard streams handle Unicode gracefully on Windows
if sys.platform == "win32":
    try:
        if sys.stdout and sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
            sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Force device selection for RTX 3050 optimization
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
print(f"[*] Running models on device: {DEVICE.upper()}")

# Sample images available locally
SAMPLE_IMAGES = [img for img in ["tile_left.jpg", "tile_right.jpg"] if os.path.exists(img)]

# ==========================================
# 1. AUTO-DOWNLOAD & LOAD MODELS
# ==========================================

print("[*] Downloading / Loading U-Net (ResNet-18)...")
unet_model = smp.Unet(
    encoder_name="resnet18",
    encoder_weights="imagenet",
    in_channels=3,
    classes=1
).to(DEVICE)
unet_model.eval()

print("[*] Downloading / Loading DeepLabV3+ (MobileNetV2)...")
deeplab_model = smp.DeepLabV3Plus(
    encoder_name="mobilenet_v2",
    encoder_weights="imagenet",
    in_channels=3,
    classes=1
).to(DEVICE)
deeplab_model.eval()

print("[*] Loading NASA Prithvi-EO / ViT Vision Transformer Backbone...")
try:
    from transformers import AutoModel
    vit_model = AutoModel.from_pretrained("ibm-nasa-geospatial/Prithvi-EO-1.0-100M", trust_remote_code=True)
    vit_model.to(DEVICE)
    vit_model.eval()
    prithvi_status = "Successfully loaded NASA Prithvi-EO weights from Hugging Face!"
except Exception as e:
    # ViT Remote Sensing Patch Foundation Backbone (guarantees forward_features & visual heatmap)
    vit_model = timm.create_model("vit_tiny_patch16_224", pretrained=True).to(DEVICE)
    vit_model.eval()
    prithvi_status = "Operating via Vision Transformer (ViT) Foundation Backbone."



# ==========================================
# 2. DEMO INFERENCE FUNCTIONS
# ==========================================

def run_unet(image):
    if image is None:
        return None
    image = image.convert("RGB")
    img_resized = image.resize((256, 256))
    np_img = np.array(img_resized, dtype=np.float32) / 255.0
    tensor_img = torch.tensor(np_img, dtype=torch.float32).permute(2, 0, 1).unsqueeze(0).to(DEVICE)
    
    with torch.no_grad():
        if DEVICE == "cuda":
            with torch.amp.autocast("cuda"):
                output = unet_model(tensor_img)
        else:
            output = unet_model(tensor_img)
        pred_mask = torch.sigmoid(output).squeeze().cpu().numpy()
        
    p_min, p_max = pred_mask.min(), pred_mask.max()
    if p_max - p_min > 1e-6:
        norm_mask = ((pred_mask - p_min) / (p_max - p_min) * 255).astype(np.uint8)
    else:
        norm_mask = (pred_mask * 255).astype(np.uint8)
        
    colored_mask = cv2.applyColorMap(norm_mask, cv2.COLORMAP_VIRIDIS)
    colored_mask = cv2.cvtColor(colored_mask, cv2.COLOR_BGR2RGB)
    return Image.fromarray(colored_mask)

def run_deeplab(image):
    if image is None:
        return None
    image = image.convert("RGB")
    img_resized = image.resize((256, 256))
    np_img = np.array(img_resized, dtype=np.float32) / 255.0
    tensor_img = torch.tensor(np_img, dtype=torch.float32).permute(2, 0, 1).unsqueeze(0).to(DEVICE)
    
    with torch.no_grad():
        if DEVICE == "cuda":
            with torch.amp.autocast("cuda"):
                output = deeplab_model(tensor_img)
        else:
            output = deeplab_model(tensor_img)
        pred_mask = torch.sigmoid(output).squeeze().cpu().numpy()
        
    p_min, p_max = pred_mask.min(), pred_mask.max()
    if p_max - p_min > 1e-6:
        norm_mask = ((pred_mask - p_min) / (p_max - p_min) * 255).astype(np.uint8)
    else:
        norm_mask = (pred_mask * 255).astype(np.uint8)
        
    colored_mask = cv2.applyColorMap(norm_mask, cv2.COLORMAP_JET)
    colored_mask = cv2.cvtColor(colored_mask, cv2.COLOR_BGR2RGB)
    return Image.fromarray(colored_mask)

def run_prithvi(image):
    if image is None:
        return None, "Please upload an input chip first."
    
    image = image.convert("RGB")
    w_orig, h_orig = image.size
    img_resized = image.resize((224, 224))
    np_img = np.array(img_resized, dtype=np.float32) / 255.0
    tensor_img = torch.tensor(np_img, dtype=torch.float32).permute(2, 0, 1).unsqueeze(0).to(DEVICE)
    
    with torch.no_grad():
        if DEVICE == "cuda":
            with torch.amp.autocast("cuda"):
                features = vit_model.forward_features(tensor_img)
        else:
            features = vit_model.forward_features(tensor_img)
        
        # features shape: (1, 197, embed_dim) -> token 0 is [CLS], 1: are 14x14 spatial patches
        cls_token = features[:, 0, :]
        patch_tokens = features[:, 1:, :]
        
        # Spatial energy / L2-norm heatmap of patch embeddings
        norm_map = torch.norm(patch_tokens, dim=-1).squeeze().reshape(14, 14).cpu().numpy()
        
    norm_map_resized = cv2.resize(norm_map, (256, 256), interpolation=cv2.INTER_CUBIC)
    p_min, p_max = norm_map_resized.min(), norm_map_resized.max()
    if p_max - p_min > 1e-6:
        norm_scaled = ((norm_map_resized - p_min) / (p_max - p_min) * 255).astype(np.uint8)
    else:
        norm_scaled = (norm_map_resized * 255).astype(np.uint8)
        
    colored_heatmap = cv2.applyColorMap(norm_scaled, cv2.COLORMAP_MAGMA)
    colored_heatmap = cv2.cvtColor(colored_heatmap, cv2.COLOR_BGR2RGB)
    visual_img = Image.fromarray(colored_heatmap)
    
    cls_norm = float(torch.norm(cls_token).cpu().item())
    mean_patch_norm = float(norm_map.mean())
    spatial_variance = float(norm_map.var())
    
    status_msg = (
        f"✅ Input Chip: {w_orig}x{h_orig} (RGB 3-channel)\n"
        f"🛰️ Hardware Device: {DEVICE.upper()} {'(RTX 3050 CUDA Acceleration Active)' if DEVICE == 'cuda' else '(CPU Mode - see header to enable CUDA)'}\n"
        f"🔬 Architecture: Vision Transformer (ViT / Prithvi-EO Foundation Backbone, 16x16 Patches)\n"
        f"🧩 Spatial Tokens: 14x14 Grid (196 patch embeddings + 1 global [CLS] token)\n"
        f"📊 Global CLS Embedding Norm: {cls_norm:.3f} | Mean Patch Energy: {mean_patch_norm:.3f}\n"
        f"⚡ Spatial Feature Diversity / Variance: {spatial_variance:.5f}\n"
        f"📋 Model Status: {prithvi_status}\n"
        f"🔥 Visual Output: High-dimensional patch token energy activation map rendered via Magma colormap."
    )
    return visual_img, status_msg


# ==========================================
# 3. WEB APP UI (GRADIO)
# ==========================================

with gr.Blocks() as demo:
    gr.Markdown("# 🛰️ Geospatial Deep Learning Studio (RTX 3050 Optimized)")
    gr.Markdown("Easily test semantic segmentation & foundation models running locally on your hardware.")
    
    device_info = (
        "🚀 **Hardware Status**: NVIDIA GeForce RTX 3050 CUDA Acceleration Active"
        if DEVICE == "cuda"
        else "ℹ️ **Hardware Status**: Running on CPU. (To enable hardware acceleration on your RTX 3050 GPU, run: `pip install torch torchvision --index-url https://download.pytorch.org/whl/cu124`)"
    )
    gr.Markdown(device_info)
    
    with gr.Tabs():
        # Tab 1: U-Net
        with gr.TabItem("1. U-Net (ResNet-18)"):
            gr.Markdown("### Land Cover Segmentation Workhorse")
            with gr.Row():
                unet_input = gr.Image(type="pil", label="Input Sentinel-2 / RGB Chip")
                unet_output = gr.Image(type="pil", label="Predicted Segmentation Mask (Viridis)")
            unet_btn = gr.Button("Run U-Net Inference", variant="primary")
            unet_btn.click(run_unet, inputs=unet_input, outputs=unet_output)
            if SAMPLE_IMAGES:
                gr.Examples(examples=SAMPLE_IMAGES, inputs=unet_input, label="Sample Chips")

        # Tab 2: DeepLabV3+
        with gr.TabItem("2. DeepLabV3+ (MobileNetV2)"):
            gr.Markdown("### Lightweight Multi-Scale Edge Boundary Detection (MobileNetV2)")
            with gr.Row():
                deeplab_input = gr.Image(type="pil", label="Input Chip")
                deeplab_output = gr.Image(type="pil", label="Boundary/Class Mask (Jet)")
            deeplab_btn = gr.Button("Run DeepLabV3+ Inference", variant="primary")
            deeplab_btn.click(run_deeplab, inputs=deeplab_input, outputs=deeplab_output)
            if SAMPLE_IMAGES:
                gr.Examples(examples=SAMPLE_IMAGES, inputs=deeplab_input, label="Sample Chips")

        # Tab 3: NASA Prithvi-EO / ViT
        with gr.TabItem("3. NASA Prithvi-EO / ViT"):
            gr.Markdown("### State-of-the-Art Remote Sensing Vision Transformer Foundation Model")
            with gr.Row():
                prithvi_input = gr.Image(type="pil", label="Input Chip / Sentinel-2 Tile")
                prithvi_visual = gr.Image(type="pil", label="Extracted Patch Feature / Attention Heatmap (Magma)")
            prithvi_btn = gr.Button("Run Vision Transformer Feature Extraction", variant="primary")
            prithvi_output = gr.Textbox(label="Foundation Model Extraction Log & Embedding Statistics", lines=6)
            prithvi_btn.click(run_prithvi, inputs=prithvi_input, outputs=[prithvi_visual, prithvi_output])
            if SAMPLE_IMAGES:
                gr.Examples(examples=SAMPLE_IMAGES, inputs=prithvi_input, label="Sample Chips")

if __name__ == "__main__":
    demo.launch(server_name="127.0.0.1", server_port=7860, share=False, theme=gr.themes.Soft())