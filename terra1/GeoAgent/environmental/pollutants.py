
POLLUTANTS = {
    "mercury": {
        "type": "heavy metal",
        "form": "solid or dissolved in water",
        "pathways": ["water", "soil", "food chain"],
        "short_term_impacts": [
            "Toxicity to aquatic organisms",
            "Potential neurological harm in exposed organisms"
        ],
        "long_term_impacts": [
            "Persistence in the environment",
            "Conversion to methylmercury under suitable conditions",
            "Bioaccumulation in aquatic food webs"
        ],
        "earth_impact": [
            "Contamination of aquatic ecosystems",
            "Potential impacts on biodiversity"
        ]
    },
    "microplastics": {
        "type": "solid pollutant",
        "form": "solid particles",
        "pathways": ["water", "soil", "air"],
        "short_term_impacts": [
            "Ingestion by aquatic organisms"
        ],
        "long_term_impacts": [
            "Environmental persistence",
            "Transport through food webs"
        ],
        "earth_impact": [
            "Widespread contamination of ecosystems"
        ]
    },
    "sulfur dioxide": {
        "type": "gaseous pollutant",
        "form": "gas",
        "pathways": ["air"],
        "short_term_impacts": [
            "Respiratory irritation",
            "Formation of atmospheric particles"
        ],
        "long_term_impacts": [
            "Contribution to acid deposition",
            "Damage to sensitive ecosystems"
        ],
        "earth_impact": [
            "Acidification of soil and freshwater"
        ]
    }
}


def explain_pollutant(name: str) -> dict:
    key = name.lower().strip()
    pollutant = POLLUTANTS.get(key)

    if not pollutant:
        return {
            "found": False,
            "pollutant": name,
            "message": "Scientific research is required."
        }

    return {
        "found": True,
        "pollutant": key,
        **pollutant
    }
