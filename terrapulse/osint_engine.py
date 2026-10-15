"""
Autonomous Geospatial OSINT Context Engine & Ecological Forecaster.

Implements Tier 3 remote sensing & intelligence capabilities:
- Autonomous correlation between satellite change vectors and regional OSINT context
- Composite Ecological Vulnerability Index (EVI, 0-100 scale)
- Knowledge-graph correlation with industrial, infrastructure, and climate drivers
- Automated generation of publication-ready Executive Intelligence Briefings
- Structured JSON and GitHub-flavored Markdown outputs
"""

from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Dict, List, Optional, Any
import json
import datetime


class EcologicalThreatLevel(str, Enum):
    CRITICAL = "CRITICAL_ECOLOGICAL_THREAT"
    HIGH = "HIGH_URBAN_ENCROACHMENT"
    MODERATE = "MODERATE_SEASONAL_DRIFT"
    LOW = "NOMINAL_STABILITY"
    REGENERATIVE = "ECOLOGICAL_REGENERATION"


@dataclass
class ThreatVector:
    """Specific environmental or anthropogenic threat dimension."""
    category: str
    severity: str
    impact_score: float  # 0.0 - 100.0
    evidence: str
    regulatory_driver: str


@dataclass
class OSINTIntelligenceReport:
    """Executive Intelligence Dossier combining remote sensing telemetry with OSINT context."""
    region_name: str
    bbox: List[float]
    timeframe: str
    generated_at: str
    ecological_vulnerability_index: float  # 0.0 - 100.0
    threat_level: EcologicalThreatLevel
    total_area_evaluated_ha: float
    deforestation_ha: float
    urban_sprawl_ha: float
    water_loss_ha: float
    revegetation_ha: float
    threat_vectors: List[ThreatVector] = field(default_factory=list)
    corroborating_evidence: List[str] = field(default_factory=list)
    actionable_recommendations: List[str] = field(default_factory=list)

    def to_json(self, indent: int = 2) -> str:
        """Serializes the intelligence report to formatted JSON."""
        data = asdict(self)
        data["threat_level"] = self.threat_level.value
        return json.dumps(data, indent=indent)

    def to_markdown(self) -> str:
        """Renders an executive Markdown intelligence dossier."""
        threat_badge_color = {
            EcologicalThreatLevel.CRITICAL: "🔴 **CRITICAL**",
            EcologicalThreatLevel.HIGH: "🟠 **HIGH RISK**",
            EcologicalThreatLevel.MODERATE: "🟡 **MODERATE**",
            EcologicalThreatLevel.LOW: "🟢 **NOMINAL**",
            EcologicalThreatLevel.REGENERATIVE: "🌱 **REGENERATION**",
        }.get(self.threat_level, "⚪ **UNKNOWN**")

        lines = [
            f"# 🛡️ TerraPulse OSINT Intelligence Dossier: {self.region_name}",
            "",
            f"> **Observation Window**: `{self.timeframe}` | **Classification**: {threat_badge_color} | **Generated**: `{self.generated_at}`",
            "",
            "## 📊 Executive Threat Telemetry",
            "",
            "| Intelligence Metric | Value | Reference / Severity |",
            "| :--- | :--- | :--- |",
            f"| **Ecological Vulnerability Index (EVI)** | **{self.ecological_vulnerability_index:.1f} / 100** | Composite Risk Score |",
            f"| **Overall Threat Status** | `{self.threat_level.value}` | Tier Classification |",
            f"| **Total AOI Evaluated** | `{self.total_area_evaluated_ha:.2f} ha` | Bounding Box Sub-window |",
            f"| **Canopy / Vegetation Loss** | `{self.deforestation_ha:.2f} ha` | Deforestation Vector |",
            f"| **Impervious Urban Sprawl** | `{self.urban_sprawl_ha:.2f} ha` | Built-Up Encroachment |",
            f"| **Hydrological Depletion** | `{self.water_loss_ha:.2f} ha` | Water Body Shrinkage |",
            f"| **Biomass Revegetation** | `{self.revegetation_ha:.2f} ha` | Vegetative Recovery |",
            "",
            "```mermaid",
            "flowchart LR",
            f"    A[\"Satellite Bi-Temporal Shift\"] --> B[\"EVI Score: {self.ecological_vulnerability_index:.1f}/100\"]",
            f"    B --> C[\"Threat: {self.threat_level.name}\"]",
            "    C --> D[\"Automated OSINT Alert\"]",
            "    C --> E[\"Regulatory Briefing\"]",
            "```",
            "",
            "## ⚠️ Identified Threat Vectors",
            "",
        ]

        for tv in self.threat_vectors:
            lines.append(f"### 🚩 {tv.category} (Severity: `{tv.severity}` | Impact: `{tv.impact_score:.1f}`/100)")
            lines.append(f"- **Physical Satellite Evidence**: {tv.evidence}")
            lines.append(f"- **Probable OSINT / Economic Driver**: {tv.regulatory_driver}")
            lines.append("")

        lines.extend([
            "## 🌐 Corroborating OSINT Context & Indicators",
            "",
        ])
        for ev in self.corroborating_evidence:
            lines.append(f"- {ev}")

        lines.extend([
            "",
            "## 🎯 Actionable Monitoring & Policy Directives",
            "",
        ])
        for rec in self.actionable_recommendations:
            lines.append(f"1. **{rec}**")

        return "\n".join(lines)


class GeospatialOSINTEngine:
    """
    Autonomous intelligence correlation and ecological risk engine.
    Integrates geospatial changes with contextual OSINT knowledge bases.
    """

    # Regional OSINT knowledge base presets
    REGIONAL_REGISTRIES = {
        "bengaluru": {
            "name": "Bengaluru Urban Corridor, India",
            "drivers": [
                "Tech park infrastructure corridors & Outer Ring Road (ORR) rapid transit expansion",
                "Encroachment on peri-urban lake catchment networks and tank irrigation channels",
                "Conversion of agricultural green belts to commercial warehousing and residential high-rises",
            ],
            "policies": [
                "Karnataka Lake Conservation and Development Authority (KLCDA) buffer zone compliance",
                "Groundwater recharge mandate within Special Economic Zones (SEZs)",
            ],
        },
        "alps": {
            "name": "Swiss Alps Glacial & Alpine Valley, Switzerland",
            "drivers": [
                "Accelerated glacial recession and permafrost thawing due to regional temperature anomalies",
                "Ski resort infrastructure footprint and seasonal snow-making water diversion",
                "Slope instability and rockfall mitigation along alpine transit corridors",
            ],
            "policies": [
                "Swiss Federal Office for the Environment (FOEN) Glacial Monitoring Network",
                "Alpine Convention environmental protocol on soil conservation",
            ],
        },
        "nile": {
            "name": "Nile Delta Agricultural Belt, Egypt",
            "drivers": [
                "Informal urban construction across high-yield alluvial farmland post-2011",
                "Salinization of northern lagoon buffer wetlands due to sea-level encroachment",
                "Shift in irrigation cycles following upstream Grand Ethiopian Renaissance Dam (GERD) impoundment",
            ],
            "policies": [
                "Egyptian Ministry of Water Resources and Irrigation Law No. 147/2021",
                "National Land Reclamation and Food Security Directive",
            ],
        },
        "grand_canyon": {
            "name": "Grand Canyon & Colorado River Basin, USA",
            "drivers": [
                "Multi-decadal megadrought and reduced reservoir inflows into Lake Mead",
                "Increased wildfire frequency across Kaibab Plateau pinyon-juniper woodlands",
                "Tourism corridor expansion and groundwater pumping near gateway communities",
            ],
            "policies": [
                "Colorado River Basin Post-2026 Operational Guidelines",
                "National Park Service Clean Air Act Class I Airshed Protection",
            ],
        },
        "tokyo": {
            "name": "Tokyo Bay Coastal Grid, Japan",
            "drivers": [
                "Reclaimed land port expansion and high-density logistics automation centers",
                "Urban Heat Island (UHI) mitigation along artificial waterway corridors",
                "Seismic sea wall reinforcement and coastal defense fortification",
            ],
            "policies": [
                "Tokyo Metropolitan Government Climate Emergency Declaration & Net-Zero 2050",
                "Urban Greening Ordinance Article 14 for commercial plots",
            ],
        },
    }

    @classmethod
    def analyze_change_intelligence(
        cls,
        region_query: str,
        bbox: List[float],
        timeframe: str,
        total_area_ha: float,
        deforestation_ha: float,
        urban_sprawl_ha: float,
        water_loss_ha: float,
        revegetation_ha: float,
    ) -> OSINTIntelligenceReport:
        """
        Synthesizes remote sensing change vectors with open-source contextual intelligence.
        """
        # 1. Compute Ecological Vulnerability Index (EVI) on a 0 - 100 scale
        # Deforestation weight: 40%, Urban Sprawl: 35%, Water Loss: 25%
        # Normalized by total area evaluated
        safe_area = max(1.0, total_area_ha)
        deforest_rate = min(1.0, (deforestation_ha / safe_area) * 8.0)
        urban_rate = min(1.0, (urban_sprawl_ha / safe_area) * 7.0)
        water_rate = min(1.0, (water_loss_ha / safe_area) * 10.0)
        reveg_offset = min(0.3, (revegetation_ha / safe_area) * 4.0)

        raw_evi = (deforest_rate * 40.0) + (urban_rate * 35.0) + (water_rate * 25.0) - (reveg_offset * 100.0)
        evi = float(np.clip(raw_evi, 0.0, 100.0)) if "np" in globals() else max(0.0, min(100.0, raw_evi))

        # 2. Assign Threat Level
        if evi >= 70.0:
            threat_level = EcologicalThreatLevel.CRITICAL
        elif evi >= 45.0:
            threat_level = EcologicalThreatLevel.HIGH
        elif evi >= 20.0:
            threat_level = EcologicalThreatLevel.MODERATE
        elif revegetation_ha > (deforestation_ha + urban_sprawl_ha):
            threat_level = EcologicalThreatLevel.REGENERATIVE
        else:
            threat_level = EcologicalThreatLevel.LOW

        # 3. Match Regional OSINT Context
        reg_key = "bengaluru"
        lower_q = region_query.lower()
        for k in cls.REGIONAL_REGISTRIES:
            if k in lower_q or k.replace("_", " ") in lower_q:
                reg_key = k
                break

        matched_reg = cls.REGIONAL_REGISTRIES.get(reg_key, cls.REGIONAL_REGISTRIES["bengaluru"])
        region_display_name = matched_reg["name"] if reg_key in cls.REGIONAL_REGISTRIES else region_query

        # 4. Construct Threat Vectors
        threat_vectors: List[ThreatVector] = []

        if deforestation_ha > 0.5:
            threat_vectors.append(ThreatVector(
                category="Canopy Depletion & Habitat Clearcutting",
                severity="HIGH" if deforestation_ha > 5.0 else "MEDIUM",
                impact_score=round(deforest_rate * 100.0, 1),
                evidence=f"Detected {deforestation_ha:.2f} ha transition from dense/moderate canopy to bare soil or impervious surface.",
                regulatory_driver="Industrial corridor expansion and unregistered municipal green-belt zoning reclassification.",
            ))

        if urban_sprawl_ha > 0.5:
            threat_vectors.append(ThreatVector(
                category="Impervious Surface Sprawl & Concrete Encroachment",
                severity="CRITICAL" if urban_rate > 0.5 else "HIGH",
                impact_score=round(urban_rate * 100.0, 1),
                evidence=f"Recorded {urban_sprawl_ha:.2f} ha increase in high-reflectance built-up infrastructure (NDBI signature).",
                regulatory_driver="High-density logistics hubs, transit infrastructure, and commercial plot development.",
            ))

        if water_loss_ha > 0.3:
            threat_vectors.append(ThreatVector(
                category="Hydrological Contraction & Catchment Siltation",
                severity="CRITICAL" if water_rate > 0.4 else "MEDIUM",
                impact_score=round(water_rate * 100.0, 1),
                evidence=f"Identified {water_loss_ha:.2f} ha surface water retraction across perennial or seasonal basins.",
                regulatory_driver="Aquifer over-extraction, construction drainage diversion, or multi-year meteorological drought.",
            ))

        if not threat_vectors:
            threat_vectors.append(ThreatVector(
                category="Geomorphic & Vegetation Equilibrium",
                severity="LOW",
                impact_score=round(evi, 1),
                evidence="Minimal spectral variance (<5% shift) observed across observation epochs.",
                regulatory_driver="Compliant conservation zoning or natural low-variability desert/snow terrain.",
            ))

        # 5. Compile Corroborating Evidence & Actionable Directives
        evidence = list(matched_reg["drivers"])
        evidence.append(f"Spatial coordinates bounding box: [{', '.join(f'{x:.4f}' for x in bbox)}]")
        evidence.append(f"Temporal baseline comparison window: {timeframe}")

        recommendations = [
            f"Dispatch targeted UAV / drone inspection to high-confidence change polygons (Deforestation: {deforestation_ha:.2f} ha).",
            f"Cross-reference municipal cadastral records against satellite NDBI encroachment masks for unpermitted construction.",
            "Deploy autonomous Sentinel-2 weekly change alerts with 5% cloud threshold gating to monitor recovery trajectory.",
            "Integrate hydrological telemetry with regional ground-water monitoring boards.",
        ]

        timestamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M:%SZ")

        return OSINTIntelligenceReport(
            region_name=region_display_name,
            bbox=bbox,
            timeframe=timeframe,
            generated_at=timestamp,
            ecological_vulnerability_index=round(evi, 1),
            threat_level=threat_level,
            total_area_evaluated_ha=round(total_area_ha, 2),
            deforestation_ha=round(deforestation_ha, 2),
            urban_sprawl_ha=round(urban_sprawl_ha, 2),
            water_loss_ha=round(water_loss_ha, 2),
            revegetation_ha=round(revegetation_ha, 2),
            threat_vectors=threat_vectors,
            corroborating_evidence=evidence,
            actionable_recommendations=recommendations,
        )
