Yes. I did a literature survey focused specifically on **deep-learning computer vision for Earth observation, satellite change detection, foundation models, domain shift, and environmental monitoring**.

My conclusion is that you can **keep your registered topic exactly as it is** and add a much more specific second line underneath it. More importantly, there is a credible research gap that is both **useful and realistically implementable**.

## 1. Keep the official topic unchanged

Your submitted topic:

> **AI-Based Computer Vision for Automated Inspection Using Deep Learning**

Add this underneath:

> **Application Focus: Automated Earth Observation and Environmental Change Analysis Using Multi-Temporal Satellite Imagery**

I would use exactly that for Phase 1.

It doesn't contradict the original topic:

**Computer Vision** → satellite imagery  
**Automated inspection** → automated inspection of Earth's surface  
**Deep Learning** → CNNs / Transformers / foundation models  
**Analysis** → environmental change detection and quantification

You can then tell your faculty:

> _The project investigates how deep-learning-based computer vision can be used to automatically inspect multi-temporal satellite imagery and identify, quantify and interpret significant changes in Earth's surface, with applications in environmental monitoring._

That gives you enormous freedom without changing the officially registered topic.

---

# 2. I think your strongest research direction is this

Don't make the project simply:

> "Detect deforestation using YOLO."

That's already a well-developed area.

Instead:

> **Generalizable, label-efficient, multi-temporal environmental change detection from satellite imagery.**

In simpler terms:

**Can an AI model learn what genuine environmental change looks like, rather than simply learning the visual appearance of one particular location/dataset?**

This is actually a current research problem.

---

# 3. Why ordinary satellite change detection isn't enough

Suppose you give a model:

**Image A — 2020**

**Image B — 2025**

and ask:

> "What changed?"

Sounds easy.

But the images may differ because of:

- different seasons
    
- different sunlight
    
- atmospheric conditions
    
- clouds/haze
    
- sensor differences
    
- different viewing angles
    
- vegetation cycles
    
- soil moisture
    
- image registration errors
    
- different geographic regions
    

The model may therefore report:

> **CHANGE DETECTED**

when nothing environmentally significant actually happened.

The literature calls these **pseudo-changes**.

Recent reviews explicitly identify atmospheric/radiometric variation, seasonal cycles, registration errors and sensor heterogeneity as major difficulties. ([DOI](https://doi.org/10.3390/rs18152573?utm_source=chatgpt.com "Change Detection in Remote Sensing Imagery: A Systematic Review of Statistical, Machine Learning, and Deep Learning Methods"))

And this is not merely an old problem.

A 2025 IEEE paper on **domain-agnostic change detection** specifically addresses the problem of models failing when the imagery comes from different domains. ([DOI](https://doi.org/10.1109/TMM.2025.3613179?utm_source=chatgpt.com "Generalization-Aware Remote Sensing Change Detection via Domain-Agnostic Learning"))

An AAAI 2026 paper reports that state-of-the-art remote-sensing change-detection models can suffer very large performance degradation—reported as **60–80%**—in unseen environments and imaging conditions. ([AAAI Publications](https://ojs.aaai.org/index.php/AAAI/article/view/38314?utm_source=chatgpt.com "Causal Decoupling Domain Generalization for Remote Sensing Change Detection | Proceedings of the AAAI Conference on Artificial Intelligence"))

That is a **very good research gap for you**.

---

# 4. The interesting research question

Your project could therefore ask:

> **How can deep-learning-based computer vision reliably detect genuine environmental changes in satellite imagery across different geographic regions, seasons and imaging conditions?**

Then your system isn't tied to:

- forests only
    
- cities only
    
- floods only
    
- agriculture only
    

Instead:

```text
                  MULTI-TEMPORAL EO DATA
                         │
              ┌──────────┴──────────┐
              │                     │
           SENTINEL              LANDSAT
              │                     │
              └──────────┬──────────┘
                         ↓
                  PREPROCESSING
                         ↓
                DEEP LEARNING MODEL
                         ↓
             CHANGE / NO-CHANGE MAP
                         ↓
             SEMANTIC INTERPRETATION
                         ↓
        ┌────────────────┼─────────────────┐
        ↓                ↓                 ↓
   VEGETATION          URBAN             WATER
      LOSS             GROWTH            CHANGE
        │                │                 │
        └────────────────┼─────────────────┘
                         ↓
               ENVIRONMENTAL REPORT
```

---

# 5. There is a very interesting technology you can actually use

This is where the project gets considerably more modern than ordinary "CNN on satellite images."

## Geospatial Foundation Models

NASA and IBM have released **Prithvi**, a geospatial foundation model specifically trained on satellite imagery.

The newer **Prithvi-EO-2.0** was trained on **4.2 million global time-series samples** from Harmonized Landsat-Sentinel-2 data and incorporates temporal and location information. It is designed to transfer to different Earth-observation tasks. ([Hugging Face](https://huggingface.co/papers/2412.02732?utm_source=chatgpt.com "Paper page - Prithvi-EO-2.0: A Versatile Multi-Temporal Foundation Model for Earth Observation Applications"))

The architecture is particularly relevant to your idea because it isn't simply:

> image → CNN → classification

It uses a Vision Transformer / masked-autoencoder approach and represents **spatiotemporal satellite data**. ([Hugging Face](https://huggingface.co/ibm-nasa-geospatial/Prithvi-EO-2.0-600M?utm_source=chatgpt.com "ibm-nasa-geospatial/Prithvi-EO-2.0-600M · Hugging Face"))

NASA explicitly lists applications such as:

- flood mapping
    
- burn-scar mapping
    
- crop classification
    
- land-use monitoring
    
- ecosystem monitoring
    
- landslide detection
    
- biomass estimation
    

for the model. ([NASA Science](https://science.nasa.gov/science-research/ai-geospatial-model-earth/?utm_source=chatgpt.com "Expanded AI Model with Global Data Enhances Earth Science Applications  - NASA Science"))

So you would be working with **actual current Earth-observation AI research**, not an artificial "modern technology" bolted onto a basic project.

---

# 6. And there is a second research gap: labels

This is another excellent area.

Traditional deep-learning change detection often requires huge quantities of labelled pixel-level data.

But creating:

```text
pixel 1 = changed
pixel 2 = unchanged
pixel 3 = changed
...
```

for millions of satellite images is extremely expensive.

A 2025 review specifically devoted to **label-efficient deep-learning change detection** identifies:

- semi-supervised learning
    
- weak supervision
    
- self-supervised learning
    
- active learning
    
- few-shot learning
    
- unsupervised learning
    

as important directions because pixel-level annotation is expensive. ([Wiley Online Library](https://onlinelibrary.wiley.com/doi/10.1111/phor.70021?utm_source=chatgpt.com "Toward Label‐Efficient Deep Learning Change Detection for Remote Sensing Imagery: A Comprehensive Review - Peng - 2025 - The Photogrammetric Record - Wiley Online Library"))

Another 2025 survey similarly concludes that practical deployment is constrained by diverse inputs and limited labelled data. ([ResearchGate](https://www.researchgate.net/publication/388996939_A_Survey_of_Sample-Efficient_Deep_Learning_for_Change_Detection_in_Remote_Sensing_Tasks_strategies_and_challenges?utm_source=chatgpt.com "(PDF) A Survey of Sample-Efficient Deep Learning for Change Detection in Remote Sensing: Tasks, strategies, and challenges"))

That gives you another potential research question:

> **Can we achieve useful environmental change detection with substantially less labelled satellite data by leveraging pretrained Earth-observation models and self-supervised learning?**

That's much more research-oriented than simply training YOLO.

---

# 7. Third gap: multimodal Earth observation

This is another direction that I think is particularly promising.

You don't have to rely solely on RGB.

Satellite sensors can provide different kinds of information:

```text
Optical / RGB
     +
NIR
     +
SWIR
     +
SAR
     +
Temporal information
     ↓
MULTIMODAL EARTH REPRESENTATION
```

For example, **SAR can observe through clouds and in darkness**, whereas optical imagery can provide rich spectral information. Recent reviews identify multimodal RS change detection as an important future direction. ([IEEE Xplore](https://ieeexplore.ieee.org/document/11146768/?utm_source=chatgpt.com "Deep Learning-Based Change Detection in Remote Sensing: A Comprehensive Review | IEEE Journals & Magazine | IEEE Xplore"))

That creates a useful question:

> **Can optical + SAR information reduce false environmental-change detections caused by clouds, lighting and seasonal variation?**

That's genuinely interesting.

---

# 8. Fourth gap: don't just say "something changed"

This is where your environmental-awareness vision becomes powerful.

Traditional binary change detection:

```text
CHANGE
NO CHANGE
```

isn't enough.

Imagine:

```text
2012 → 2026

████████████████
       ↓
   CHANGE
```

The user wants:

> **What changed?**

So you move toward **semantic change detection**:

```text
Forest
   ↓
Bare land

Agriculture
   ↓
Urban

Water
   ↓
Bare land

Bare land
   ↓
Vegetation
```

Recent literature explicitly identifies **binary, multiclass and semantic change detection** as different research tasks. ([IEEE Xplore](https://ieeexplore.ieee.org/document/11205282/?utm_source=chatgpt.com "Deep Learning for High-Resolution Remote Sensing Change Detection: Task Taxonomy, Datasets, and Perspectives | IEEE Journals & Magazine | IEEE Xplore"))

That is much closer to your eventual OSINT vision.

---

# 9. Put all four together

Now your potential project becomes:

### Core problem

> **Reliable semantic environmental change detection from multi-temporal satellite imagery under geographic, seasonal and sensor/domain variation, with limited labelled data.**

And your potential approach:

```text
                 SENTINEL / LANDSAT
                        │
                        ↓
               MULTI-TEMPORAL DATA
                        │
                        ↓
             PRETRAINED EO FOUNDATION
                    MODEL
                 (Prithvi)
                        │
                        ↓
              CHANGE DETECTION MODEL
                        │
              ┌─────────┴─────────┐
              ↓                   ↓
       CHANGE LOCALIZATION    CHANGE TYPE
              │                   │
              └─────────┬─────────┘
                        ↓
                 CONFIDENCE /
                 UNCERTAINTY
                        ↓
              ENVIRONMENTAL MAP
                        ↓
                PUBLIC DASHBOARD
```

You **do not need to implement all of this**.

That is the research space.

Your actual project can select one manageable contribution.

---

# 10. What I'd actually recommend you build

Given that this is a college project and you need something demonstrable, I'd choose:

## **Domain-Generalized Semantic Change Detection**

### Prototype

Input:

```text
Location A
2020 satellite image
+
2026 satellite image
```

Output:

```text
                CHANGE MAP

Forest → Urban       4.8 km²
Forest → Bare        1.2 km²
Water → Land         0.4 km²
Urban expansion      7.3 km²

Confidence:
Forest→Urban         93%
Forest→Bare          87%
Water→Land           61%
```

Then test the model on **a different geographical region that wasn't used during training**.

That last part is crucial.

Instead of saying:

> "Our model achieved 96% accuracy on the dataset."

you can say:

> "Our model was trained on Region A and evaluated on previously unseen Region B to measure geographic generalization."

That is much more meaningful.

---

# 11. You have plenty of genuine datasets

This isn't a project where you'll spend three months collecting data.

Sentinel-2 provides global multispectral imagery with a designed revisit frequency of about five days at the equator, and its applications include land monitoring, agriculture, forestry, climate change and disaster management. ([Copernicus Data Space Ecosystem](https://dataspace.copernicus.eu/data-collections/copernicus-sentinel-missions/sentinel-2?utm_source=chatgpt.com "Sentinel-2 | Copernicus Data Space Ecosystem"))

There are established research datasets as well.

For example, **S2Looking** contains 5,000 bitemporal image pairs and more than 65,920 annotated change instances, deliberately introducing difficult viewing-angle and illumination variation. ([MDPI](https://www.mdpi.com/2072-4292/13/24/5094?utm_source=chatgpt.com "S2Looking: A Satellite Side-Looking Dataset for Building Change Detection"))

You also have established datasets such as LEVIR-CD and other change-detection benchmarks covered extensively by recent surveys.

So your concern about finding data is basically solved.

---

# 12. The literature progression is actually excellent for your Phase 1

You can structure your first 10 papers approximately like this:

|Area|What you learn|
|---|---|
|Traditional remote-sensing change detection|Problem foundations|
|CNN/Siamese CD|Baseline deep learning|
|BIT|Transformers for temporal/spatial context|
|ChangeFormer|Transformer-based Siamese architecture|
|S2Looking|Difficult real-world imaging conditions|
|Domain adaptation|Handling distribution shifts|
|Domain generalization|Generalizing to unseen regions|
|Label-efficient CD|Reducing annotation requirements|
|Multimodal CD|Optical + SAR/etc.|
|Prithvi-EO|Modern geospatial foundation models|

For example, **BIT** introduced a bitemporal Transformer specifically to model spatial-temporal context efficiently. ([arXiv](https://arxiv.org/abs/2103.00208?utm_source=chatgpt.com "Remote Sensing Image Change Detection with Transformers"))

**ChangeFormer** subsequently used a Transformer-based Siamese architecture for multi-scale long-range change detection. ([arXiv](https://arxiv.org/abs/2201.01293?utm_source=chatgpt.com "A Transformer-Based Siamese Network for Change Detection"))

Then the field moved toward:

**Transformers → domain generalization → label efficiency → multimodal learning → geospatial foundation models.**

That's an excellent literature-survey storyline.

---

# 13. One thing I would NOT claim

Don't make your academic project:

> **"AI that predicts Earth's future catastrophes."**

That's too broad and scientifically difficult.

Satellite CV can **observe and quantify indicators**, but predicting something like:

> "This region will become environmentally catastrophic in 15 years"

requires climate models, causal relationships, socioeconomic variables, weather data, hydrology, etc.

Instead:

### What your CV system can legitimately do

**Observe**

> Forest decreased 14%.

**Detect**

> New built-up region appeared.

**Compare**

> Vegetation changed significantly between 2010 and 2026.

**Quantify**

> 23 km² of land-cover transition detected.

**Track**

> Change trajectory over multiple years.

**Flag**

> Region exhibits abnormal environmental change.

Then, potentially later:

**Risk estimation**

> Region shows indicators associated with increased flood/fire/deforestation risk.

That is much more scientifically defensible.

---

# 14. And this connects directly to your huge OSINT idea

Your college prototype could be:

> **AI-based environmental change detector**

But the eventual platform could become:

> **Earth OSINT — an open environmental intelligence system**

with:

```text
                 EARTH OSINT
                     │
        ┌────────────┼────────────┐
        ↓            ↓            ↓
     FOREST        URBAN         WATER
        ↓            ↓            ↓
    DEFOREST.      SPRAWL       FLOOD
        │            │            │
        └────────────┼────────────┘
                     ↓
              MULTI-TEMPORAL AI
                     ↓
              CHANGE DETECTION
                     ↓
              ENVIRONMENTAL
                 INDICATORS
                     ↓
              HUMAN-READABLE
                  EVIDENCE
```

That is where your original vision of **showing people what is happening to Earth** fits.

---

# 15. My recommendation for the actual project framing

### Official topic

> **AI-Based Computer Vision for Automated Inspection Using Deep Learning**

### Subtopic

> **Application Focus: Automated Earth Observation and Environmental Change Analysis Using Multi-Temporal Satellite Imagery**

### Problem statement

> **To develop a deep-learning-based computer vision system capable of detecting, quantifying and semantically interpreting environmental changes from multi-temporal satellite imagery, with emphasis on robustness to geographic, seasonal and imaging variations.**

### Research direction

> **Domain-generalized and label-efficient semantic change detection using modern Earth-observation foundation models.**

### Long-term vision

> **An open environmental OSINT platform that converts satellite observations into accessible evidence of planetary change.**

---

## The important conclusion from the literature survey

**Yes, there is a real research problem here.**

But I would **not** try to invent a completely new CV architecture.

The smarter contribution for your team is:

**Existing CV capability:** satellite change detection  
↓  
**Existing technology:** Transformers / foundation models  
↓  
**Known weakness:** geographic/domain shift + seasonal pseudo-change + expensive labels  
↓  
**Your contribution:** improve robustness/generalization and semantic interpretation  
↓  
**Application:** environmental monitoring  
↓  
**Interface:** public Earth-OSINT visualization

That gives you a project that is simultaneously **CV research + deep learning + satellite data + modern foundation models + environmental usefulness**, while remaining compatible with the topic you already submitted.

And the literature is current enough that you can genuinely discuss **2025–2026 research**, rather than building a project around an outdated CNN-only approach. Recent reviews specifically identify **label-efficient learning, multimodal change detection, lightweight models, foundation-model-assisted change detection, and vision-language approaches** as active directions. ([DOI](https://doi.org/10.3390/rs18152573?utm_source=chatgpt.com "Change Detection in Remote Sensing Imagery: A Systematic Review of Statistical, Machine Learning, and Deep Learning Methods"))

**One particularly strong candidate for us to investigate next is:**

> **“Can Prithvi-EO-2.0 + a lightweight change-detection head generalize to environmental changes in geographic regions it was never trained on?”**

That is concrete enough to become an actual experiment, rather than just a big website idea.