Yes. **Earth observation / satellite-image analysis is a much more defensible direction** than generic exam-hall proctoring, especially for your Phase 1 literature survey.

The important part is to **not make the topic simply “satellite image analysis.”** That is too broad. Keep the broad domain, then identify a specific CV/deep-learning problem after the literature survey.

### Why your reasoning is strong

|Exam-hall proctoring|Earth observation CV|
|---|---|
|Human behavior is difficult to label consistently|Large public satellite datasets exist|
|Head pose/gaze/body movement can be ambiguous|Many measurable visual phenomena|
|Often need your own classroom recordings|Sentinel/Landsat and other open imagery|
|Privacy/consent issues|Public Earth-observation data|
|Occlusion between students|Multiple spectral/spatial modalities|
|Hard to reproduce realistic cheating scenarios|Easier to reproduce experiments|
|Narrow application|Agriculture, forests, water, urbanization, disasters, pollution proxies, etc.|
|Mostly person detection + pose + temporal analysis|Detection, segmentation, classification, change detection, multimodal fusion, time-series analysis|

And importantly, **you don't have to abandon deep learning/CV at all**. Earth observation gives you a huge space to apply modern CV techniques.

### The direction I'd propose

Instead of:

> **AI-Based Computer Vision for Automated Inspection Using Deep Learning**

move toward something like:

> **Deep Learning-Based Computer Vision for Earth Observation and Environmental Analysis**

or, slightly more research-oriented:

> **AI-Based Earth Observation Using Deep Learning for Automated Environmental Monitoring**

Then your literature survey can investigate different problems:

- **Land-cover classification** — forest, desert, water, urban, agriculture, etc.
    
- **Land-use/land-cover change detection** — detect how an area changes over time.
    
- **Deforestation detection**
    
- **Urban expansion monitoring**
    
- **Water-body detection and monitoring**
    
- **Flood detection**
    
- **Wildfire/burn-scar mapping**
    
- **Agricultural/crop monitoring**
    
- **Coastal change**
    
- **Mining/quarry detection**
    
- **Desertification**
    
- **Glacier/ice change**
    
- **Marine/environmental monitoring**
    
- **Disaster damage assessment**
    
- **Multispectral/hyperspectral image analysis**
    
- **Satellite-image super-resolution**
    
- **Cloud removal/cloud detection**
    
- **Multi-temporal Earth observation**
    
- **3D terrain/environment reconstruction**
    

This is where your idea becomes much more interesting: **the project isn't necessarily about one environment. The underlying problem can be a general CV capability that is applied to Earth observation.**

For example:

> **“Deep Learning-Based Multi-Temporal Change Detection in Satellite Imagery for Automated Environmental Monitoring.”**

Now you have a genuine research question:

**Given satellite images of the same geographical region at different times, can a deep-learning model automatically identify meaningful environmental changes?**

That could potentially detect:

`forest → cleared land`  
`land → urban development`  
`normal river → flooded river`  
`vegetation → drought/stressed vegetation`  
`coastline → erosion`  
`bare land → mining activity`

And you can start with one specific application for the prototype while keeping the underlying system general.

### The biggest advantage for your project

You can build the project progressively.

**Phase 1 — Literature survey**

Study ~10–20 papers covering:

`Satellite imagery → CNN/ViT → segmentation → classification → change detection → multispectral → temporal models`

**Phase 2 — Choose one gap**

For example:

> Existing models perform well on known datasets but struggle when imagery comes from different geographical regions, seasons, sensors, or resolutions.

Then your project could become:

> **Domain-Generalized Deep Learning for Environmental Change Detection in Satellite Imagery**

That's substantially more research-oriented than:

> “We made a YOLO model that detects students looking sideways.”

### And your dataset argument is valid

You have access to major open Earth-observation sources such as **Sentinel-1, Sentinel-2 and Landsat**, which gives you RGB, multispectral, SAR and temporal imagery depending on the problem.

That also opens up a much more interesting stack:

**Python → PyTorch → OpenCV → NumPy → Rasterio/GDAL → GeoPandas → segmentation/change-detection models → Sentinel/Landsat → FastAPI/Streamlit**

You could eventually make a small interface where someone selects an area and gets something like:

```text
AREA: 25 km²

Forest loss       8.4%
Urban expansion   3.1%
Water change      12.7%
Vegetation stress 6.8%

Detected changes:
██████████████████ Forest → Bare land
██████████         Agriculture → Urban
████                 Water expansion
```

That gives you **CV + AI + deep learning + geospatial data + a demonstrable application**, without requiring you to collect hundreds of hours of human behavior footage.

### One caution

Don't tell your faculty:

> “We chose satellite imagery because the datasets are easier.”

Instead, frame the motivation academically:

> **“We propose to investigate deep-learning-based computer vision methods for automated Earth observation, with emphasis on extracting and monitoring environmental changes from publicly available multi-temporal satellite imagery.”**

Then your literature survey determines the exact research problem.

**I think this is a much better direction for your group than locking yourselves into exam-hall proctoring.**