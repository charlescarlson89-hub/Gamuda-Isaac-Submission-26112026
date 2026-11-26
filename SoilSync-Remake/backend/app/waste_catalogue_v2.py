"""Waste entries and method links checked against the SoilSync Atlas recipe library."""

# ID, name, category, aliases, description, ingredient role, recipe IDs.
NEW_WASTE = (
    (54, "Guava trimmings", "Fruit Scrap", ["guava peels", "jambu batu peel"],
     "Plain guava skins and attached flesh. Cut into small pieces.", "green", (4, 5, 7, 8)),
    (55, "Carrot tops", "Vegetable Scrap", ["carrot greens", "carrot leaves", "daun lobak merah"],
     "The leafy green tops cut from carrots.", "green", (4, 5, 7, 8)),
    (56, "Spinach trimmings", "Vegetable Scrap", ["spinach stalks", "spinach leaves", "bayam stems"],
     "Plain spinach leaves and tender stems. Remove ties or packaging.", "green", (4, 5, 7, 8)),
    (57, "Plain cooked rice", "Plain Cooked Scraps", ["leftover white rice", "plain steamed rice", "nasi putih"],
     "Use a small amount of unseasoned cooked rice. Leave out rice with oil, sauces or visible spoilage.",
     "green", (6, 7, 8)),
    (58, "Stale plain bread", "Plain Cooked Scraps", ["stale bread", "plain bread crusts", "roti kosong"],
     "Plain bread without mold, fillings, butter or sauce. Use a small amount.", "green", (6, 7, 8)),
    (59, "Plain cooked noodles", "Plain Cooked Scraps", ["unseasoned noodles", "plain cooked pasta"],
     "Plain drained noodles without oil or sauces. Use the Bokashi guide.", "green", (6,)),
    (60, "Plain tofu offcuts", "Plain Cooked Scraps", ["tofu scraps", "unseasoned tofu", "plain tauhu"],
     "Unseasoned tofu pieces without sauce or frying oil. Use the Bokashi guide.", "green", (6,)),
    (61, "Mangosteen rinds", "Fruit Scrap", ["mangosteen peel", "manggis peel", "kulit manggis"],
     "Thick mangosteen rind. Chop the rind for the Bokashi batch.", "green", (6,)),
    (62, "Durian husks", "Fruit Scrap", ["durian shells", "durian rind", "kulit durian"],
     "Hard durian husks. Keep whole shells out of household batches. Use only small chopped pieces in the Atlas Bokashi mix.",
     "green", (6,)),
    (63, "Untreated sawdust", "Dry Browns", ["clean sawdust", "unpainted wood sawdust"],
     "Fine sawdust from plain untreated wood. Use only as a recipe ingredient.", "brown", (4, 8)),
    (64, "Plain paper egg cartons", "Dry Browns", ["uncoated egg cartons", "paper egg trays"],
     "Tear up clean, plain paper egg cartons. Keep plastic and foam cartons out.", "brown", (4, 5, 7)),
    (65, "Plain shredded newspaper", "Dry Browns", ["uncoated newsprint", "plain newspaper"],
     "Shredded, uncoated newspaper. Leave out glossy inserts.", "brown", (4, 5, 7)),
    (66, "Hard coconut shells", "Slow to Break Down", ["whole coconut shell", "hard coconut husk"],
     "Hard coconut shells and husks take too long to break down for these household recipes.", None, ()),
    (67, "Moldy cooked leftovers", "Spoiled Cooked Scraps", ["mouldy cooked food", "rotten cooked leftovers"],
     "Keep cooked leftovers with visible mold or a rotten smell out of SoilSync household batches.", None, ()),
)

COMMON_RECIPE_WASTE = (
    "Banana peels", "Coffee grounds", "Crushed eggshells", "Apple cores", "Carrot peels", "Potato peels",
    "Leafy vegetable trimmings", "Cucumber peels", "Melon rinds", "Pumpkin scraps", "Tea leaves", "Pea pods",
    "Broccoli stems", "Plain shredded cardboard", "Tomato scraps", "Pear cores", "Whole Potato", "Papaya peels",
    "Mango peels", "Pineapple trimmings", "Citrus peels", "Dragon fruit peels", "Rambutan peels", "Avocado peels",
    "Onion skins", "Cabbage trimmings", "Bean trimmings", "Cauliflower trimmings", "Ginger peels", "Chayote peels",
)

ATLAS_LINKS = (
    (name, recipe_id)
    for recipe_id, names in (
        (7, (*COMMON_RECIPE_WASTE, "Plain paper")),
        (8, COMMON_RECIPE_WASTE),
    )
    for name in names
)
WASTE_LINKS = (*ATLAS_LINKS, *((row[1], recipe_id) for row in NEW_WASTE for recipe_id in row[-1]))


def waste_values(row):
    index, name, category, aliases, description, role, _ = row
    return {
        "id": index, "name": name, "category": category, "is_supported": role is not None,
        "rejection_reason": category if role is None else None, "guide_recommendation": description,
        "aliases": aliases, "description": description, "ingredient_role": role,
    }
