"""Approved household methods. IDs 1–3 remain historical recipes, never reassigned."""

from app.waste_catalogue_v3 import BOKASHI_SOURCE, BOKASHI_STEP

EPA = {"label": "EPA home composting", "url": "https://www.epa.gov/recycle/composting-home"}
CALRECYCLE = {
    "label": "CalRecycle home composting",
    "url": "https://calrecycle.ca.gov/organics/homecompost/",
}
RHS = {
    "label": "RHS Bokashi guide",
    "url": "https://www.rhs.org.uk/garden-inspiration/get-gardening/bokashi",
}

FERTILIZERS = [
    {
        "id": 4,
        "method": "hot",
        "name": "Hot Composting",
        "description": "An actively managed outdoor pile. Balance greens, browns, air and moisture, then allow the compost to cure.",
        "est_days_to_finish": 120,
        "timeline": "Plan for several months, including curing. Heat and time vary with the pile.",
        "stages": ["Prepare greens & browns", "Build an airy pile", "Turn, monitor & cure"],
        "steps": [
            "Remove packaging. Use chopped plant scraps with dry leaves or plain shredded cardboard.",
            "Keep meat, dairy, oil, pet waste and treated materials out of this household pile.",
            "Build a substantial pile in a ventilated bin; small piles may not retain heat.",
            "Mix greens and browns, keeping the pile damp with space for air.",
            "Check the centre with a compost thermometer; a photo cannot measure temperature.",
            "Turn and adjust moisture as needed; add dry browns if the pile becomes soggy.",
            "After active heating stops, allow curing. Use only when stable, crumbly and earthy.",
        ],
        "check_cadence": "Check heat and moisture regularly; turn as needed",
        "optimal_temp": "Measure with a compost thermometer; photos do not show heat",
        "moisture_range": "Damp, with airflow; add browns if waterlogged",
        "sources": [EPA, CALRECYCLE],
    },
    {
        "id": 5,
        "method": "cold",
        "name": "Cold Composting",
        "description": "A slower outdoor method with less turning. Add suitable plant scraps and browns, cover food and give the mix time.",
        "est_days_to_finish": 270,
        "timeline": "Often 6–12 months or longer. Readiness depends on conditions, not the calendar.",
        "stages": ["Collect suitable materials", "Add, cover & keep airy", "Wait, check & harvest"],
        "steps": [
            "Collect fruit and vegetable scraps and a separate supply of dry plant material.",
            "Remove contaminants; leave meat, dairy, grease and diseased plants out.",
            "Choose a draining, ventilated outdoor bin; add materials gradually.",
            "Cover food additions with browns to discourage pests; keep air spaces in the mix.",
            "Moisten dry material gently. Mix if compacted or smelly; avoid waterlogging.",
            "Let the material decompose slowly, with occasional checks and less frequent turning.",
            "Harvest only the fully decomposed, earthy portion. Leave recognisable scraps to continue breaking down.",
        ],
        "check_cadence": "Check occasionally and after heavy rain or dry weather",
        "optimal_temp": "No sustained high-heat target; decomposition is slower",
        "moisture_range": "Moist and draining; avoid compacted, soggy layers",
        "sources": [CALRECYCLE, EPA],
    },
    {
        "id": 6,
        "method": "bokashi",
        "name": "Bokashi Composting",
        "description": "Ferment food with Bokashi bran in an airtight bucket, then finish breaking it down in soil or a compost system. Fermented scraps are not finished compost.",
        "est_days_to_finish": 42,
        "timeline": "About 2 weeks sealed after the bucket is full, followed by further breakdown. Allow extra time before planting.",
        "stages": ["Prepare bucket & bran", "Layer, press & seal", "Ferment, then finish in soil"],
        "steps": [
            "Use a Bokashi bucket with a tap and inoculated bran; keep it shaded.",
            BOKASHI_STEP,
            "Add food in shallow layers with bran, following the kit's quantities.",
            "Press out air and close the airtight lid after each addition. Do not stir to aerate.",
            "Drain accumulated liquid using the tap every few days; follow the kit's disposal instructions.",
            "Once full, leave sealed for around 2 weeks. The fermented contents are pre-compost.",
            "Bury in an unplanted area or add to a compost system for further breakdown. Keep away from roots and wait at least 2 weeks before planting; allow longer if scraps remain.",
        ],
        "check_cadence": "Keep sealed; drain the tap every few days",
        "optimal_temp": "Keep shaded; no hot-pile target or aerating turns",
        "moisture_range": "Avoid excess liquid; drain without leaving the lid open",
        "sources": [RHS, {"label": "Washington State University Bokashi guide", "url": BOKASHI_SOURCE}],
    },
]

CURRENT_RECIPE_IDS = tuple(recipe["id"] for recipe in FERTILIZERS)
RECIPE_DETAILS = {recipe["id"]: recipe for recipe in FERTILIZERS}
WASTE_MATCHES = {
    4: (*range(1, 21), *range(31, 44)),
    5: (*range(1, 21), *range(31, 44)),
    # Food scraps, not bulk garden browns, cardboard or woody husks.
    6: (1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 13, 14, 19, 20, *range(31, 44)),
}
