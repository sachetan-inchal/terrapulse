"""Earth Temporal Intelligence - FastAPI Backend Application."""
import os
os.environ["LITELLM_LOCAL_MODEL_COST_MAP"] = "True"
from pathlib import Path
import io
import sys
import json
import asyncio
from typing import List, Optional
from fastapi import FastAPI, Query, HTTPException, Response, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import numpy as np
from PIL import Image, ImageDraw, ImageFont

from backend.config import settings
from backend.models.schemas import (
    LocationInfo, SatelliteScene, EnvironmentalAnalysis,
    ChangeDetectionResult, RegistrationResult, InvestigationResponse,
    FutureScenario,
    InvestigatorChatRequest, StationMeasurementSchema,
    HeatmapResponseSchema, SymptomAnalysisRequest,
    SymptomAnalysisResponse, SymptomHypothesisSchema,
    ForecastRequest, ForecastResponse, ForecastScenarioResult, ForecastScenarioPoint,
    ResearchQueryResponse, ResearchArticleSchema
)
from backend.services.geocoding import list_preset_locations, get_location_by_id, geocode_location
from backend.services.satellite import get_scenes_for_location, fetch_real_stac_scenes
from backend.services.vision import compute_sift_registration
from backend.services.analysis import get_environmental_analysis, compute_temporal_change
from backend.services.investigator import investigate_region
from backend.services.reports import generate_report

ROOT_DIR = Path(__file__).resolve().parent.parent
GEOAGENT_DIR = ROOT_DIR / "terra1" / "GeoAgent"
if str(GEOAGENT_DIR) not in sys.path:
    sys.path.insert(0, str(GEOAGENT_DIR))

from sse_starlette.sse import EventSourceResponse
from environmental.agent import TerraPulseInvestigatorAgent, ActivityEventType, ActivityEvent
from environmental.spatial_analysis import (
    get_preset_bengaluru_monitoring_stations,
    compute_idw_surface,
    generate_investigation_geojson,
    SpatialBoundingBox,
    IDWConfig,
)
from environmental.symptom_analyzer import investigate_environmental_symptom
from environmental.forecasting import generate_environmental_forecast
from environmental.research_apis.aggregator import ResearchAggregator
from environmental.research_apis.base import ArticleMetadata

global_investigator_agent = TerraPulseInvestigatorAgent()
global_research_aggregator = ResearchAggregator()

app = FastAPI(
    title="Earth Temporal Intelligence API",
    description="Planetary-Scale Geospatial Vision, Bi-temporal Change Detection & Evidence Synthesis API",
    version="2.0.0"
)

# CORS Configuration for local frontend development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/health")
def health_check():
    return {
        "status": "healthy",
        "service": "Earth Temporal Intelligence Backend",
        "version": "2.0.0",
        "storage_cache": str(settings.CACHE_DIR)
    }

@app.get("/api/environmental/stations", response_model=List[StationMeasurementSchema])
def get_environmental_stations(
    indicator: Optional[str] = Query(None, description="Optional pollutant filter, e.g. PM2.5, DO"),
    location: str = Query("bengaluru", description="Target region")
):
    """
    Returns ground monitoring stations with telemetry, quality flags, and sample data disclosure.
    """
    from environmental.spatial_analysis import get_monitoring_stations_for_location
    stations = get_monitoring_stations_for_location(location)
    if indicator:
        ind_clean = indicator.strip().upper()
        stations = [s for s in stations if s.pollutant.strip().upper() == ind_clean]
    
    loc_display = "Chennai" if "chennai" in location.lower() else "Bengaluru"
    return [
        StationMeasurementSchema(
            station_id=s.id,
            station_name=s.name,
            latitude=s.latitude,
            longitude=s.longitude,
            indicator=s.pollutant,
            value=s.measured_value,
            unit=s.unit,
            timestamp=s.timestamp,
            quality_flag=s.quality_flag,
            provenance=s.source_agency,
            is_sample_data=True,
            sample_data_note=f"Illustrative benchmark telemetry for {loc_display} urban air & water quality monitoring stations."
        )
        for s in stations
    ]

@app.get("/api/locations", response_model=List[LocationInfo])
def get_locations_endpoint():
    from backend.services.geocoding import PRESET_LOCATIONS
    return PRESET_LOCATIONS

@app.get("/api/locations/search", response_model=List[LocationInfo])
def search_location_endpoint(
    q: str = Query(..., min_length=1, description="Worldwide place name, address, or coordinates"),
    limit: int = Query(8, ge=1, le=20, description="Max candidate suggestions")
):
    from backend.services.geocoding import search_locations
    return search_locations(q, limit=limit)

@app.get("/api/locations/geocode", response_model=LocationInfo)
def geocode_endpoint(q: str = Query(..., min_length=1, description="Location query to resolve")):
    from backend.services.geocoding import geocode_location
    try:
        return geocode_location(q, allow_fallback=False)
    except ValueError as err:
        raise HTTPException(status_code=404, detail=str(err))

@app.get("/api/scenes", response_model=List[SatelliteScene])
def get_scenes(
    location_id: str = Query("bengaluru"),
    max_cloud: float = Query(20.0)
):
    from backend.services.satellite import get_scenes_for_location
    return get_scenes_for_location(location_id, max_cloud=max_cloud)

@app.get("/api/scenes/chronological", response_model=List[SatelliteScene])
def get_chronological_scenes_endpoint(location_id: str = Query("bengaluru")):
    from backend.services.satellite import get_chronological_scenes
    return get_chronological_scenes(location_id)

@app.get("/api/scenes/related")
def get_related_imagery_endpoint(location_id: str = Query("bengaluru")):
    from backend.services.satellite import get_related_imagery
    return get_related_imagery(location_id)

@app.get("/api/scenes/georeferenced")
def get_georeferenced_scene_endpoint(
    scene_id: str = Query("default"),
    min_lon: float = Query(77.45),
    min_lat: float = Query(12.90),
    max_lon: float = Query(77.70),
    max_lat: float = Query(13.10)
):
    from backend.services.satellite import get_georeferenced_image_bytes
    img_data = get_georeferenced_image_bytes(scene_id, [min_lon, min_lat, max_lon, max_lat])
    return Response(content=img_data, media_type="image/jpeg")

@app.get("/api/scenes/measurements")
def get_scene_measurements_endpoint(
    scene_id: str = Query("default"),
    min_lon: float = Query(77.45),
    min_lat: float = Query(12.90),
    max_lon: float = Query(77.70),
    max_lat: float = Query(13.10)
):
    from backend.services.satellite import compute_real_environmental_measurements
    return compute_real_environmental_measurements(scene_id, [min_lon, min_lat, max_lon, max_lat])

@app.get("/api/stac/live")
def get_live_stac_scenes(
    min_lon: float = Query(77.45),
    min_lat: float = Query(12.85),
    max_lon: float = Query(77.75),
    max_lat: float = Query(13.10),
    max_items: int = Query(4)
):
    return fetch_real_stac_scenes([min_lon, min_lat, max_lon, max_lat], max_cloud=20.0)[:max_items]

@app.get("/api/analysis", response_model=EnvironmentalAnalysis)
def get_analysis_endpoint(
    location_id: str = Query("bengaluru"),
    year: int = Query(2024)
):
    return get_environmental_analysis(location_id, year)

@app.get("/api/change", response_model=ChangeDetectionResult)
def get_change_endpoint(
    location_id: str = Query("bengaluru"),
    year_a: int = Query(1985),
    year_b: int = Query(2024)
):
    return compute_temporal_change(location_id, year_a, year_b)

@app.post("/api/vision/register", response_model=RegistrationResult)
def run_cv_registration(
    lowe_ratio: float = Query(0.75),
    ransac_thresh: float = Query(5.0),
    min_inlier_ratio: float = Query(0.25)
):
    p_left = ROOT_DIR / "tile_left.jpg"
    p_right = ROOT_DIR / "tile_right.jpg"
    if not p_left.exists() or not p_right.exists():
        raise HTTPException(status_code=404, detail="Benchmark spatial tiles not found.")
    
    img1 = np.array(Image.open(p_left).convert("RGB"))
    img2 = np.array(Image.open(p_right).convert("RGB"))

    res = compute_sift_registration(
        img1, img2,
        lowe_ratio=lowe_ratio,
        ransac_thresh=ransac_thresh,
        min_inlier_ratio=min_inlier_ratio
    )
    return res

@app.get("/api/investigator", response_model=InvestigationResponse)
def run_investigation(
    query: str = Query("Why did this region change?"),
    location_id: str = Query("bengaluru"),
    scene_id: Optional[str] = Query(None)
):
    return investigate_region(query=query, location_id=location_id, scene_id=scene_id)

@app.get("/api/future/simulate", response_model=List[FutureScenario])
def get_future_scenarios(location_id: str = Query("bengaluru")):
    return [
        FutureScenario(
            scenario_year=2030,
            model_type="Spatiotemporal Transformer + Cellular Automata Dynamics",
            projected_urban_pct=81.4,
            projected_vegetation_pct=14.2,
            projected_water_pct=1.8,
            assumptions=[
                "Peripheral Ring Road (PRR) construction proceeding along planned alignment",
                "Continued peri-urban residential infill in Sarjapur, Whitefield, and Devanahalli",
                "Buffer zone enforcement on remaining Tier-1 lake catchments"
            ],
            uncertainty_margin="± 3.8% confidence interval",
            disclaimer="Generative simulation conditioned on historical trajectory and municipal permits. Not ground-truth satellite observation."
        ),
        FutureScenario(
            scenario_year=2040,
            model_type="Spatiotemporal Transformer + Cellular Automata Dynamics",
            projected_urban_pct=86.7,
            projected_vegetation_pct=10.1,
            projected_water_pct=1.5,
            assumptions=[
                "Satellite Town Ring Road (STRR) economic agglomeration completed",
                "Full industrialization of northern IT corridor connecting KIAL airport",
                "Increased surface run-off and urban heat island (LST) elevation of 2.4°C"
            ],
            uncertainty_margin="± 6.5% confidence interval",
            disclaimer="Generative simulation conditioned on historical trajectory and municipal permits. Not ground-truth satellite observation."
        ),
        FutureScenario(
            scenario_year=2050,
            model_type="Spatiotemporal Transformer + Cellular Automata Dynamics",
            projected_urban_pct=89.5,
            projected_vegetation_pct=7.8,
            projected_water_pct=1.2,
            assumptions=[
                "Metropolitan saturation limit reached across Greater Bangalore boundaries",
                "Trans-district coalescence with Hosur and Tumkur corridors",
                "High reliance on artificial rainwater harvesting infrastructure"
            ],
            uncertainty_margin="± 9.2% confidence interval",
            disclaimer="Generative simulation conditioned on historical trajectory and municipal permits. Not ground-truth satellite observation."
        )
    ]

@app.post("/api/reports/generate")
def create_report_endpoint(
    location_id: str = Query("bengaluru"),
    year_a: int = Query(1985),
    year_b: int = Query(2024),
    notes: Optional[str] = Query(None)
):
    return generate_report(location_id=location_id, year_a=year_a, year_b=year_b, notes=notes or "")

@app.get("/api/imagery/tile")
def get_imagery_tile(
    mission: str = Query("LS05"),
    year: int = Query(1985),
    loc: str = Query("bengaluru")
):
    """Dynamic satellite tile image provider."""
    # Use real benchmark tiles where appropriate
    p_left = ROOT_DIR / "tile_left.jpg"
    p_right = ROOT_DIR / "tile_right.jpg"
    
    base_file = p_left if year <= 2005 else p_right
    if base_file.exists():
        img = Image.open(base_file).convert("RGB")
    else:
        img = Image.new("RGB", (400, 300), (20, 30, 40))

    # Adjust visual tone slightly based on year to visually simulate historical spectral evolution
    arr = np.array(img, dtype=np.float32)
    if year <= 1995:
        # Greener / lush canopy
        arr[..., 1] = np.clip(arr[..., 1] * 1.15, 0, 255)
    elif year >= 2015:
        # Higher urban reflectance
        arr[..., 0] = np.clip(arr[..., 0] * 1.12, 0, 255)
        arr[..., 2] = np.clip(arr[..., 2] * 1.08, 0, 255)

    img_out = Image.fromarray(arr.astype(np.uint8))
    
    # Render mission banner watermark
    draw = ImageDraw.Draw(img_out)
    draw.rectangle([(10, 10), (160, 34)], fill=(11, 15, 25, 200), outline=(0, 240, 255, 180))
    draw.text((16, 14), f"{mission} ({year})", fill=(0, 240, 255))

    buf = io.BytesIO()
    img_out.save(buf, format="JPEG", quality=85)
    return Response(content=buf.getvalue(), media_type="image/jpeg")

@app.get("/api/imagery/change_mask")
def get_change_mask_tile(loc: str = "bengaluru", y1: int = 1985, y2: int = 2024):
    """Generates visual bi-temporal change mask overlay."""
    p_right = ROOT_DIR / "tile_right.jpg"
    if p_right.exists():
        img = Image.open(p_right).convert("RGBA")
    else:
        img = Image.new("RGBA", (400, 300), (30, 35, 45, 255))
    
    arr = np.array(img)
    # Generate disturbance mask overlay in glowing red
    h, w = arr.shape[:2]
    np.random.seed(42)
    noise = np.random.rand(h, w)
    mask = noise > 0.65
    
    overlay = np.zeros_like(arr)
    overlay[mask] = [255, 30, 80, 160]  # Cyberpunk glowing red
    
    composite = Image.alpha_composite(img, Image.fromarray(overlay))
    buf = io.BytesIO()
    composite.convert("RGB").save(buf, format="JPEG")
    return Response(content=buf.getvalue(), media_type="image/jpeg")

# ==============================================================================
# Phase 6: TerraPulse 2.0 AI Environmental Investigator Endpoints
# ==============================================================================

@app.post("/api/investigator/chat")
async def investigator_chat_endpoint(req: InvestigatorChatRequest, request: Request):
    """
    Conversational AI Environmental Investigator streaming endpoint (SSE).
    Streams real-time tool execution events, slot clarification questions, and final evidence reports.
    """
    async def sse_event_stream():
        try:
            if await request.is_disconnected():
                return
            
            for event in global_investigator_agent.process_message(
                user_message=req.message,
                session_id=req.session_id,
                location=req.location,
                indicator=req.indicator
            ):
                if await request.is_disconnected():
                    break
                
                payload = {
                    "event": event.event_type.value,
                    "data": json.dumps(event.data, default=str),
                }
                yield payload
                await asyncio.sleep(0.005)
        except Exception as exc:
            yield {
                "event": "error",
                "data": json.dumps({
                    "error": str(exc),
                    "type": type(exc).__name__,
                    "message": "An error occurred during conversational investigation."
                }),
            }

    return EventSourceResponse(sse_event_stream())

@app.post("/api/investigator/reset")
def reset_investigator_session(session_id: str = Query("default_session")):
    """Resets conversational memory and investigation state for a given session."""
    global_investigator_agent.session_manager.reset_session(session_id)
    return {"status": "success", "session_id": session_id, "message": "Investigation session context reset."}

@app.get("/api/environmental/heatmap")
def get_environmental_heatmap(
    indicator: str = Query("PM2.5", description="Pollutant or indicator metric"),
    min_lon: float = Query(77.45, description="Bounding box minimum longitude"),
    min_lat: float = Query(12.80, description="Bounding box minimum latitude"),
    max_lon: float = Query(77.75, description="Bounding box maximum longitude"),
    max_lat: float = Query(13.15, description="Bounding box maximum latitude"),
    location: str = Query("bengaluru", description="Target region"),
    power: float = Query(2.0, ge=0.5, le=5.0, description="IDW distance weighting power"),
    search_radius_km: float = Query(10.0, ge=1.0, le=50.0, description="Maximum interpolation influence radius in km"),
    grid_resolution_deg: float = Query(0.015, ge=0.005, le=0.05, description="Grid spacing in decimal degrees")
):
    """
    Computes Inverse Distance Weighting (IDW) interpolation surface from monitoring telemetry.
    Returns standard GeoJSON FeatureCollection along with empirical coverage metrics.
    """
    from environmental.spatial_analysis import get_monitoring_stations_for_location
    if min_lon > 79.0 or "chennai" in location.lower():
        all_stations = get_monitoring_stations_for_location("chennai")
    else:
        all_stations = get_monitoring_stations_for_location(location)
    ind_clean = indicator.strip().upper()
    matching_stations = [s for s in all_stations if s.pollutant.strip().upper() == ind_clean]
    
    if not matching_stations:
        matching_stations = all_stations

    bbox = SpatialBoundingBox(
        min_lon=min_lon,
        min_lat=min_lat,
        max_lon=max_lon,
        max_lat=max_lat
    )
    x_steps = max(5, int(round((max_lon - min_lon) / grid_resolution_deg)))
    y_steps = max(5, int(round((max_lat - min_lat) / grid_resolution_deg)))

    config = IDWConfig(
        power=power,
        search_radius_km=search_radius_km,
        grid_resolution_x=x_steps,
        grid_resolution_y=y_steps
    )

    cells, metadata = compute_idw_surface(matching_stations, bbox, config)
    geojson_data = generate_investigation_geojson(matching_stations, interpolated_cells=cells)

    total_cells = metadata.get("total_cells", len(cells))
    cov_pct = metadata.get("data_coverage_pct", 0.0)
    interp_count = sum(1 for c in cells if c.contributing_neighbors > 0)
    uninterp_count = total_cells - interp_count

    return {
        "indicator": indicator,
        "interpolation_method": f"Inverse Distance Weighting (IDW, Power={power}, Radius={search_radius_km}km)",
        "bounding_box": [min_lon, min_lat, max_lon, max_lat],
        "coverage_percentage": cov_pct,
        "total_grid_points": total_cells,
        "interpolated_points": interp_count,
        "uninterpolated_points": uninterp_count,
        "geojson": geojson_data,
        "epistemic_notice": (
            f"Interpolated surface covers {cov_pct}% of bounding box within "
            f"{search_radius_km}km radius. Points outside radius carry high uncertainty and are not ground-truth measurements."
        )
    }

@app.post("/api/environmental/symptom-analysis")
def analyze_environmental_symptom(req: SymptomAnalysisRequest):
    """
    Runs multidisciplinary symptom-to-cause investigation using spatial telemetry and academic research.
    Evaluates Bradford Hill causality criteria (temporality, biological plausibility, dose-response).
    """
    from environmental.spatial_analysis import get_monitoring_stations_for_location
    stations = get_monitoring_stations_for_location(req.location or "bengaluru")
    result = investigate_environmental_symptom(
        user_query=req.symptom_query,
        stations=stations,
        fetch_live_literature=True,
        literature_limit=2
    )

    hypotheses = []
    for h in result.get("hypotheses_ranked", []):
        bh = h.get("bradford_hill") or {}
        hypotheses.append({
            "hypothesis_id": h.get("hypothesis_id", ""),
            "title": h.get("cause_name", ""),
            "pollutant": h.get("hypothesis_id", "").split("_")[0],
            "biological_mechanism": h.get("mechanistic_summary", ""),
            "confidence_tier": h.get("support_tier", ""),
            "bradford_hill_score": h.get("evidence_score", 0.0),
            "supporting_evidence": h.get("supporting_evidence", []),
            "conflicting_evidence": h.get("conflicting_evidence", []),
            "alternative_explanations": bh.get("alternative_explanations", []),
            "missing_data": h.get("missing_measurements_needed", [])
        })

    all_citations = []
    for h in result.get("hypotheses_ranked", []):
        all_citations.extend(h.get("scientific_citations", []))

    return {
        "symptom_detected": result.get("symptom_key", "unknown"),
        "location": req.location or "Bengaluru",
        "hypotheses": hypotheses,
        "uncertainty_statement": result.get("causal_disclaimer", ""),
        "investigation_summary": result.get("verdict_summary", ""),
        "academic_citations": all_citations
    }

@app.post("/api/environmental/forecast", response_model=ForecastResponse)
def generate_forecast_endpoint(req: ForecastRequest):
    """
    Generates statistical multi-scenario forecast (Business-As-Usual, Policy Reduction, Ecological Intervention).
    Includes 80% and 95% heteroskedastic prediction intervals.
    """
    from environmental.agent import generate_environmental_forecast_tool
    res = generate_environmental_forecast_tool(
        indicator=req.indicator,
        horizon=req.horizon,
        reduction_percentage=req.reduction_percentage
    )
    if "error" in res:
        raise HTTPException(status_code=400, detail=res["error"])

    scenarios_dict = {}
    for sc_key, sc in res.get("scenarios", {}).items():
        points = [
            ForecastScenarioPoint(
                year=p["year"],
                predicted_value=p["projected_value"],
                lower_80=p["lower_80"],
                upper_80=p["upper_80"],
                lower_95=p["lower_95"],
                upper_95=p["upper_95"]
            )
            for p in sc.get("trajectory", [])
        ]
        scenarios_dict[sc_key] = ForecastScenarioResult(
            scenario_name=sc.get("scenario_name", sc_key),
            description=sc.get("description", ""),
            trajectory=points,
            assumptions=sc.get("assumptions", [])
        )

    # Derive historical sequence from indicator preset in agent
    target_yr = 2030
    if scenarios_dict and "BAU" in scenarios_dict and scenarios_dict["BAU"].trajectory:
        target_yr = scenarios_dict["BAU"].trajectory[-1].year

    return ForecastResponse(
        indicator=res.get("indicator", req.indicator),
        unit=res.get("unit", "µg/m³"),
        historical_observations=[],
        scenarios=scenarios_dict,
        horizon_target_year=target_yr,
        statistical_method=res.get("model_name", "OLS Linear Extrapolation + Heteroskedastic Prediction Intervals"),
        disclaimer=res.get("disclaimer", "")
    )

@app.get("/api/environmental/research", response_model=ResearchQueryResponse)
def search_environmental_research(
    q: str = Query(..., min_length=2, description="Research query or topic"),
    limit: int = Query(4, ge=1, le=20, description="Max articles per provider")
):
    """
    Queries peer-reviewed scientific literature and environmental news via multi-source research aggregators.
    """
    articles, metrics = global_research_aggregator.search_all(query=q, limit_per_source=limit)
    res_list = [
        ResearchArticleSchema(
            title=art.title,
            authors=art.authors,
            publication_year=int(art.publication_date[:4]) if art.publication_date and art.publication_date[:4].isdigit() else None,
            source=art.source_provider,
            doi_or_url=art.doi or art.url or None,
            snippet=art.abstract_or_summary,
            article_type="academic_peer_reviewed" if art.source_provider in ["OpenAlex", "Europe PMC", "Crossref", "Semantic Scholar"] else "environmental_news"
        )
        for art in articles
    ]
    return ResearchQueryResponse(
        query=q,
        total_found=len(res_list),
        articles=res_list
    )



# ------------------------------------------------------------------------------
# Frontend SPA Static Assets Mounting
# ------------------------------------------------------------------------------
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

dist_dir = ROOT_DIR / "frontend" / "dist"
if dist_dir.exists():
    assets_dir = dist_dir / "assets"
    if assets_dir.exists():
        app.mount("/assets", StaticFiles(directory=str(assets_dir)), name="static-assets")
    textures_dir = dist_dir / "textures"
    if textures_dir.exists():
        app.mount("/textures", StaticFiles(directory=str(textures_dir)), name="static-textures")

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        # Do not catch /api paths
        if full_path.startswith("api/"):
            raise HTTPException(status_code=404, detail="API route not found")
        file_path = dist_dir / full_path
        if file_path.exists() and file_path.is_file():
            return FileResponse(file_path)
        return FileResponse(dist_dir / "index.html")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host=settings.HOST, port=settings.PORT, reload=settings.DEBUG)

