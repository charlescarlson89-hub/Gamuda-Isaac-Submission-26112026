"""Separate thin fish pin bones from spines and other structural bones."""

import re

SMALL_ANIMAL_BONE_ID = 70
SMALL_ANIMAL_BONE_GUIDANCE = (
    "Use only clearly small, thin bones with sealed Bokashi or the DIY rice-water Bokashi "
    "process, and only if your system accepts them. Keep out spines, backbones, large or "
    "thick bones and bones you cannot identify."
)
SMALL_ANIMAL_BONE_RICE_WATER_LINK = (SMALL_ANIMAL_BONE_ID, 8)

REJECTED_BONE_ID = 71
FISH_PIN_BONE_ID = 73
FISH_PIN_BONE = (
    FISH_PIN_BONE_ID, "Small fish pin bones", "Small Animal Scraps",
    ["thin fish pin bones", "small fine fish bones", "fine fish pin bones"],
    "Use only clearly thin, small fish pin bones in sealed fermentation. Keep out spines, backbones and thick bones.",
    "mineral", (6, 8),
)
SMALL_FISH_BONE = (
    FISH_PIN_BONE_ID, "Small fish bones", "Small Animal Scraps",
    ["small fish bones", "thin fish pin bones", "small tilapia bones"],
    "Use only clearly small, separate fish bones in a sealed fermentation system that accepts them. "
    "Keep out fish spines, skeletons and large or thick bones, such as a large tuna bone.",
    "mineral", (6, 8),
)
CHICKEN_BONE_ID = 74
CHICKEN_BONE = (
    CHICKEN_BONE_ID, "Separate chicken bones", "Small Animal Scraps",
    ["chicken bones", "chicken drumstick bone", "chicken wing bone", "chicken thigh bone"],
    "Use separate chicken bones only in the sealed DIY rice-water process if your system accepts them. "
    "Keep out chicken carcasses, spines and backbones.",
    "mineral", (8,),
)
REJECTED_BONE_GUIDANCE = (
    "Keep chicken carcasses, spines, backbones, fish skeletons and large or thick fish bones "
    "out of SoilSync household recipes."
)
REJECTED_BONE_ALIASES = [
    "beef marrow bone", "large leg bone", "thick pork bone", "fish spine", "fish backbone",
    "vertebrae", "chicken carcass", "chicken spine", "large tuna bone", "thick fish bone",
]
BONE_RULES_VERSION = 2
BONE_DETAILS = {
    70: (
        ["small chicken bones", "thin small poultry bones"],
        "Use only clearly small bones in a sealed Bokashi system that accepts them. "
        "Keep out spines, backbones, large or thick bones and bones you cannot identify.",
    ),
    71: (
        ["beef marrow bone", "large leg bone", "thick pork bone", "fish spine", "fish backbone", "vertebrae"],
        "Keep fish spines, backbones and other large or thick bones out of all SoilSync household recipes.",
    ),
}

SERVINGWARE = re.compile(
    r"(?:[\w-]+ )*(?:cutlery|utensils?|forks?|knives|knife|spoons?|chopsticks?|plates?|bowls?|"
    r"saucers?|tableware|serving dishes?)",
    re.I,
)
STRUCTURAL_BONE = re.compile(
    r"\b(?:spines?|back\s*bones?|vertebra\w*|skeletons?|carcass(?:es)?|rib racks?)\b", re.I,
)
BONE_WORD = re.compile(r"\b(?:bones?|pin\s*bones?)\b", re.I)
CHICKEN = re.compile(r"\bchicken\b", re.I)
FISH = re.compile(r"\b(?:fish|tilapia|tuna|salmon|sardines?|mackerel|cod|anchov(?:y|ies))\b", re.I)
LARGE_BONE = re.compile(
    r"\b(?:large|thick|big|heavy|oversized)\b.*\b(?:bones?|pin\s*bones?)\b"
    r"|\b(?:bones?|pin\s*bones?)\b.*\b(?:large|thick|big|heavy|oversized)\b",
    re.I,
)
SMALL_BONE = re.compile(
    r"\b(?:small|fine|thin|tiny)\b.*\bbones?\b|\bpin\s*bones?\b"
    r"|\bbones?\b.*\b(?:small|fine|thin|tiny)\b",
    re.I,
)


def is_servingware(name):
    if not name or re.search(r"\b(?:on|with|containing|of)\b", name, re.I):
        return False
    return bool(SERVINGWARE.fullmatch(name.strip(" .")))


def resolve_bone_detection(waste_id, name):
    if STRUCTURAL_BONE.search(name):
        return REJECTED_BONE_ID
    if BONE_WORD.search(name):
        if CHICKEN.search(name):
            return SMALL_ANIMAL_BONE_ID if SMALL_BONE.search(name) and not LARGE_BONE.search(name) else CHICKEN_BONE_ID
        if LARGE_BONE.search(name):
            return REJECTED_BONE_ID
        if FISH.search(name):
            if SMALL_BONE.search(name):
                return FISH_PIN_BONE_ID
            if re.search(r"\btuna\b", name, re.I):
                return REJECTED_BONE_ID
            # The vision prompt permits this ID only when size is visible.
            return FISH_PIN_BONE_ID if waste_id == FISH_PIN_BONE_ID else None
        if SMALL_BONE.search(name) and re.search(r"\bpin\s*bones?\b", name, re.I):
            return FISH_PIN_BONE_ID
    return waste_id


def has_legacy_bone_detection(result):
    return result.get("bone_rules") != BONE_RULES_VERSION and any(
        item.get("waste_type_id") in {22, SMALL_ANIMAL_BONE_ID, REJECTED_BONE_ID, FISH_PIN_BONE_ID}
        or BONE_WORD.search(item.get("name") or "")
        for item in result.get("items", ())
    )
