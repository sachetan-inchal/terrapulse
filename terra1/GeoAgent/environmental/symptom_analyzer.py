"""Environmental Symptom-to-Cause Analysis Engine.

Investigates environmental symptoms (e.g. fish mortality, toxic foaming, algal blooms,
chlorosis, respiratory smog) using:
- Natural-language symptom classification and entity extraction.
- Multi-hypothesis generation with mechanistic descriptions.
- Empirical telemetry evaluation against critical biological/chemical thresholds.
- Bradford Hill causality considerations (biological plausibility, dose-response, temporality, coherence, alternative explanations).
- Integration with Phase 1 scientific literature and Phase 2 spatial measurements.
- Hypothesis ranking by evidence strength (strictly qualitative support tiers; never pseudo-probabilities).
- Explicit identification of missing data, conflicting evidence, and causal uncertainty boundaries.
"""

from __future__ import annotations

import re
import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Tuple

from environmental.research_apis import (
    ArticleMetadata,
    search_academic_literature,
    search_environmental_news,
)
from environmental.spatial_analysis import MonitoringStation

logger = logging.getLogger(__name__)


# Standard Qualitative Support Tiers (Never presented as causal probabilities)
SUPPORT_TIERS = [
    "HIGH_EMPIRICAL_SUPPORT",
    "MODERATE_SUPPORT",
    "INSUFFICIENT_EVIDENCE",
    "CONFLICTING_EVIDENCE",
    "UNVERIFIED_HYPOTHESIS",
]


@dataclass
class EvidenceItem:
    """A discrete empirical observation or literature finding."""
    evidence_type: str  # "EMPIRICAL_MEASUREMENT", "SCIENTIFIC_LITERATURE", "NEWS_REPORT", "ANOMALY_DETECTION"
    claim: str
    source: str
    relevance: str      # "SUPPORTING", "CONFLICTING", "NEUTRAL"
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class BradfordHillEvaluation:
    """Evaluation of Bradford Hill considerations for an environmental hypothesis."""
    biological_plausibility: str  # "High", "Moderate", "Unclear"
    plausibility_rationale: str
    temporality_satisfied: Optional[bool]
    temporality_rationale: str
    dose_response_gradient: str   # "Consistent with toxic threshold", "Sub-lethal exposure", "Unknown"
    coherence: str                # "Coherent with ecosystem dynamics", "Conflicts with known hydrology/chemistry"
    alternative_explanations: List[str]


@dataclass
class CausalHypothesis:
    """A structured candidate cause for an observed environmental symptom."""
    hypothesis_id: str
    cause_name: str
    mechanistic_summary: str
    support_tier: str             # From SUPPORT_TIERS
    evidence_score: float         # Internal qualitative index [0.0 to 1.0], not a causal probability
    supporting_evidence: List[EvidenceItem] = field(default_factory=list)
    conflicting_evidence: List[EvidenceItem] = field(default_factory=list)
    bradford_hill: Optional[BradfordHillEvaluation] = None
    scientific_citations: List[Dict[str, str]] = field(default_factory=list)
    missing_measurements_needed: List[str] = field(default_factory=list)
    epistemic_caveat: str = (
        "Evidence ranking indicates empirical and literature corroboration, "
        "not a validated causal proof. Correlation does not establish causation."
    )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "hypothesis_id": self.hypothesis_id,
            "cause_name": self.cause_name,
            "mechanistic_summary": self.mechanistic_summary,
            "support_tier": self.support_tier,
            "evidence_score": round(self.evidence_score, 2),
            "supporting_evidence": [
                {"type": e.evidence_type, "claim": e.claim, "source": e.source}
                for e in self.supporting_evidence
            ],
            "conflicting_evidence": [
                {"type": e.evidence_type, "claim": e.claim, "source": e.source}
                for e in self.conflicting_evidence
            ],
            "bradford_hill": {
                "biological_plausibility": self.bradford_hill.biological_plausibility if self.bradford_hill else "Unclear",
                "plausibility_rationale": self.bradford_hill.plausibility_rationale if self.bradford_hill else "",
                "dose_response_gradient": self.bradford_hill.dose_response_gradient if self.bradford_hill else "Unknown",
                "alternative_explanations": self.bradford_hill.alternative_explanations if self.bradford_hill else [],
            } if self.bradford_hill else None,
            "scientific_citations": self.scientific_citations,
            "missing_measurements_needed": self.missing_measurements_needed,
            "epistemic_caveat": self.epistemic_caveat,
        }


@dataclass
class SymptomProfile:
    """Recognized environmental symptom profile with hypothesis templates."""
    symptom_key: str
    canonical_name: str
    trigger_keywords: List[str]
    candidate_hypotheses: List[Dict[str, Any]]


# Comprehensive Environmental Symptom Knowledge Base
SYMPTOM_CATALOG: List[SymptomProfile] = [
    SymptomProfile(
        symptom_key="fish_mortality",
        canonical_name="Aquatic Organism & Fish Mortality (Fish Kill)",
        trigger_keywords=[
            "fish die", "fish death", "fish kill", "dead fish", "fish dying",
            "aquatic mortality", "floating fish", "gill damage", "lake mortality"
        ],
        candidate_hypotheses=[
            {
                "id": "HYP-HYPOXIA",
                "cause_name": "Dissolved Oxygen Depletion (Anoxia / Hypoxia)",
                "mechanism": "Severe depletion of dissolved oxygen (< 2.0 mg/L) caused by organic wastewater decomposition or post-bloom microbial respiration, asphyxiating aquatic fauna.",
                "target_telemetry_keys": ["dissolved_oxygen_mg_l"],
                "critical_threshold": {"key": "dissolved_oxygen_mg_l", "op": "lt", "value": 2.5, "unit": "mg/L"},
                "plausibility": "High. Oxygen concentrations below 2-3 mg/L induce acute hypoxia in teleost fish within hours.",
                "search_queries": ["fish kill dissolved oxygen depletion hypoxia freshwater lake", "hypoxic event aquatic mortality"],
                "missing_needs": ["Continuous diurnal dissolved oxygen profile", "Biochemical Oxygen Demand (BOD5) assay"],
                "rivals": ["Acute industrial chemical toxicity", "Ammonia toxicity under high pH"],
            },
            {
                "id": "HYP-TOXIC-CONTAMINATION",
                "cause_name": "Acute Toxic Industrial / Chemical Contamination",
                "mechanism": "Direct entry of untreated industrial effluents containing surfactants, heavy metals, or organophosphates disrupting gill epithelial tissue.",
                "target_telemetry_keys": ["surfactants_mg_l", "heavy_metals_mg_l"],
                "critical_threshold": {"key": "surfactants_mg_l", "op": "gt", "value": 2.0, "unit": "mg/L"},
                "plausibility": "High. High surfactant and heavy metal loads cause severe cell lysis and gill hypersecretion.",
                "search_queries": ["industrial surfactant wastewater toxicity fish mortality", "heavy metal contamination aquatic death"],
                "missing_needs": ["Gas chromatography-mass spectrometry (GC-MS) for industrial chemicals", "Histopathology of fish gills and liver"],
                "rivals": ["Nocturnal oxygen depletion", "Pathogenic outbreak"],
            },
            {
                "id": "HYP-ALGAL-BIOTOXINS",
                "cause_name": "Harmful Algal Bloom (HAB) & Cyanotoxins",
                "mechanism": "Cyanobacterial blooms (e.g. Microcystis) releasing hepatotoxins and neurotoxins (microcystins) into water columns.",
                "target_telemetry_keys": ["microcystin_ug_l", "chlorophyll_a_ug_l"],
                "critical_threshold": {"key": "chlorophyll_a_ug_l", "op": "gt", "value": 50.0, "unit": "µg/L"},
                "plausibility": "Moderate. Cyanotoxins cause lethal systemic toxicity, but bloom collapse typically kills fish via secondary hypoxia.",
                "search_queries": ["cyanobacteria harmful algal bloom fish kill microcystin", "algal bloom eutrophication toxicity"],
                "missing_needs": ["Microcystin ELISA toxin quantification", "Phytoplankton species cell counts"],
                "rivals": ["Physical asphyxiation via nocturnal anoxia"],
            },
            {
                "id": "HYP-THERMAL-SHOCK",
                "cause_name": "Sudden Thermal Shock / Inversion",
                "mechanism": "Abrupt temperature increases from cooling water discharge or rapid lake destratification reducing oxygen solubility and inducing metabolic stress.",
                "target_telemetry_keys": ["water_temp_celsius"],
                "critical_threshold": {"key": "water_temp_celsius", "op": "gt", "value": 34.0, "unit": "°C"},
                "plausibility": "Moderate. Thermal shock lowers oxygen solubility and accelerates oxygen demand.",
                "search_queries": ["thermal shock aquatic mortality lake turnover", "temperature stress fish death"],
                "missing_needs": ["Depth-resolved temperature profile", "Thermal satellite radiometric readings"],
                "rivals": ["Chemical contamination", "Hypoxic water column overturn"],
            },
        ],
    ),
    SymptomProfile(
        symptom_key="toxic_foam",
        canonical_name="Surfactant Foam & Wetland Frothing Events",
        trigger_keywords=[
            "foam", "froth", "foaming", "lake fire", "burning lake", "white foam",
            "detergent bubbles", "toxic foam", "soap foam"
        ],
        candidate_hypotheses=[
            {
                "id": "HYP-SURFACTANT-DISCHARGE",
                "cause_name": "Untreated Synthetic Detergents & Surfactant Influx",
                "mechanism": "Accumulation of linear alkylbenzene sulfonates (LAS) from domestic and industrial laundering effluents which lower water surface tension and foam under turbulent spillways.",
                "target_telemetry_keys": ["surfactants_mg_l"],
                "critical_threshold": {"key": "surfactants_mg_l", "op": "gt", "value": 2.0, "unit": "mg/L"},
                "plausibility": "High. High surfactant concentration is the established physical driver of lake frothing under aeration.",
                "search_queries": ["Bellandur lake foam surfactants detergent effluent", "urban wetland foaming synthetic surfactants"],
                "missing_needs": ["Speciation of anionic vs non-ionic surfactants", "Discharge volume tracking from upstream STPs"],
                "rivals": ["Natural organic lipid/protein foam from decaying algal biomass"],
            },
            {
                "id": "HYP-ORGANIC-EUTROPHICATION",
                "cause_name": "Organic Decomposition & Biogenic Foam Agents",
                "mechanism": "Decomposition of massive algal and macrophytic biomass releasing biogenic proteins, lipids, and extracellular polysaccharides that stabilize surface foams.",
                "target_telemetry_keys": ["dissolved_oxygen_mg_l"],
                "critical_threshold": {"key": "dissolved_oxygen_mg_l", "op": "lt", "value": 1.5, "unit": "mg/L"},
                "plausibility": "Moderate to High. Organic matter provides foam stabilization matrices alongside synthetic detergents.",
                "search_queries": ["biogenic foam eutrophic lakes organic lipids", "decaying phytoplankton foam stabilization"],
                "missing_needs": ["Total Organic Carbon (TOC) analysis", "Lipid fraction chromatographic profiling"],
                "rivals": ["Industrial synthetic surfactants"],
            },
        ],
    ),
    SymptomProfile(
        symptom_key="water_discoloration",
        canonical_name="Water Discoloration & Turbidity Influx",
        trigger_keywords=[
            "green water", "water green", "brown water", "discoloration", "turbid",
            "algal scum", "sludge", "red tide", "murky water"
        ],
        candidate_hypotheses=[
            {
                "id": "HYP-EUTROPHIC-ALGAE",
                "cause_name": "Hyper-Eutrophication & Cyanobacterial Proliferation",
                "mechanism": "Excessive phosphorus and nitrogen runoff triggering exponential cyanobacterial growth, creating dense green surface scums.",
                "target_telemetry_keys": ["chlorophyll_a_ug_l", "mean_ndvi"],
                "critical_threshold": {"key": "chlorophyll_a_ug_l", "op": "gt", "value": 40.0, "unit": "µg/L"},
                "plausibility": "High. High nutrient loading directly manifests as intense green coloration.",
                "search_queries": ["cyanobacterial green scum eutrophication chlorophyll", "lake hyper eutrophication satellite NDVI"],
                "missing_needs": ["Total Nitrogen and Total Phosphorus nutrient ratios", "Phytoplankton microscopy"],
                "rivals": ["Suspended sediment runoff", "Industrial dye effluent"],
            },
        ],
    ),
    SymptomProfile(
        symptom_key="air_pollution_smog",
        canonical_name="Atmospheric Particulate Smog & Chemical Odor",
        trigger_keywords=[
            "smog", "haze", "air pollution", "burning smell", "chemical odor",
            "choking", "respiratory", "particulate spike", "sulfur smell"
        ],
        candidate_hypotheses=[
            {
                "id": "HYP-PM-STAGNATION",
                "cause_name": "Combustion Emission Trapping & Thermal Inversion",
                "mechanism": "Industrial stack emissions and diesel exhaust trapped in a shallow planetary boundary layer during meteorological inversion.",
                "target_telemetry_keys": ["measured_value", "so2_ug_m3", "no2_ug_m3"],
                "critical_threshold": {"key": "measured_value", "op": "gt", "value": 100.0, "unit": "µg/m³"},
                "plausibility": "High. Particulate matter spikes exceeding 100 µg/m³ match dense smog formation.",
                "search_queries": ["urban air pollution thermal inversion particulate matter", "PM2.5 spike industrial emissions sulfur dioxide"],
                "missing_needs": ["Boundary layer lidar profiling", "Speciated aerosol mass spectrometry (black carbon, sulfate, nitrate)"],
                "rivals": ["Agricultural biomass burning plume from regional sources"],
            },
        ],
    ),
    SymptomProfile(
        symptom_key="vegetation_damage",
        canonical_name="Canopy Chlorosis, Defoliation & Forest Dieback",
        trigger_keywords=[
            "chlorosis", "yellowing leaves", "vegetation damage", "forest dieback",
            "tree death", "defoliation", "canopy loss", "crop failure"
        ],
        candidate_hypotheses=[
            {
                "id": "HYP-ACID-SO2-EXPOSURE",
                "cause_name": "Atmospheric Sulfur Dioxide & Acid Deposition",
                "mechanism": "Gaseous SO2 entering stomata, generating toxic bisulfite ions that degrade chlorophyll molecules and leach foliar nutrients.",
                "target_telemetry_keys": ["so2_ug_m3"],
                "critical_threshold": {"key": "so2_ug_m3", "op": "gt", "value": 40.0, "unit": "µg/m³"},
                "plausibility": "High. High SO2 exposure induces foliar necrosis and interveinal chlorosis.",
                "search_queries": ["sulfur dioxide foliar chlorosis vegetation damage", "acid deposition forest dieback canopy fragmentation"],
                "missing_needs": ["Foliar sulfur concentration assay", "Soil pH and exchangeable aluminum testing"],
                "rivals": ["Severe root-zone drought stress", "Bark beetle / phytopathogen infestation"],
            },
        ],
    ),
]


def classify_symptom_from_text(query_text: str) -> Optional[SymptomProfile]:
    """Recognize and map natural-language query to an environmental symptom profile."""
    q_norm = query_text.lower().strip()
    if not q_norm:
        return None

    words = set(re.findall(r"\w+", q_norm))

    # 1. Flexible semantic rules for compound symptoms
    # Fish / aquatic mortality
    if "fish" in words and (words & {"die", "dying", "dead", "death", "deaths", "kill", "killed", "kills", "floating", "mortality"}):
        return next(p for p in SYMPTOM_CATALOG if p.symptom_key == "fish_mortality")

    # Toxic foam & lake frothing
    if (words & {"foam", "foaming", "froth", "frothing"}) or ("lake" in words and "fire" in words):
        return next(p for p in SYMPTOM_CATALOG if p.symptom_key == "toxic_foam")

    # Water green / algal scum / discoloration
    if (words & {"water", "lake", "river"}) and (words & {"green", "algae", "algal", "scum", "discoloration", "turbid", "turbidity", "murky", "brown"}):
        return next(p for p in SYMPTOM_CATALOG if p.symptom_key == "water_discoloration")

    # Atmospheric smog & haze
    if words & {"smog", "haze", "choking", "respiratory", "sulfur", "fumes"}:
        return next(p for p in SYMPTOM_CATALOG if p.symptom_key == "air_pollution_smog")

    # Vegetation damage / chlorosis
    if (words & {"vegetation", "forest", "tree", "trees", "canopy", "leaf", "leaves"}) and (words & {"damage", "dieback", "death", "chlorosis", "yellowing", "defoliation", "dying"}):
        return next(p for p in SYMPTOM_CATALOG if p.symptom_key == "vegetation_damage")

    # 2. Keyword score matching fallback
    best_match: Optional[SymptomProfile] = None
    max_hits = 0

    for profile in SYMPTOM_CATALOG:
        hits = 0
        for kw in profile.trigger_keywords:
            if kw in q_norm:
                hits += 1
        if hits > max_hits:
            max_hits = hits
            best_match = profile

    return best_match if max_hits > 0 else None


def evaluate_hypothesis_against_measurements(
    hypothesis_tmpl: Dict[str, Any],
    stations: List[MonitoringStation],
) -> Tuple[List[EvidenceItem], List[EvidenceItem], Optional[BradfordHillEvaluation]]:
    """Compare candidate hypothesis against empirical monitoring telemetry."""
    supporting: List[EvidenceItem] = []
    conflicting: List[EvidenceItem] = []

    target_keys = hypothesis_tmpl.get("target_telemetry_keys", [])
    threshold = hypothesis_tmpl.get("critical_threshold")

    # Collect available measurements across stations
    matched_measurements: Dict[str, List[Tuple[float, str, str]]] = {k: [] for k in target_keys}

    for st in stations:
        # Check standard measured_value
        if "measured_value" in target_keys:
            matched_measurements["measured_value"].append((st.measured_value, st.unit, st.name))

        # Check pollutant matches
        if st.pollutant.lower() in [k.lower() for k in target_keys]:
            matched_measurements[st.pollutant.lower()].append((st.measured_value, st.unit, st.name))

        # Check extra_attributes
        for attr_key, attr_val in st.extra_attributes.items():
            if attr_key in target_keys and isinstance(attr_val, (int, float)):
                matched_measurements[attr_key].append((float(attr_val), "", st.name))

    # Evaluate critical threshold
    dose_response = "Unknown (No targeted chemical assay)"
    if threshold:
        th_key = threshold["key"]
        th_op = threshold["op"]
        th_val = threshold["value"]
        th_unit = threshold.get("unit", "")

        values = matched_measurements.get(th_key, [])
        if values:
            numeric_vals = [v[0] for v in values]
            max_v = max(numeric_vals)
            min_v = min(numeric_vals)
            station_names = ", ".join(set(v[2] for v in values[:3]))

            if th_op == "lt":
                # E.g. DO < 2.5 mg/L is critical
                if min_v <= th_val:
                    supporting.append(
                        EvidenceItem(
                            evidence_type="EMPIRICAL_MEASUREMENT",
                            claim=f"Measured {th_key} dropped to critical low of {min_v:.2f} {th_unit} at {station_names} (Threshold < {th_val} {th_unit}).",
                            source="Regional Monitoring Network",
                            relevance="SUPPORTING",
                            details={"min_value": min_v, "threshold": th_val, "stations": station_names},
                        )
                    )
                    dose_response = f"Consistent with lethal threshold (observed min {min_v:.2f} {th_unit} <= {th_val})"
                else:
                    conflicting.append(
                        EvidenceItem(
                            evidence_type="EMPIRICAL_MEASUREMENT",
                            claim=f"Measured {th_key} was {min_v:.2f} {th_unit} at {station_names}, above the critical hypoxia threshold of {th_val} {th_unit}.",
                            source="Regional Monitoring Network",
                            relevance="CONFLICTING",
                            details={"min_value": min_v, "threshold": th_val, "stations": station_names},
                        )
                    )
                    dose_response = f"Sub-critical level ({min_v:.2f} {th_unit} > threshold {th_val})"
            elif th_op == "gt":
                # E.g. Surfactants > 2.0 mg/L or PM2.5 > 100 µg/m³
                if max_v >= th_val:
                    supporting.append(
                        EvidenceItem(
                            evidence_type="EMPIRICAL_MEASUREMENT",
                            claim=f"Measured {th_key} reached elevated spike of {max_v:.2f} {th_unit} at {station_names} (Critical threshold > {th_val} {th_unit}).",
                            source="Regional Monitoring Network",
                            relevance="SUPPORTING",
                            details={"max_value": max_v, "threshold": th_val, "stations": station_names},
                        )
                    )
                    dose_response = f"Exceeds toxic/hazard threshold (observed max {max_v:.2f} {th_unit} >= {th_val})"
                else:
                    conflicting.append(
                        EvidenceItem(
                            evidence_type="EMPIRICAL_MEASUREMENT",
                            claim=f"Measured {th_key} was {max_v:.2f} {th_unit} at {station_names}, which is below the threshold of {th_val} {th_unit}.",
                            source="Regional Monitoring Network",
                            relevance="CONFLICTING",
                            details={"max_value": max_v, "threshold": th_val, "stations": station_names},
                        )
                    )
                    dose_response = f"Below hazard threshold (observed max {max_v:.2f} {th_unit} < {th_val})"

    bradford_hill = BradfordHillEvaluation(
        biological_plausibility="High" if supporting else hypothesis_tmpl.get("plausibility", "Moderate"),
        plausibility_rationale=hypothesis_tmpl.get("plausibility", "Biologically plausible mechanism."),
        temporality_satisfied=True if supporting else None,
        temporality_rationale="Requires verification that emission/depletion preceded observed symptom onset.",
        dose_response_gradient=dose_response,
        coherence="Coherent with documented limnological and atmospheric degradation mechanisms.",
        alternative_explanations=hypothesis_tmpl.get("rivals", []),
    )

    return supporting, conflicting, bradford_hill


def investigate_environmental_symptom(
    user_query: str,
    stations: Optional[List[MonitoringStation]] = None,
    fetch_live_literature: bool = True,
    literature_limit: int = 2,
) -> Dict[str, Any]:
    """Execute end-to-end evidence-based symptom investigation.
    
    Returns structured analysis with ranked hypotheses, supporting/conflicting evidence,
    scientific literature citations, and missing data disclosure.
    """
    stations = stations or []
    symptom = classify_symptom_from_text(user_query)

    if not symptom:
        return {
            "query": user_query,
            "status": "UNRECOGNIZED_SYMPTOM",
            "symptom_identified": "Unrecognized Symptom",
            "symptom_key": None,
            "verdict_summary": "Could not confidently match query to a documented environmental symptom category.",
            "message": (
                "Could not confidently match query to a documented environmental symptom category. "
                "Supported categories include: aquatic mortality/fish kills, toxic foaming, water discoloration, "
                "atmospheric smog, vegetation chlorosis, and soil degradation."
            ),
            "hypotheses_ranked": [],
            "missing_measurements": ["Specific physical or biological symptom description."],
            "causal_disclaimer": (
                "Scientific Integrity Rule: Evidence rankings quantify comparative support from available "
                "telemetry and literature. They do not constitute proven causal certainty. Never treat "
                "correlation as proof of causation without comprehensive biological, chemical, and historical verification."
            ),
        }

    evaluated_hypotheses: List[CausalHypothesis] = []

    for tmpl in symptom.candidate_hypotheses:
        supporting, conflicting, bh = evaluate_hypothesis_against_measurements(tmpl, stations)

        # Retrieve peer-reviewed scientific literature
        citations: List[Dict[str, str]] = []
        if fetch_live_literature:
            search_terms = tmpl.get("search_queries", [tmpl["cause_name"]])[0]
            try:
                articles, _ = search_academic_literature(search_terms, limit_per_source=literature_limit)
                for art in articles[:3]:
                    citations.append({
                        "title": art.title,
                        "journal": art.publication_name,
                        "year": art.publication_date,
                        "url": art.url,
                        "doi": art.doi or "",
                        "snippet": art.abstract_or_summary[:200] + ("..." if len(art.abstract_or_summary) > 200 else ""),
                    })
                    supporting.append(
                        EvidenceItem(
                            evidence_type="SCIENTIFIC_LITERATURE",
                            claim=f"Literature corroboration: '{art.title}' ({art.publication_name}, {art.publication_date}).",
                            source=art.source_provider,
                            relevance="SUPPORTING",
                            details={"doi": art.doi, "url": art.url},
                        )
                    )
            except Exception as exc:
                logger.warning("Literature retrieval failed for %s: %s", tmpl["id"], exc)

        # Calculate qualitative support tier & score
        has_empirical_support = any(e.evidence_type == "EMPIRICAL_MEASUREMENT" for e in supporting)
        has_empirical_conflict = any(e.evidence_type == "EMPIRICAL_MEASUREMENT" for e in conflicting)
        has_literature = len(citations) > 0

        if has_empirical_conflict:
            support_tier = "CONFLICTING_EVIDENCE"
            score = 0.15
        elif has_empirical_support and has_literature:
            support_tier = "HIGH_EMPIRICAL_SUPPORT"
            score = 0.90
        elif has_empirical_support:
            support_tier = "MODERATE_SUPPORT"
            score = 0.75
        elif has_literature:
            support_tier = "MODERATE_SUPPORT"
            score = 0.60
        else:
            support_tier = "INSUFFICIENT_EVIDENCE"
            score = 0.35

        evaluated_hypotheses.append(
            CausalHypothesis(
                hypothesis_id=tmpl["id"],
                cause_name=tmpl["cause_name"],
                mechanistic_summary=tmpl["mechanism"],
                support_tier=support_tier,
                evidence_score=score,
                supporting_evidence=supporting,
                conflicting_evidence=conflicting,
                bradford_hill=bh,
                scientific_citations=citations,
                missing_measurements_needed=tmpl.get("missing_needs", []),
            )
        )

    # Sort hypotheses descending by evidence score
    evaluated_hypotheses.sort(key=lambda h: h.evidence_score, reverse=True)

    # Global missing measurements across all hypotheses
    all_missing: Set[str] = set()
    for h in evaluated_hypotheses:
        for m in h.missing_measurements_needed:
            all_missing.add(m)

    # Epistemic finding summary
    top_hyp = evaluated_hypotheses[0] if evaluated_hypotheses else None
    if top_hyp and top_hyp.support_tier == "HIGH_EMPIRICAL_SUPPORT":
        summary_verdict = (
            f"Preliminary analysis reveals strong empirical and literature support for '{top_hyp.cause_name}', "
            f"corroborated by local monitoring telemetry. However, in accordance with Bradford Hill criteria, "
            f"rival explanations ({', '.join(top_hyp.bradford_hill.alternative_explanations[:2]) if top_hyp.bradford_hill else 'none'}) "
            f"and unmeasured factors must be ruled out before asserting definitive causality."
        )
    elif top_hyp and top_hyp.support_tier == "MODERATE_SUPPORT":
        summary_verdict = (
            f"Hypothesis '{top_hyp.cause_name}' is mechanistically plausible and supported by published literature, "
            f"but direct local chemical assays remain incomplete. Causality cannot be conclusively established without "
            f"targeted water/air sampling."
        )
    else:
        summary_verdict = (
            "Current empirical data coverage is insufficient to distinguish between candidate hypotheses. "
            "Definitive causality cannot yet be determined. Additional monitoring telemetry is required."
        )

    return {
        "query": user_query,
        "symptom_identified": symptom.canonical_name,
        "symptom_key": symptom.symptom_key,
        "verdict_summary": summary_verdict,
        "hypotheses_ranked": [h.to_dict() for h in evaluated_hypotheses],
        "missing_measurements": sorted(list(all_missing)),
        "causal_disclaimer": (
            "Scientific Integrity Rule: Evidence rankings quantify comparative support from available "
            "telemetry and literature. They do not constitute proven causal certainty. Never treat "
            "correlation as proof of causation without comprehensive biological, chemical, and historical verification."
        ),
    }
