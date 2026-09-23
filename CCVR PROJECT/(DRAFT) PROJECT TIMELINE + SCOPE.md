Yes. With **11 weeks**, I would deliberately change the goal from _“build a pipeline and demonstrate it”_ to:

> **Build a complete vertical-slice product where the computer-vision system is the core engine, and the web application + AI research agent are interfaces around that engine.**

The key is **not** to build your entire long-term Earth archive in 11 weeks. Build one impressive, end-to-end slice that proves the architecture can scale.

# 11-Week MVP Strategy

### Your MVP should answer one complete question:

> **“What changed in this region, where did it change, and what evidence exists about why it changed?”**

For example:

**Bengaluru → 2015 vs 2025**

```text
Satellite imagery
       ↓
Preprocessing
       ↓
U-Net
       ↓
Land-cover maps
       ↓
NDVI
       ↓
Change detection
       ↓
Quantitative results
       ↓
Web dashboard
       ↓
AI Research Agent
       ↓
Search engine
       ↓
Evidence + explanation
```

That is a **full-stack AI product**, not just a machine-learning notebook.

---

# 1. Freeze the MVP scope

I strongly recommend making the MVP contain exactly these components:

### Core Computer Vision

- Landsat 8/9
    
- 5-band or carefully selected multispectral input
    
- U-Net
    
- 5 land-cover classes
    
- segmentation
    
- mIoU / IoU / Dice / pixel accuracy
    
- geographic holdout test
    

### Environmental Analysis

- NDVI
    
- land-cover area in km²
    
- percentage composition
    
- temporal comparison
    
- class-to-class transitions
    

### Web Application

- region selection
    
- year/date selection
    
- satellite imagery viewer
    
- predicted land-cover map
    
- NDVI map
    
- statistics
    
- change map
    
- charts
    

### AI Agent

User asks:

> **“Why did built-up area increase in this region?”**

Agent:

1. receives detected change
    
2. identifies relevant location/time
    
3. searches web/scientific sources
    
4. retrieves evidence
    
5. summarizes possible explanations
    
6. cites sources
    
7. distinguishes evidence from inference
    

That is enough.

---

# 2. What NOT to build in the 11 weeks

This is extremely important.

Do **not** attempt all of these for the MVP:

- global Earth archive
    
- every satellite provider
    
- millions of historical images
    
- sophisticated 3D Earth engine
    
- custom satellite image search engine
    
- advanced image stitching across arbitrary sensors
    
- building-level detection
    
- multiple deep-learning architectures
    
- autonomous multi-agent society
    
- 2100/2200/2300 prediction system
    
- Kubernetes/microservices everywhere
    

Those belong in:

> **Future Architecture / Scalability / Long-Term Vision**

Your MVP should prove the **core loop**.

---

# 3. Recommended architecture

I would build it like this:

```text
                    ┌──────────────────────┐
                    │       WEB UI         │
                    │ React / Next.js      │
                    │ Map + Charts + Chat  │
                    └──────────┬───────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │      FASTAPI         │
                    │    Backend API       │
                    └──────────┬───────────┘
                               │
             ┌─────────────────┼──────────────────┐
             │                 │                  │
             ▼                 ▼                  ▼
      ┌─────────────┐   ┌──────────────┐   ┌──────────────┐
      │ CV ENGINE   │   │ GEO ENGINE   │   │ AI RESEARCH  │
      │             │   │              │   │ AGENT        │
      │ U-Net       │   │ NDVI         │   │              │
      │ Inference   │   │ Change       │   │ Search       │
      │ Segmentation│   │ Detection    │   │ Retrieval    │
      │ Evaluation  │   │ Statistics   │   │ Evidence     │
      └──────┬──────┘   └──────┬───────┘   └──────┬───────┘
             │                  │                  │
             └──────────────────┼──────────────────┘
                                ▼
                     ┌─────────────────────┐
                     │   DATA / STORAGE    │
                     │                     │
                     │ PostgreSQL/PostGIS  │
                     │ Object Storage      │
                     │ Satellite Metadata  │
                     └─────────────────────┘
```

---

# 4. Tech stack I would actually choose

Don't over-engineer it.

|Layer|Technology|
|---|---|
|Satellite data|**Google Earth Engine + Landsat**|
|Geospatial processing|**Python + Rasterio + GDAL + GeoPandas**|
|Numerical processing|**NumPy + Pandas**|
|Computer Vision|**PyTorch + U-Net**|
|Spectral analysis|**NumPy / Rasterio**|
|Backend|**FastAPI**|
|Frontend|**React / Next.js**|
|Maps|**MapLibre or Leaflet**|
|Database|**PostgreSQL + PostGIS**|
|File storage|Local initially → cloud object storage later|
|AI Agent|**Python + LLM API**|
|Web search|Search API / supported web-search provider|
|RAG|Start simple; add **pgvector** if needed|
|Authentication|Skip initially unless required|
|Deployment|Docker + one cloud deployment|
|Version control|GitHub|
|ML experimentation|Google Colab|
|API testing|Postman / Swagger|
|Charts|Recharts / Plotly|

### One important choice:

I would **not use Streamlit as the final frontend** if your explicit goal is a full-stack web application.

Use:

> **Next.js/React + FastAPI**

You can still use Streamlit internally during early experimentation.

---

# 5. Your 11-week development roadmap

## WEEK 1 — Architecture + Dataset

### Goal

Get the entire project technically defined.

Build:

- GitHub repository
    
- project structure
    
- GEE setup
    
- study region
    
- satellite acquisition
    
- class definitions
    
- database schema
    
- API architecture
    
- frontend wireframes
    

Your team should finish Week 1 knowing:

```text
What goes in?
What happens?
What comes out?
Where is each output stored?
Which API exposes it?
```

### Deliverable

**Architecture + working satellite data extraction**

---

# WEEK 2 — Dataset + Preprocessing

Build the actual dataset.

```text
Landsat
 ↓
Cloud masking
 ↓
Band selection
 ↓
Normalization
 ↓
Tiling
 ↓
Training / validation / test
```

Create:

```text
images/
masks/
metadata/
```

Use geographically separated validation/test data if possible.

### Deliverable

**Reproducible training dataset**

---

# WEEK 3 — U-Net Baseline

Now forget the web application for a moment.

Make the CV engine work.

```text
Satellite tile
      ↓
    U-Net
      ↓
Segmentation mask
```

Implement:

- model
    
- loss
    
- training loop
    
- validation
    
- checkpoint saving
    
- inference
    

### Deliverable

**First trained U-Net producing actual land-cover maps**

---

# WEEK 4 — CV Evaluation

This is where your mentor's requirements become concrete.

Calculate:

- Pixel Accuracy
    
- IoU per class
    
- mIoU
    
- Dice/F1
    
- confusion matrix
    

Then test on your geographically unseen region.

### Deliverable

A results table such as:

```text
                     Test Region
mIoU                    XX.X%
Forest IoU              XX.X%
Agriculture IoU         XX.X%
Water IoU               XX.X%
Built-up IoU            XX.X%
Bare Land IoU            XX.X%
```

And:

> **Geographic generalization gap: XX.X percentage points**

---

# WEEK 5 — NDVI + Change Detection

Now connect the CV engine to environmental analysis.

Implement:

```text
Year 1 satellite
      ↓
     U-Net
      ↓
Land-cover map
      ↓
Statistics
```

and:

```text
Year 2 satellite
      ↓
     U-Net
      ↓
Land-cover map
```

Then:

```text
Map 1
 ↓
Comparison
 ↓
Change map
 ↓
Transition matrix
```

Add NDVI.

### Outputs

- land-cover km²
    
- land-cover %
    
- NDVI
    
- change km²
    
- change %
    
- transition matrix
    

### Deliverable

**Complete analytical engine**

At this point, you already have the heart of the project.

---

# WEEK 6 — Backend

Turn your notebooks/scripts into services.

Build FastAPI endpoints like:

```text
POST /analyze
GET  /regions
GET  /imagery
GET  /landcover
GET  /ndvi
GET  /changes
GET  /statistics
```

Conceptually:

```text
Frontend
   ↓
FastAPI
   ↓
CV / Geo processing
   ↓
Results
```

### Deliverable

**Functional backend API**

---

# WEEK 7 — Web UI

Now build the product.

I'd make the main screen something like:

```text
┌──────────────────────────────────────────────┐
│ EARTH INTELLIGENCE                           │
├──────────────────────────────────────────────┤
│                                              │
│ Region: Bengaluru       Year: 2015 → 2025   │
│                                              │
│ ┌────────────────────────────────────────┐   │
│ │                                        │   │
│ │              MAP                       │   │
│ │                                        │   │
│ └────────────────────────────────────────┘   │
│                                              │
│  Forest     Built-up     Agriculture         │
│  XX km²     XX km²       XX km²              │
│                                              │
│  NDVI       Change       Area mapped         │
│  XX         XX km²       XXXX km²            │
└──────────────────────────────────────────────┘
```

Tabs could be:

**Overview | Land Cover | NDVI | Change | Investigate**

### Deliverable

**Usable web interface**

---

# WEEK 8 — Connect Frontend + CV

This is the critical integration week.

User should be able to:

```text
Select region
     ↓
Select dates
     ↓
Click Analyze
     ↓
Backend
     ↓
Satellite data
     ↓
U-Net
     ↓
Analysis
     ↓
Results
     ↓
Browser
```

No notebook should be required.

### Deliverable

**End-to-end working application**

---

# WEEK 9 — AI Research Agent

Now add the "why?" layer.

Your UI gets a button:

> 🔍 **Investigate this change**

The agent receives structured information:

```text
Location:
Bengaluru

Period:
2015–2025

Detected changes:
Built-up +XX km²
Forest -XX km²
NDVI Δ = -X.XX
```

The agent then generates searches such as:

```text
Bengaluru urban expansion 2015 2025
Bengaluru land use change
Bengaluru infrastructure development
Bengaluru population growth
Bengaluru environmental reports
```

Then retrieves sources.

### Deliverable

**Search-connected research agent**

---

# WEEK 10 — Evidence + Integration

This is where you make the agent scientifically useful rather than just another chatbot.

Every result should contain:

```text
Claim
↓
Source
↓
Date
↓
Location relevance
↓
Evidence type
```

For example:

```text
OBSERVED
Built-up area increased by X km²
Source: Your CV analysis

DOCUMENTED
Infrastructure development occurred during this period
Source: Government report

CORRELATED
Population increased during the same period
Source: Census/statistical source

INFERENCE
These factors may be associated with the observed expansion
```

The agent should explicitly say when evidence is insufficient.

### Deliverable

**Evidence-grounded explanation interface**

---

# WEEK 11 — Final Testing + Deployment

No new features.

This week is for:

### Model testing

- mIoU
    
- class IoU
    
- Dice/F1
    
- pixel accuracy
    
- unseen-region test
    

### Geographic testing

- km² processed
    
- % study area mapped
    
- change km²
    
- transition accuracy
    

### System testing

- API response
    
- frontend functionality
    
- failed inputs
    
- inference time
    
- search failures
    
- agent hallucination checks
    

### Final deployment

```text
GitHub
   ↓
Docker
   ↓
Cloud
   ↓
Public/demo URL
```

### Deliverable

**Deployed MVP + final evaluation report**

---

# 6. Your final demo should be one continuous story

This is where I think you can make the project feel much bigger than a normal college ML project.

Don't demonstrate:

> "Here is our U-Net."

Instead:

### Step 1

User enters:

> **Bengaluru**

### Step 2

Select:

> **2015 → 2025**

### Step 3

System retrieves/processes imagery.

### Step 4

U-Net generates:

> **Land-cover map**

### Step 5

System calculates:

> **Forest: X km²**  
> **Built-up: X km²**  
> **Agriculture: X km²**

### Step 6

NDVI analysis:

> **Mean NDVI: X → X**

### Step 7

Change detection:

> **X km² changed**

with transitions:

```text
Agriculture → Built-up
Forest → Built-up
etc.
```

### Step 8

User clicks:

> **“Investigate this change”**

### Step 9

AI agent searches the web.

### Step 10

It returns:

> **Observed change**

> **Relevant documented events**

> **Scientific/contextual evidence**

> **Sources**

> **Uncertainty**

That's your **wow moment**.

---

# 7. Your project then has three distinct layers

This is also a very clean way to explain it to your mentor.

## Layer 1 — SEE

### Computer Vision

> **What is present?**

U-Net → land-cover segmentation

---

## Layer 2 — MEASURE

### Geospatial Analytics

> **What changed?**

NDVI + temporal comparison + area statistics + transitions

---

## Layer 3 — INVESTIGATE

### Agentic AI

> **What documented evidence exists about the change?**

Search → retrieval → evidence → synthesis

---

### So your core philosophy becomes:

# **SEE → MEASURE → INVESTIGATE**

And **Computer Vision remains the heart**.

The agent doesn't replace the CV system.

It consumes the **structured evidence generated by the CV system**.

That distinction is important:

```text
                  COMPUTER VISION
                       │
                       │
                 "What changed?"
                       │
                       ▼
              GEOSPATIAL ANALYSIS
                       │
                       │
                 "How much?"
                       │
                       ▼
                 AI RESEARCH
                       │
                       │
                 "What evidence
                  exists about it?"
                       │
                       ▼
                  HUMAN USER
```

The human ultimately interprets the evidence; the system provides the observations, measurements, and sourced context.

---

# 8. What I would put on your MVP specification

You can literally give this to your mentor:

### **11-Week MVP**

**Input**

> Multispectral Landsat imagery + geographic region + time period

**Core AI**

> U-Net semantic segmentation

**Environmental analysis**

> NDVI + land-cover statistics + temporal change detection

**Geospatial output**

> Land-cover maps + change maps + km²/% statistics

**Web application**

> Interactive map + analytics dashboard + temporal comparison

**AI Agent**

> Search-connected evidence retrieval and contextual explanation

**Final evaluation**

> mIoU + class IoU + Dice/F1 + geographic generalization + area mapped + change detected + system performance

**Deployment**

> Full-stack web application accessible through a browser

---

## The one thing I'd change from your original vision

Don't make **"image stitching"** a mandatory MVP feature.

It's technically interesting, but it can consume a disproportionate amount of your 11 weeks and isn't necessary to prove the central idea.

Make it:

> **Phase 2: Registration + stitching + large-scale Earth archive**

Your 11-week MVP should instead nail:

**Landsat → U-Net → Land Cover → NDVI → Change → Web → AI Investigation**

If that works end-to-end, you have a very strong proof-of-concept and a clean foundation for adding the **global imagery archive, image registration, 3D Earth globe, temporal slider, and larger multi-agent architecture** later.

# [DRAFT] MVP SCOPE

Yes — **this changes the MVP architecture in a useful way.** Your “search Bengaluru → find two observations → automatically align them → compare → heatmap” idea is feasible as an 11-week proof of concept, provided you constrain the image sources and comparison conditions.

The important part is that you are actually trying to learn and demonstrate **real computer vision**, not just run U-Net on already-aligned raster tiles.

I would make this your central demonstration:

# **Search → Find → Align → Compare → Explain**

### User searches:

> **Bengaluru**

Your system:

```text
"Bengaluru"
     ↓
Find geographically relevant imagery
     ↓
Image A                    Image B
Older                      Newer
     ↓                        ↓
       Computer Vision
             ↓
   Detect features/keypoints
             ↓
      Match correspondences
             ↓
   Estimate transformation
      (rotation/scale/
       perspective/affine)
             ↓
        Warp / Align
             ↓
      Compare imagery
             ↓
       Change Heatmap
             ↓
      Land-cover analysis
             ↓
       AI Research Agent
             ↓
"What documented evidence
 exists about this change?"
```

That is a much more interesting CV project.

---

# But I would separate two image sources

This is the key architectural decision.

## Track A — Reliable scientific mode

Use **Sentinel-2** or Landsat.

This gives you:

- known coordinates
    
- known acquisition dates
    
- consistent sensor characteristics
    
- multispectral bands
    
- repeated observations
    
- reproducible experiments
    

Sentinel-2's constellation provides roughly **5-day revisit time under nominal conditions**, although actual usable observations can be affected by clouds and other conditions.

This should be your **scientific ground truth / primary analysis mode**.

---

# Track B — "JARVIS" visual mode

The user searches:

> **New York**

Your agent retrieves two geographically relevant images from permitted/public sources:

```text
Image A — older
Image B — newer
```

They might be:

- rotated
    
- resized
    
- cropped
    
- different resolutions
    
- slightly shifted
    
- perspective distorted
    

Your CV system attempts:

> **"Make these two images comparable automatically."**

This is where you demonstrate registration.

---

# The computer vision stack becomes much richer

Instead of simply:

> Image → U-Net

you now have:

```text
Image A ────────┐
                │
                ▼
        Feature Detection
                │
        SIFT / ORB / AKAZE
                │
                ▼
        Feature Matching
                │
       Lowe ratio / BF /
          FLANN matching
                │
                ▼
         Outlier rejection
             RANSAC
                │
                ▼
       Transformation model
      ┌─────────┼─────────┐
      ▼         ▼         ▼
   Affine    Homography   ...
      └─────────┼─────────┘
                ▼
          Image Warping
                │
                ▼
       Registered Images
                │
                ▼
       Difference / Change
                │
                ▼
          Heatmap
```

That gives your project legitimate **classical computer vision + deep learning**.

---

# What each technique teaches you

### 1. Feature detection

Find distinctive points:

```text
corners
edges
building intersections
road junctions
structures
```

Possible algorithms:

- SIFT
    
- ORB
    
- AKAZE
    

For your project, I'd start with **SIFT + ORB** so you can demonstrate the difference between robustness and computational efficiency.

---

### 2. Feature matching

Suppose:

```text
Image A                    Image B

   ●                         ●
      ●                   ●
           ●           ●
                ●   ●
```

The system determines which features correspond.

---

### 3. RANSAC

This is particularly important.

Real image matching produces incorrect correspondences.

RANSAC estimates a transformation while rejecting outliers.

Conceptually:

```text
100 matches
    ↓
RANSAC
    ↓
72 reliable matches
    +
28 rejected matches
```

You can actually display this in your UI.

That makes the system visually impressive **and technically explainable**.

---

# 4. Homography / affine transformation

If one image is:

- rotated
    
- scaled
    
- translated
    
- mildly perspective-distorted
    

you can estimate a transformation matrix.

Then:

```text
Image B
   ↓
Transformation matrix
   ↓
WarpPerspective()
   ↓
Image B aligned with Image A
```

This is the part that gives you the **"JARVIS adjusts the image automatically"** effect.

But be precise about what it can handle.

A single homography works well when the scene is approximately planar or the viewpoint differences are modest. Arbitrary 3D viewpoint changes, severe perspective differences, or major occlusions require more advanced methods.

---

# 5. Then calculate the change heatmap

Once registered:

```text
Reference Image
       │
       │
       ├──────────► Difference
       │
New Image
```

For example:

```text
difference = |Image_A - Image_B|
```

Then:

```text
difference
     ↓
threshold / statistical filtering
     ↓
change mask
     ↓
heatmap
```

You can visualize:

```text
No significant change
        ↓
     low value

Strong difference
        ↓
     high value
```

But there is an important scientific caveat:

**A raw image difference is not automatically a land-cover change.**

Differences can come from:

- shadows
    
- clouds
    
- lighting
    
- season
    
- atmospheric conditions
    
- different cameras
    
- different viewing angles
    
- vegetation phenology
    

This is actually a **great research problem for your project**, rather than something to hide.

---

# Your Sentinel-2 mode solves much of this

For Sentinel-2 you can deliberately choose:

```text
Location: Bengaluru

Image A:
2020-01-15

Image B:
2025-01-15
```

Same approximate season.

Then:

```text
cloud masking
       ↓
band harmonization
       ↓
registration
       ↓
comparison
       ↓
change map
```

You can also use spectral indices and your U-Net segmentation rather than relying purely on RGB pixel differences.

---

# Your U-Net then becomes the second layer

This is where your original project fits beautifully.

Instead of:

> **U-Net OR image registration**

you have:

### Computer Vision Layer 1

**Image Registration**

> Make different observations spatially comparable.

### Computer Vision Layer 2

**Semantic Segmentation**

> Understand what is present.

### Computer Vision Layer 3

**Change Detection**

> Determine what changed.

### Environmental Layer

**NDVI / spectral analysis**

> Quantify vegetation-related changes.

### Agentic Layer

**Evidence retrieval**

> Investigate documented context surrounding the detected change.

---

# And your web application becomes much more compelling

Your home page could literally have:

## 🌍 Search Earth

**[ Bengaluru __________________ ] 🔍**

Then:

```text
┌──────────────────────────────────────────────┐
│              BENGALURU                       │
│                                              │
│   EARLIER                LATER               │
│   2015                   2025                │
│                                              │
│   [ satellite ]          [ satellite ]       │
│                                              │
│        ↘                    ↙                 │
│          AUTOMATICALLY ALIGNED               │
│                    ↓                         │
│             CHANGE HEATMAP                   │
│                                              │
└──────────────────────────────────────────────┘
```

And underneath:

```text
Area analyzed             XXXX km²

Changed area               XXX km²

Built-up change             +XX km²

Forest change               -XX km²

Mean NDVI                    X.XX → X.XX
```

Then:

### **Investigate Change →**

The agent opens:

> **What could explain these observed changes?**

and searches for relevant evidence.

---

# This gives you a genuinely impressive 11-week MVP

I'd actually redefine your project around this:

## **Core MVP**

> **A geographic search-driven Earth observation system that automatically retrieves or accesses multi-temporal imagery, registers heterogeneous images using computer vision, detects spatial changes, quantifies land-cover/environmental indicators, and uses an AI research agent to retrieve evidence about the observed changes.**

That is much closer to the vision you've been describing.

---

# Your 11 weeks should then look like this

|Week|Main achievement|
|---|---|
|**1**|Architecture + Sentinel-2/Landsat data pipeline|
|**2**|Image preprocessing + geographic search|
|**3**|SIFT/ORB feature detection + matching|
|**4**|RANSAC + affine/homography registration|
|**5**|Difference maps + change heatmaps|
|**6**|U-Net segmentation|
|**7**|NDVI + land-cover/change statistics|
|**8**|FastAPI backend + database/storage|
|**9**|React/Next.js map-based UI|
|**10**|Search-connected AI research agent|
|**11**|Integration + evaluation + deployment|

### Critical dependency

**Weeks 3–5 are your biggest technical risk.**

Don't wait until Week 10 to discover that arbitrary internet images cannot be reliably registered.

Build a **registration benchmark immediately**.

For example:

```text
Dataset:
100 image pairs

Transformation:
rotation
scale
crop
translation
mild perspective

Measure:
matching success %
registration RMSE
inlier ratio
successful alignment %
```

Then you know objectively whether your "JARVIS" component works.

---

# One more important design decision

Don't promise:

> **"Our system can take any two internet images of Bengaluru and always compare them."**

That's much harder than it sounds because an image of Bengaluru from street level and an aerial image from another viewpoint may have almost no valid geometric correspondence.

Instead define:

> **"The system automatically attempts registration of geographically related multi-temporal images and quantifies registration confidence. When registration quality is insufficient, the system rejects the comparison rather than producing a misleading heatmap."**

That last part is **very important**.

A professional CV system should be capable of saying:

> **“Insufficient reliable correspondences — comparison rejected.”**

rather than hallucinating a change map.

---

# Your final project story becomes extremely clean

### **SEARCH**

> Where?

### **RETRIEVE**

> What observations exist?

### **REGISTER**

> Can we align them?

### **SEGMENT**

> What is there?

### **COMPARE**

> What changed?

### **QUANTIFY**

> How much changed?

### **INVESTIGATE**

> What evidence exists about it?

### **VISUALIZE**

> Show the result on a map/timeline.

That is the architecture I would build around for your 11-week MVP.

And importantly, **computer vision remains the heart of the project**: registration, feature matching, segmentation and change detection are doing the actual visual reasoning; the web application is the delivery layer and the agent is the evidence/context layer.

# CHANGE OF SCOPE
Yes — and I think this realization is actually **good news for your project**.

You should **not** build a project whose claim is:

> “We created a system that can analyze satellite imagery and detect environmental change.”

Because Google Earth Engine already provides a huge amount of that infrastructure. Earth Engine combines a massive geospatial data catalog, planetary-scale computation, APIs, visualization, and machine-learning capabilities. Its catalog includes Landsat, Sentinel-2, MODIS and many other datasets. ([Google for Developers](https://developers.google.com/earth-engine?utm_source=chatgpt.com "Google Earth Engine  |  Google for Developers"))

Google itself describes Earth Engine as being used to **detect changes, map trends, and quantify differences on Earth's surface**. ([Google Earth Engine](https://earthengine.google.com/?hl=pl&utm_source=chatgpt.com "Google Earth Engine"))

So your instinct is right:

> **If we simply reproduce Google Earth Engine, we're building a weaker version of something that already exists.**

But that does **not** mean your project is meaningless.

It means we need to move **one level above Earth Engine**.

---

# First: What exactly is Google Earth Engine?

Think of it like this:

```text
                  GOOGLE EARTH ENGINE

       ┌──────────────────────────────────┐
       │       HUGE EARTH DATA CATALOG    │
       │                                  │
       │ Landsat                          │
       │ Sentinel-1 / Sentinel-2          │
       │ MODIS                            │
       │ Climate data                     │
       │ Terrain                          │
       │ Land cover                       │
       │ Demographics                     │
       │ etc.                             │
       └────────────────┬─────────────────┘
                        ↓
       ┌──────────────────────────────────┐
       │      PLANETARY COMPUTE           │
       │                                  │
       │ filtering                        │
       │ compositing                      │
       │ NDVI                             │
       │ classification                   │
       │ statistics                       │
       │ change analysis                  │
       │ ML                               │
       └────────────────┬─────────────────┘
                        ↓
       ┌──────────────────────────────────┐
       │       VISUALIZATION / EXPORT     │
       └──────────────────────────────────┘
```

Google describes it as essentially **data + computation + APIs + applications** for large-scale geospatial analysis. ([Google for Developers](https://developers.google.com/earth-engine?utm_source=chatgpt.com "Google Earth Engine  |  Google for Developers"))

And its scale is enormous. Google currently describes the catalog as having **90+ petabytes of analysis-ready geospatial data and 1,000+ curated datasets**, including imagery going back decades. ([Google Cloud](https://cloud.google.com/earth-engine?hl=en&utm_source=chatgpt.com "Earth Engine | Google Cloud"))

So don't compete with that.

---

# The important question isn't "Can we do what GEE does?"

The better question is:

> **What does GEE make possible, but doesn't itself solve for the person who actually wants an answer?**

And this is where I think your original idea becomes much more interesting.

---

# There is a huge gap between

### "Here is satellite data"

and

### "Tell me what happened here, when it happened, and what evidence exists about why."

Those are very different problems.

Imagine a user types:

> **Bengaluru**

Your proposed system could eventually produce:

```text
BENGALURU
──────────────────────────────────────

2016 → 2020 → 2024 → 2026

      SATELLITE OBSERVATIONS
              ↓
       ALIGN / REGISTER
              ↓
        CHANGE MAP
              ↓
     ┌────────────────────┐
     │  + 183 km² built   │
     │  - 47 km² vegetation│
     │  + 12 km² water     │
     └────────────────────┘
              ↓
       WHERE DID IT HAPPEN?
              ↓
        WHAT CHANGED?
              ↓
       WHAT DOCUMENTED
       EVENTS COINCIDE?
              ↓
       RESEARCH / NEWS /
       GOVERNMENT / PAPERS
              ↓
       EVIDENCE GRAPH
```

**That is substantially different from "we used Earth Engine to calculate NDVI."**

---

# Your actual contribution could be the missing layer

I'd redefine the project as:

## **An AI-powered Earth Change Investigation System**

Not:

> AI satellite image classifier

Not:

> Google Earth clone

Not:

> another NDVI dashboard

Not:

> another U-Net segmentation project

But:

> **A system that converts multi-temporal Earth observations into evidence-backed investigations of environmental and land-use change.**

That is much more interesting.

---

# Think of the stack this way

Google Earth Engine is infrastructure.

Your system is an **investigator sitting on top of infrastructure**.

```text
                    USER
                     │
                     ▼
              "Bengaluru"
                     │
                     ▼
        ┌─────────────────────────┐
        │  EARTH INVESTIGATOR AI  │
        └────────────┬────────────┘
                     │
       ┌─────────────┼──────────────┐
       ▼             ▼              ▼
   Satellite      Computer       Internet
   Retrieval      Vision         Research
       │             │              │
       ▼             ▼              ▼
   Sentinel       Register       Papers
   Landsat        Segment        News
   etc.           Compare        Reports
                  NDVI           Government
                     │              │
                     └──────┬───────┘
                            ▼
                    EVIDENCE GRAPH
                            │
                            ▼
                    HUMAN-READABLE
                     INVESTIGATION
```

Earth Engine can provide some of the raw material.

**Your project determines how to turn it into an investigation.**

---

# And there is another important insight

You were worried:

> "What if everything we want to do has already been done?"

Almost everything individually **has** been done.

That's normal in engineering research.

For example:

- U-Net already exists.
    
- SIFT already exists.
    
- RANSAC already exists.
    
- NDVI already exists.
    
- satellite change detection already exists.
    
- Google Earth Engine already exists.
    
- web search already exists.
    
- LLMs already exist.
    

Your contribution doesn't have to be inventing a new mathematical algorithm.

It can be:

> **a new system architecture that combines existing capabilities to solve a problem in a way that existing tools don't.**

That's legitimate engineering research.

---

# But I would change one thing about your current idea

Right now you have something like:

> Search Bengaluru → find images → align them → compare → heatmap → U-Net → NDVI → research agent.

That's cool.

But **don't make arbitrary internet-image registration the central scientific contribution.**

That's technically dangerous.

Two Google Images results might be:

- different cameras
    
- different viewpoints
    
- different seasons
    
- different atmospheric conditions
    
- different resolutions
    
- different years
    
- cropped
    
- rotated
    
- perspective-distorted
    
- partially occluded
    
- completely unrelated
    

Your registration algorithm could produce a visually convincing but scientifically meaningless alignment.

That is a research problem in itself.

So I'd make the system explicitly distinguish:

### Scientific mode

```text
Sentinel-2
Landsat
other georeferenced EO datasets
        ↓
reproducible comparison
```

### Experimental visual mode

```text
Internet imagery
        ↓
CV registration
        ↓
confidence score
        ↓
ACCEPT / REJECT
```

That's actually much stronger.

---

# And here is where your computer vision contribution becomes meaningful

Instead of claiming:

> "Our system aligns images."

Measure it.

For example:

### Registration benchmark

Take 100 image pairs.

Introduce:

- rotation
    
- scaling
    
- translation
    
- cropping
    
- mild perspective distortion
    
- different image resolutions
    

Then evaluate:

|Metric|Result|
|---|--:|
|Feature matching success|91%|
|RANSAC inlier ratio|74%|
|Registration RMSE|2.8 px|
|Successful registration|87%|
|Incorrect alignment rejection|94%|

Now you have an actual **experiment**.

And your system can say:

> "These images cannot be reliably registered."

That's far more scientifically respectable than forcing every pair into a heatmap.

---

# But I think there is an even bigger opportunity

Your original idea contains something much more ambitious:

## **What changed vs. Why did it change?**

Satellite imagery is very good at answering:

> **WHAT changed?**

For example:

```text
Forest
   ↓
Built-up
```

or

```text
Vegetation ↓
Built-up ↑
```

But imagery alone usually cannot establish:

> **WHY?**

Suppose your system detects:

```text
2017 → 2026

Built-up area:
+38 km²
```

Your AI agent could then investigate:

```text
Detected change
       ↓
Search geographic area
       ↓
Government planning documents
       ↓
Scientific literature
       ↓
News archives
       ↓
Infrastructure databases
       ↓
Population/economic data
       ↓
Cross-check evidence
       ↓
Possible explanations
```

And importantly:

### It shouldn't say:

> "Company X caused the environmental damage."

unless the evidence actually establishes that.

Instead:

```text
OBSERVED
────────────
Built-up land increased by X km².

DOCUMENTED
────────────
A major infrastructure project began
in this area during 2019–2022.

SCIENTIFIC EVIDENCE
───────────────────
Studies report that urban expansion
in this region is associated with...

CORRELATION
───────────
The spatial and temporal patterns overlap.

UNCONFIRMED
───────────
The available evidence does not establish
that event X caused the entire observed change.
```

**That evidence discipline could become one of your strongest contributions.**

---

# Now imagine the UI

This could be genuinely impressive.

User enters:

> **Bengaluru**

And gets:

### EARTH TIMELINE

```text
2015 ───── 2017 ───── 2019 ───── 2021 ───── 2023 ───── 2026
  │          │          │          │          │          │
  🌍         🌍         🌍         🌍         🌍         🌍
```

Then:

### CHANGE MAP

```text
         BENGALURU

       ┌──────────────┐
       │ ░░░▓▓▓▓      │
       │ ░░▓████▓     │
       │ ░▓██████▓    │
       │ ░░▓███▓      │
       │    ░░        │
       └──────────────┘

       Change detected
       126.4 km²
```

Then:

### WHAT CHANGED?

```text
Built-up     + 82.1 km²
Vegetation   - 61.3 km²
Agriculture  - 17.4 km²
Water        -  2.1 km²
```

Then:

### INVESTIGATION

```text
Why might this area have changed?

Evidence found:

● Urban expansion documented in...
● Infrastructure development reported in...
● Population growth reported in...
● Land-use planning document...
● Scientific study...
```

Then:

### EVIDENCE GRAPH

```text
                  Population
                      │
                      ▼
              Urban expansion
                 /        \
                ▼          ▼
          Construction   Roads
                │          │
                └────┬─────┘
                     ▼
             Land-cover change
                     │
                     ▼
              Satellite evidence
```

That is no longer simply a remote-sensing classifier.

---

# And there is a societal purpose

You don't need to claim:

> "Our project will save the planet."

That's too broad.

A much more defensible contribution is:

> **Reduce the amount of expertise and manual effort required to investigate geographically localized environmental change.**

For example, an environmental researcher shouldn't have to manually:

1. find satellite imagery,
    
2. download scenes,
    
3. preprocess them,
    
4. remove clouds,
    
5. align images,
    
6. calculate changes,
    
7. calculate area statistics,
    
8. search historical records,
    
9. search scientific literature,
    
10. connect the evidence,
    
11. explain the findings.
    

Your system could compress that into:

> **Search → Observe → Measure → Investigate.**

That is a meaningful engineering objective.

---

# And now your project has a very clean research question

I'd seriously consider making this your central question:

> **Can an AI-driven geospatial system automatically transform multi-temporal Earth observations into quantitative, spatially explicit, and evidence-backed investigations of environmental change?**

That's a much stronger research question than:

> "Can we classify satellite images using U-Net?"

Because U-Net is merely one component.

---

# Your contribution could have 4 layers

## 1. Computer Vision

Your team actually implements:

- feature detection
    
- feature matching
    
- RANSAC
    
- homography/affine transformation
    
- image registration
    
- image warping
    
- change detection
    

**Contribution:** robust image comparison.

---

## 2. Deep Learning

Implement:

- U-Net
    
- land-cover segmentation
    
- NDVI integration
    
- class statistics
    
- geographic generalization
    

**Contribution:** semantic interpretation of the observed change.

---

## 3. Geospatial Intelligence

Combine:

- time
    
- coordinates
    
- imagery
    
- land-cover
    
- area statistics
    
- transition matrices
    

**Contribution:** convert pixels into geographically meaningful events.

---

## 4. AI Research Agent

Search:

- scientific papers
    
- government sources
    
- historical documents
    
- news
    
- public datasets
    

and construct:

```text
Observation
     ↓
Evidence
     ↓
Context
     ↓
Possible explanation
     ↓
Confidence / uncertainty
```

**Contribution:** bridge Earth observation with external evidence.

---

# That's where I think your project becomes defensible

Not:

> "We invented satellite image analysis."

Instead:

> **"Existing platforms provide extraordinary Earth observation data and planetary-scale computation. Our project explores a higher-level system that combines computer vision, semantic segmentation, temporal analysis, and evidence retrieval to turn those observations into localized, explainable investigations of environmental change."**

That's honest.

And importantly, you're **not pretending Google Earth Engine doesn't exist.**

You're using it.

---

# In fact, I would proudly put GEE in your architecture

Something like:

```text
                    OUR SYSTEM
                         │
          ┌──────────────┴──────────────┐
          │                             │
    EARTH ENGINE                  EXTERNAL WEB
          │                             │
   Satellite data                 Research/news
   Landsat                        Government docs
   Sentinel                       Scientific papers
   MODIS                          Public information
          │                             │
          └──────────────┬──────────────┘
                         ↓
                 OUR AI/CV ENGINE
                         │
            ┌────────────┼────────────┐
            ↓            ↓            ↓
        REGISTER      SEGMENT      ANALYZE
            │            │            │
            └────────────┼────────────┘
                         ↓
                  CHANGE DETECTION
                         ↓
                  EVIDENCE AGENT
                         ↓
                 EARTH INVESTIGATION
```

That makes GEE a **dependency/data infrastructure**, not your competitor.

---

# There's also an important reality check

You said:

> "without which our project won't be meaningful"

I would change that standard.

A college project does **not** have to solve a problem that nobody on Earth has solved.

It needs to demonstrate:

**1. A real problem**

**2. A defensible technical approach**

**3. An implementation**

**4. Evaluation**

**5. A measurable contribution**

**6. An honest discussion of limitations**

In fact, saying:

> "Google Earth Engine already provides planetary-scale processing, so we deliberately do not attempt to reproduce its infrastructure. Instead, we investigate the problem of converting heterogeneous Earth observations into explainable, evidence-backed change investigations."

would make your project sound **more mature**, not less.

---

# And there's a beautiful distinction you can use

### Google Earth Engine asks:

> **"What can we compute from Earth's data?"**

Your system asks:

> **"What happened here, when did it happen, what can we measure about it, and what evidence exists to help explain it?"**

That is the direction I'd take.

And then your slogan **"See what changed. Understand why."** suddenly has an actual technical architecture behind it.

The **"understand why"** part should never be presented as automatic causal truth—it is an evidence-retrieval and hypothesis-generation layer with explicit uncertainty.

---

## One final thing: don't throw away your existing work

Your existing pieces actually fit beautifully:

|Existing idea|New role|
|---|---|
|Sentinel/Landsat|Earth observations|
|Google Earth Engine|Data infrastructure|
|SIFT/ORB|Image registration|
|RANSAC|Geometric robustness|
|Homography|Image alignment|
|Difference maps|Change detection|
|U-Net|Semantic interpretation|
|NDVI|Environmental indicator|
|Connected components|Spatial patterns|
|Web search|Evidence retrieval|
|LLM|Investigation/synthesis|
|React|Investigation interface|
|FastAPI|Orchestration|
|PostGIS|Spatiotemporal archive|

So I **wouldn't restart the project**.

I'd change its **center of gravity**.

From:

> **"We built an AI system that analyzes satellite imagery."**

to:

> **"We built an AI Earth Investigator that observes, measures, and researches changes in the physical world."**

That is a project you can actually spend the next 11 weeks building—and defend without pretending that Google, NASA, ESA, or decades of remote-sensing research don't exist.