"""Method-specific animal scraps from sections 3–5 of the SoilSync guide."""

ANIMAL_WASTE_KINDS = {68: "meat", 69: "fish", 70: "bone"}
BOKASHI_SOURCE = "https://extension.wsu.edu/kitsap/bokashi-composting/"
ANIMAL_WASTE = (
    (68, "Small plain meat trimmings", "Small Animal Scraps",
     ["small boneless meat scraps", "small plain chicken trimmings", "small plain beef trimmings"],
     "Use only small, plain boneless trimmings in a sealed fermentation method. Keep out of Blender Slurry.",
     "green", (6, 8)),
    (69, "Small fish and seafood trimmings", "Small Animal Scraps",
     ["small boneless fish scraps", "small seafood offcuts", "small fish trimmings"],
     "Use only small plain scraps without large bones, hard shells, oil or sauces in a sealed fermentation method.",
     "green", (6, 8)),
    (70, "Small animal bones", "Small Animal Scraps",
     ["small chicken bones", "small fish bones", "thin small poultry bones"],
     "Use only with a sealed Bokashi system that accepts small bones. Keep out thick, large or unidentified bones.",
     "mineral", (6,)),
    (71, "Large or thick animal bones", "Slow to Break Down",
     ["beef marrow bone", "large leg bone", "thick pork bone"],
     "Keep large or thick bones out of SoilSync household recipes.", None, ()),
    (72, "Large meat or fish pieces", "Unsuitable Animal Scraps",
     ["whole meat cut", "large raw chicken piece", "whole fish"],
     "Large cuts, whole fish and unidentified animal scraps are outside these recipes.", None, ()),
)

ANIMAL_METHOD_IDS = (6, 8)
ANIMAL_LINKS = tuple((row[0], method_id) for row in ANIMAL_WASTE for method_id in row[-1])

UNSPECIFIED_GUIDE = (
    "Keep unidentified meat, fish or bones out of the batch. "
    "For clearly small, plain pieces, check the sealed fermentation guides."
)
BOKASHI_STEP = (
    "Remove packaging. Use suitable plant scraps, small plain meat or fish trimmings, "
    "or small bones if your kit accepts them. Keep out large bones, excess liquids and oil."
)
