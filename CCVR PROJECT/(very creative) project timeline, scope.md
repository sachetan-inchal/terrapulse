What you have now is actually enough to stop brainstorming and start **designing the research problem**.

I would make one major change to the direction:

> **Do not make the AI agent the research contribution. Make the computer-vision system the research contribution, and make the agent the layer that operates and investigates the CV system.**

That distinction will matter enormously when your faculty asks, _“What exactly did you research?”_

I also checked the current state of the relevant tooling. Google Earth Engine already provides a huge Earth-science data catalog and planetary-scale processing, including Landsat, Sentinel, land-cover, forest-change, fire, drought, water and human-activity datasets. ([Google for Developers](https://developers.google.com/earth-engine/datasets/catalog?utm_source=chatgpt.com "Earth Engine Data Catalog  |  Google for Developers")) And Prithvi has already evolved into a family of Earth-observation foundation models, including multi-temporal models and downstream models for crop classification, burn scars and floods. ([Hugging Face](https://huggingface.co/ibm-nasa-geospatial?utm_source=chatgpt.com "ibm-nasa-geospatial (IBM-NASA Prithvi Models Family)"))

So **U-Net + Prithvi + NDVI + an LLM** by themselves aren't novel.

But the way you combine and _experimentally evaluate_ them can be.

---

# 1. I would define your project like this

## Working title

### **EarthTrace: AI-Driven Computer Vision for Multi-Temporal Earth Change Detection and Evidence-Guided Investigation**

Or, if you want something more academic:

### **A Computer Vision Framework for Reliable Multi-Temporal Earth Observation and Evidence-Guided Geospatial Change Analysis**

Your central research problem:

> **How can computer vision reliably detect, align, quantify and interpret changes across heterogeneous Earth observations, while an AI agent retrieves external evidence to investigate the context surrounding those changes?**

And your architecture becomes:

```text
                         USER
                          │
                    "Bengaluru"
                          │
                          ▼
                 ┌─────────────────┐
                 │  AI ORCHESTRATOR│
                 └────────┬────────┘
                          │
             ┌────────────┼────────────┐
             ▼            ▼            ▼
       Earth Data      CV Engine    Web Search
             │            │            │
       Sentinel/Landsat   │        Papers/news/
       GEE/catalog        │        reports/events
             │            │            │
             └──────┬─────┘            │
                    ▼                   │
              IMAGE PAIRS              │
                    │                   │
                    ▼                   │
            REGISTRATION ENGINE         │
                    │                   │
             ┌──────┴──────┐            │
             ▼             ▼            │
        feature match   geometric       │
        RANSAC          alignment       │
             └──────┬──────┘            │
                    ▼                   │
             CHANGE DETECTION           │
                    │                   │
          ┌─────────┼──────────┐        │
          ▼         ▼          ▼        │
       U-Net     Prithvi      NDVI      │
       classes   features   spectral    │
          │         │          │        │
          └─────────┼──────────┘        │
                    ▼                   │
            CHANGE HEATMAP              │
                    │                   │
                    ▼                   │
           RELIABILITY / CONFIDENCE     │
                    │                   │
                    └─────────┬─────────┘
                              ▼
                    EVIDENCE INVESTIGATION
                              │
                              ▼
                     HUMAN-READABLE REPORT
```

That is a coherent system.

---

# 2. But here's the really important part

You need to decide what your **actual research contribution** is.

I see three possibilities.

### A. Event → environmental change

> "Can geopolitical/economic events explain changes detected in satellite imagery?"

Interesting, but scientifically dangerous.

### B. Predict future green-cover loss

> "Can we predict where vegetation will disappear next?"

Interesting, but **much too large for your 11-week timeline** if you want proper validation.

### C. Reliable multi-temporal change detection

> **"Can we make satellite/image change detection more reliable by explicitly modelling registration quality and feature/segmentation uncertainty?"**

**This is the one I would choose as the core research problem.**

Then A becomes your demonstration application.

---

# 3. Your novel thing could be a "Change Reliability Score"

This is where I think you can turn your existing experimentation into something research-like.

Most naive change detection looks like:

```text
Image A
   ↓
Image B
   ↓
Difference
   ↓
Heatmap
```

But what if the images aren't perfectly aligned?

Then:

```text
building moved by 4 pixels
        ↓
difference detector
        ↓
"OMG! LAND CHANGED!"
```

when nothing actually changed.

This is one of the fundamental problems in temporal remote sensing.

So your CV system can explicitly ask:

> **"How trustworthy is this detected change?"**

---

# 4. Build your own composite reliability parameter

Call it something like:

## **Temporal Change Reliability Score — TCRS**

Don't claim it is a globally new scientific metric until you've done a literature review. Instead say:

> "We propose and evaluate a project-specific composite reliability score."

For every detected change region, calculate components such as:

### Registration quality

RregR_{reg}

based on:

- RANSAC inlier ratio
    
- reprojection error
    
- number of reliable correspondences
    
- transformation stability
    

### Spectral consistency

RspecR_{spec}

Does the apparent change make sense across multiple bands?

### Segmentation confidence

RsegR_{seg}

How confident is U-Net / Prithvi about the class?

### Temporal consistency

RtempR_{temp}

Does the change persist across multiple observations?

Then:

TCRS=w1Rreg+w2Rspec+w3Rseg+w4RtempTCRS = w_1R_{reg} +w_2R_{spec} +w_3R_{seg} +w_4R_{temp}

with normalized components.

You can then classify:

```text
0.00 ─────────────── 1.00

LOW              MEDIUM              HIGH
│                   │                   │
Reject         Investigate          Reliable
```

**That is a much more interesting CV experiment than "we ran U-Net."**

---

# 5. Now you have an actual research experiment

Suppose you construct 500 image pairs.

Introduce controlled transformations:

- translation
    
- rotation
    
- scale
    
- crop
    
- mild perspective distortion
    
- noise
    
- illumination differences
    
- seasonal differences where possible
    

Then test:

### Method 1

```text
Raw pixel difference
```

### Method 2

```text
Feature matching
+
RANSAC
+
difference
```

### Method 3

```text
Registration
+
U-Net segmentation
+
difference
```

### Method 4

```text
Registration
+
U-Net
+
spectral features
+
TCRS
```

Now you have a proper experimental question:

> Does explicit registration and reliability estimation reduce false change detections?

---

# 6. Your results could look like this

Not invented numbers—these are the **metrics you should actually measure**:

|Approach|False Change Rate|IoU|Registration RMSE|Precision|Recall|
|---|--:|--:|--:|--:|--:|
|Pixel Difference|measure|measure|—|measure|measure|
|ORB + RANSAC|measure|measure|measure|measure|measure|
|SIFT + RANSAC|measure|measure|measure|measure|measure|
|U-Net + Difference|measure|measure|measure|measure|measure|
|Proposed TCRS|measure|measure|measure|measure|measure|

Now your teacher can ask:

> "What did you contribute?"

And you have an answer:

> **"We investigated whether registration-aware reliability estimation improves multi-temporal change detection under heterogeneous image conditions."**

That's research.

---

# 7. Your current code needs a fairly serious correction

This is important.

Your current demo looks impressive, but **the outputs are not yet scientifically meaningful**.

### Your U-Net

You create:

```python
smp.Unet(
    encoder_name="resnet18",
    encoder_weights="imagenet",
    in_channels=3,
    classes=1
)
```

You haven't loaded a land-cover-trained checkpoint.

Therefore you're essentially using an ImageNet-initialized architecture with an untrained segmentation head.

So this:

> "Predicted Segmentation Mask"

should **not yet be presented as a land-cover prediction**.

Same issue with DeepLabV3+.

You need either:

1. train/fine-tune them on an appropriate dataset, or
    
2. load a properly trained checkpoint.
    

---

# 8. There is an even bigger issue with your Prithvi implementation

Your code feeds:

```text
RGB
3 channels
224 × 224
```

into Prithvi-EO 1.0.

But the actual Prithvi-EO-1.0 configuration expects:

```text
6 channels
3 temporal frames
224 × 224
```

with bands:

```text
B02
B03
B04
B05
B06
B07
```

The published configuration explicitly specifies `in_chans: 6`, three frames and those six bands. ([Hugging Face](https://huggingface.co/ibm-nasa-geospatial/Prithvi-EO-1.0-100M/blob/main/config.json?utm_source=chatgpt.com "config.json · ibm-nasa-geospatial/Prithvi-EO-1.0-100M at main"))

And the multi-temporal crop-classification model uses 18-channel inputs representing **six bands across three time steps**. ([Hugging Face](https://huggingface.co/ibm-nasa-geospatial/Prithvi-EO-1.0-100M-multi-temporal-crop-classification?utm_source=chatgpt.com "ibm-nasa-geospatial/Prithvi-EO-1.0-100M-multi-temporal-crop-classification · Hugging Face"))

So your current code:

```python
image.convert("RGB")
```

is not actually giving Prithvi the kind of input it was designed for.

And if it falls into:

```python
timm.create_model("vit_tiny_patch16_224", pretrained=True)
```

you aren't using Prithvi at all.

You're using a generic ImageNet ViT.

---

# 9. Also, call your Prithvi visualization what it actually is

You currently say:

> "Attention Heatmap"

but you're calculating:

```python
torch.norm(patch_tokens, dim=-1)
```

That's **patch embedding magnitude / feature energy**, not attention.

Those are different things.

Call it:

> **Patch Feature Energy Map**

or

> **Spatial Feature Activation Map**

unless you actually extract attention matrices.

This kind of precision will protect you during the viva.

---

# 10. So your CV stack should become this

I'd simplify your model zoo.

You don't need 10 models.

Use **three levels**.

## Baseline 1 — Classical CV

```text
SIFT
  ↓
Feature matching
  ↓
RANSAC
  ↓
Homography
  ↓
Warp
  ↓
Difference
```

This is your classical computer-vision baseline.

---

## Baseline 2 — CNN

```text
Sentinel/Landsat
      ↓
U-Net
      ↓
Land-cover map
      ↓
Temporal comparison
```

This establishes your deep-learning baseline.

---

## Experimental model — Foundation model

```text
Multispectral temporal imagery
            ↓
         Prithvi
            ↓
       embeddings
            ↓
change representation / segmentation
```

Prithvi is genuinely relevant because the IBM/NASA family specifically targets Earth-observation foundation models, and newer Prithvi-EO versions support multi-temporal EO data. ([Hugging Face](https://huggingface.co/ibm-nasa-geospatial?utm_source=chatgpt.com "ibm-nasa-geospatial (IBM-NASA Prithvi Models Family)"))

Then compare:

```text
Classical CV
      vs
CNN
      vs
EO Foundation Model
      vs
Your registration/reliability framework
```

Now you have a research story.

---

# 11. What about the geopolitical-events idea?

Keep it.

But **move it to the application layer.**

Do NOT make:

> "Our AI predicts geopolitical events from satellite imagery."

That's an enormous claim.

Instead:

> **"Our system detects geographically and temporally localized environmental changes and retrieves external evidence that may provide context for those changes."**

For example:

```text
Satellite:
Built-up +12 km²
2021 → 2025
       ↓
Spatial hotspot
       ↓
Search agent
       ↓
"Industrial development"
"New highway"
"Mining project"
"Population expansion"
"Policy change"
       ↓
Evidence verification
       ↓
Contextual explanation
```

The agent should distinguish:

```text
OBSERVED
DOCUMENTED
CORRELATED
POSSIBLE
UNKNOWN
```

That makes the system much more credible.

---

# 12. Don't predict green-cover loss yet

I would **not put this into the core MVP**:

> "Predict where the next forest/green-cover loss will happen."

You'd need:

- long temporal datasets
    
- carefully defined labels
    
- spatial cross-validation
    
- climate variables
    
- socioeconomic variables
    
- roads/infrastructure
    
- land-use policy
    
- uncertainty estimation
    
- forecasting model
    
- serious evaluation
    

You can make it an **optional research extension**.

For example:

> "Given sufficient historical observations, the system can generate an experimental change-risk surface."

But your final 11-week deliverable should be **detection**, not ambitious planetary forecasting.

---

# 13. MCP is useful—but don't make MCP your research

You mentioned:

> AI agent through maybe an MCP server

Yes.

But MCP should simply be your **tool interface**.

Something like:

```text
                    LLM AGENT
                        │
                  MCP Tool Layer
                        │
        ┌───────────────┼───────────────┐
        │               │               │
        ▼               ▼               ▼
 get_satellite     run_registration   search_web
        │               │               │
        ▼               ▼               ▼
    GEE/API          OpenCV/CV       Search API
                        │
                        ▼
                 run_change_detection
                        │
                        ▼
                 generate_heatmap
```

The LLM doesn't directly perform computer vision.

It **orchestrates tools**.

For example:

```text
User:
"Investigate green-cover loss around Bengaluru between 2018 and 2025."
```

Agent:

```text
1. geocode("Bengaluru")
2. retrieve_satellite_images(...)
3. preprocess(...)
4. register_images(...)
5. calculate_landcover(...)
6. calculate_ndvi(...)
7. generate_change_heatmap(...)
8. search_web(...)
9. retrieve_scientific_sources(...)
10. cross_check(...)
11. generate_report(...)
```

That's a legitimate agentic architecture.

---

# 14. Your MCP tools could be extremely simple

You might eventually expose tools like:

```text
get_location()

get_satellite_scenes(
    region,
    start_date,
    end_date
)

preprocess_scene(
    scene_id
)

register_images(
    image_a,
    image_b
)

calculate_registration_quality(
    image_a,
    image_b
)

segment_landcover(
    image
)

calculate_ndvi(
    image
)

detect_change(
    image_a,
    image_b
)

generate_heatmap(
    change_map
)

search_evidence(
    query,
    location,
    date_range
)

search_scientific_literature(
    query
)

build_evidence_graph(
    observations
)
```

Then your agent becomes an **Earth-analysis operating layer**.

---

# 15. The middle demonstration becomes very easy to define

You have 11 weeks.

Don't wait until week 6 to show everything.

Your **midterm demo should be this:**

### Input

Two Sentinel/Landsat images of the same region.

### Pipeline

```text
IMAGE A
IMAGE B
  ↓
Feature detection
  ↓
Feature matching
  ↓
RANSAC
  ↓
Homography
  ↓
Registered B
  ↓
Difference map
  ↓
Change heatmap
```

And show the metrics:

```text
Features detected:       XXXX
Good matches:             XXX
RANSAC inliers:           XXX
Inlier ratio:             XX%
Registration RMSE:        X.XX px
Change pixels:            XX%
```

Then:

> "This is our computer-vision core."

That alone is a meaningful midterm.

---

# 16. The final demonstration adds intelligence

By week 11:

```text
                 SEARCH
                   │
              "Bengaluru"
                   │
                   ▼
           SATELLITE RETRIEVAL
                   │
            ┌──────┴──────┐
            ▼             ▼
        2018 image    2025 image
            │             │
            └──────┬──────┘
                   ▼
             REGISTRATION
                   │
                   ▼
             CHANGE MAP
                   │
         ┌─────────┼─────────┐
         ▼         ▼         ▼
       U-Net     NDVI     Prithvi
         │         │         │
         └─────────┼─────────┘
                   ▼
            CHANGE HEATMAP
                   │
                   ▼
          RELIABILITY SCORE
                   │
                   ▼
             AI AGENT
                   │
       ┌───────────┼───────────┐
       ▼           ▼           ▼
     Papers       News      Documents
       │           │           │
       └───────────┼───────────┘
                   ▼
             INVESTIGATION
```

That is a **very strong college demonstration**.

---

# 17. Here's how I'd divide the 11 weeks

## Weeks 1–2 — Research + CV baseline

### Build:

- Sentinel/Landsat acquisition
    
- preprocessing
    
- cloud masking
    
- image pairing
    
- SIFT/ORB
    
- feature matching
    
- RANSAC
    
- homography
    
- image warping
    

### Deliverable

**Registration benchmark.**

Do not move on until this works.

---

# Week 3 — Change detection

Implement:

- absolute difference
    
- SSIM/change metrics
    
- thresholding
    
- morphological cleanup
    
- connected components
    
- change area
    

Output:

```text
Before
After
Registered
Difference
Heatmap
Change polygons
```

---

# Week 4 — Registration research experiment

This is where I'd start your paper-like experiment.

Compare:

```text
ORB
SIFT
AKAZE
```

under:

```text
rotation
scale
translation
crop
perspective
noise
```

Measure:

- matching success
    
- inlier ratio
    
- RMSE
    
- transformation error
    
- runtime
    
- false change rate.
    

This alone could generate a lot of useful graphs.

---

# Week 5 — Your reliability parameter

Implement:

### TCRS

or whatever name you settle on.

Then investigate:

> Does registration quality predict change-detection reliability?

This gives you your **own research hypothesis**.

---

# Week 6 — U-Net

Now train/fine-tune properly.

Not random weights.

Use a real dataset.

Evaluate:

- IoU
    
- mIoU
    
- Dice/F1
    
- pixel accuracy
    
- confusion matrix.
    

And compare land-cover change using semantic classes rather than raw pixel differences.

---

# Week 7 — Prithvi

Don't just "run Prithvi."

Use it properly.

Ideally:

```text
6 spectral bands
×
multiple timestamps
```

and compare its representation/downstream performance against your CNN baseline.

The current Prithvi family specifically supports multi-temporal Earth-observation modelling, so this is much more scientifically defensible than feeding it an RGB photograph. ([Hugging Face](https://huggingface.co/collections/ibm-nasa-geospatial/prithvi-for-earth-observation?utm_source=chatgpt.com "Prithvi for Earth Observation - a ibm-nasa-geospatial Collection"))

---

# Week 8 — Geographic generalization

This is important.

Don't randomly split neighboring pixels.

Do something like:

```text
TRAIN
Bengaluru + Hyderabad

TEST
Chennai
```

or:

```text
TRAIN
Region A + Region B

TEST
Region C
```

Then ask:

> **Does the model generalize geographically?**

Remote-sensing foundation-model research identifies generalization, heterogeneous data and alignment as continuing challenges. ([arXiv](https://arxiv.org/abs/2503.22081?utm_source=chatgpt.com "A Survey on Remote Sensing Foundation Models: From Vision to Multimodality"))

This makes your evaluation much more serious.

---

# Week 9 — Backend + database + map UI

Move away from Gradio.

Architecture:

```text
React / Next.js
       ↓
FastAPI
       ↓
CV service
       ↓
PostGIS
       ↓
Satellite / object storage
```

Your Gradio app is your **research prototype**.

Your React app is your **product prototype**.

---

# Week 10 — AI agent + MCP

Add:

```text
LLM
 ↓
MCP
 ↓
CV tools
 ↓
Satellite tools
 ↓
Search tools
 ↓
Evidence database
```

The agent should be able to execute your existing pipeline—not generate arbitrary Python and pray it works.

---

# Week 11 — Evaluation + final integration

Absolutely no major new features.

Run:

```text
Registration benchmark
Segmentation benchmark
Change detection benchmark
Generalization benchmark
Agent evidence evaluation
Runtime benchmark
```

Then produce:

```text
Final heatmaps
Final tables
Final graphs
Final demo
Final report
```

---

# 18. Your final evaluation table could be excellent

Something like:

|Component|Metric|
|---|---|
|Image registration|Registration RMSE|
|Image registration|RANSAC inlier ratio|
|Feature matching|Match success rate|
|Change detection|Precision|
|Change detection|Recall|
|Change detection|F1|
|Change detection|IoU|
|U-Net|mIoU|
|U-Net|Dice|
|Prithvi|mIoU / downstream metric|
|Geographic generalization|Unseen-region mIoU|
|Reliability score|AUROC / calibration / correlation with true correctness|
|System|Processing time / km²|
|Agent|Evidence retrieval precision / citation validity|

That is far stronger than:

> "Our AI gives a heatmap."

---

# 19. And I would give each teammate a real ownership area

This is particularly important given what you said about your friends.

Don't divide the project as:

> "You copy prompts."

That will hurt you during the presentation.

Instead:

### You — CV / research lead

Own:

- SIFT/ORB/AKAZE
    
- RANSAC
    
- registration
    
- change detection
    
- TCRS
    
- experimental design
    
- metrics
    

You should be able to explain every equation.

---

### Roommate — ML/data pipeline

Own:

- datasets
    
- preprocessing
    
- U-Net
    
- training
    
- validation
    
- segmentation metrics
    
- experiment logging
    

They should be able to explain:

> "Why did mIoU change?"

---

### Friend — Agent/full-stack

Give them:

- MCP
    
- FastAPI
    
- search
    
- evidence retrieval
    
- React UI
    
- orchestration
    
- database
    

But make them document it and present a module.

If someone cannot explain their own module to the teacher, **do not make that module a critical dependency until they can.**

Claude Pro/GPT/etc. is irrelevant to the academic contribution. AI can help write code; the team still has to understand, test and defend it.

---

# 20. One thing I would NOT do

Don't build this:

```text
"Geopolitical event"
       ↓
LLM
       ↓
"forest loss heatmap"
```

That's too easy to make scientifically bogus.

Instead:

```text
SATELLITE OBSERVATION
        ↓
OBJECTIVE CHANGE
        ↓
SPATIAL/TEMPORAL ASSOCIATION
        ↓
SEARCH FOR DOCUMENTED EVENTS
        ↓
EVIDENCE
        ↓
POSSIBLE EXPLANATIONS
```

The direction of reasoning matters.

You're going from **physical evidence → contextual evidence**, rather than asking an LLM to invent physical evidence for a narrative.

---

# 21. And don't claim "AI discovers why"

Your interface could explicitly say:

> **Observed change**

> **Supporting evidence**

> **Potential contributing factors**

> **Unverified hypotheses**

> **Evidence gaps**

That would actually be a fantastic feature.

---

# 22. The really interesting research paper hiding inside this

Your paper could eventually have this structure:

### Research question

> Can registration-aware, multi-modal computer vision improve the reliability of multi-temporal Earth-observation change detection?

### Hypothesis

> Explicitly modelling geometric registration quality and semantic/spectral consistency will reduce false-positive change detections compared with direct image differencing.

### Baselines

- pixel difference
    
- ORB + RANSAC
    
- SIFT + RANSAC
    
- U-Net
    
- Prithvi
    

### Proposed system

```text
Registration
+
semantic segmentation
+
spectral analysis
+
temporal consistency
+
reliability score
```

### Experiments

Controlled transformations + real satellite pairs + geographically unseen test region.

### Application

AI evidence investigator.

**That is a computer-vision project with an AI agent attached to it.**

Not an AI-agent project pretending to be computer vision.

---

# 23. The one-sentence version I'd tell your professor

If they ask:

> **"So what are you actually researching?"**

Say:

> **"We're investigating whether registration-aware multi-temporal computer vision can make Earth-observation change detection more reliable, by combining geometric feature matching, semantic segmentation and spectral-temporal consistency, and we're building an AI agent on top of it that retrieves external evidence to investigate the context of detected changes."**

That's the sentence I'd build the entire project around.

And your demo story becomes beautifully simple:

> **Search → Retrieve → Align → Detect → Quantify → Verify → Investigate.**

The **CV is the engine.**  
The **AI agent is the operator.**  
The **heatmap is the evidence.**  
The **web research is the context.**

That gives you a meaningful prototype without pretending you've invented Earth observation itself.