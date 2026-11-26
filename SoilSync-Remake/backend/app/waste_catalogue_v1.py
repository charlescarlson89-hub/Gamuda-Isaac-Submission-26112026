"""Reference data for the waste catalogue expansion. Keep IDs and migration data stable."""

SOURCE = "https://www.epa.gov/recycle/composting-home"

# ID, alternate names, description, ingredient role.
DETAILS = {
    1: (["banana skin"], "The outer peel of a banana. Remove produce stickers before chopping.", "green"),
    2: (["used coffee grounds", "spent coffee grounds"], "Damp grounds left after brewing coffee. Break up compacted clumps.", "green"),
    3: (["eggshell fragments"], "Hard shell fragments from eggs. Crush well and expect visible pieces to break down slowly.", "mineral"),
    4: (["apple centres"], "The fibrous centre and attached flesh left after eating an apple.", "green"),
    5: (["carrot skins"], "Thin outer peel and small end trimmings from carrots.", "green"),
    6: (["potato skins"], "Peel from plain potatoes. Keep oily, seasoned leftovers separate.", "green"),
    7: (["lettuce trimmings", "sawi trimmings", "kangkung trimmings"], "Wilted leaves and stems from leafy vegetables. Mix with dry material to prevent matting.", "green"),
    8: (["cucumber skins"], "Thin, moist outer peel from cucumbers. Mix with dry browns.", "green"),
    9: (["watermelon rind", "honeydew rind"], "Thick outer rind of a melon. Chop into small pieces.", "green"),
    10: (["pumpkin peel", "squash trimmings"], "Plain pumpkin skins, flesh trimmings and fibrous pulp. Chop tough skin.", "green"),
    11: (["spent tea leaves", "loose-leaf tea residue"], "Loose leaves left after brewing tea. Empty the leaves out of bags unless their material is known.", "green"),
    12: (["maize husks", "corn wrappers"], "Fibrous leaves surrounding a corn cob. Cut up and add to an outdoor pile.", "brown"),
    13: (["snow pea pods"], "Empty or trimmed pods from peas, including tough ends.", "green"),
    14: (["broccoli stalks"], "Thick stem and stalk pieces left after trimming broccoli. Chop before mixing.", "green"),
    15: (["uncoated cardboard"], "Dry, plain cardboard with tape, labels and glossy coatings removed. Shred for airflow.", "brown"),
    16: (["dried fallen leaves", "leaf litter"], "Dry fallen leaves without litter or chemical contamination. Mix into a pile or use to cover scraps.", "brown"),
    17: (["uncoated paper"], "Plain dry paper without wax, coatings or plastic film. Shred and mix in small layers.", "brown"),
    18: (["small branches", "untreated sticks"], "Small pieces of clean woody material. Use sparingly for structure or at the bottom of a pile.", "brown"),
    19: (["tomato trimmings"], "Tomato tops, cores and plain fruit trimmings. Mix the wet scraps with dry browns.", "green"),
    20: (["pear centres"], "The fibrous core and attached flesh left after eating a pear.", "green"),
    21: (["plastic wrapper", "plastic bottle", "plastic food container"], "Synthetic film or rigid plastic from food packaging. Separate it from organic scraps.", None),
    22: (["meat scraps", "fish scraps", "bones"], "Animal flesh, skin or bones from cooking and meals. Keep out of SoilSync household recipes.", None),
    23: (["cheese leftovers", "spoiled milk", "yoghurt"], "Milk-based leftovers. Keep out of SoilSync household recipes.", None),
    24: (["grease", "frying oil"], "Oil or grease left from cooking. Keep it separate from compost materials.", None),
    25: (["glass jar", "broken glass"], "Glass containers or fragments. Separate from food scraps and handle sharp pieces carefully.", None),
    26: (["food tin", "aluminium can"], "Metal food or drink packaging. Empty and separate it for the appropriate local route.", None),
    27: (["painted wood", "pressure-treated wood"], "Wood treated with paint, preservatives or similar coatings. Keep it out of compost.", None),
    28: (["dog waste", "cat litter"], "Pet droppings and soiled litter. Keep away from household compost and edible gardens.", None),
    29: (["chemical residue on scraps"], "Food or plant scraps known to be contaminated with cleaners or other chemicals.", None),
    30: (["fruit label", "produce label"], "Small adhesive labels attached to produce. Peel them off before composting.", None),
    31: (["plain whole potato", "whole kentang"], "A plain potato tuber. Cut it into small pieces before mixing it with other scraps.", "green"),
    32: (["papaya skin", "papaya fruit scrap", "betik peel", "kulit betik"], "Outer peel and plain flesh trimmings from papaya. Chop and mix with dry browns for an outdoor pile.", "green"),
    33: (["mango skin", "mangga peel"], "Mango skin and attached flesh. Separate the large woody stone before using this recipe.", "green"),
    34: (["pineapple skin", "nanas rind"], "Plain pineapple peel and core trimmings. Chop tough pieces before adding.", "green"),
    35: (["orange peel", "lemon peel", "lime peel"], "Plain peels from citrus fruit. Chop and mix with other scraps rather than adding a thick layer.", "green"),
    36: (["dragon fruit skin", "pitaya peel"], "The thick outer skin and attached flesh from dragon fruit. Cut into small pieces.", "green"),
    37: (["rambutan skin"], "Hairy outer peel from rambutan. Separate the seed and cut tough rind into pieces.", "green"),
    38: (["avocado skin"], "Avocado skin and plain flesh trimmings. Separate the large stone.", "green"),
    39: (["onion outer layers", "shallot skins"], "Thin outer layers and ends from onions or shallots. Remove rubber bands and labels.", "green"),
    40: (["cabbage core", "outer cabbage leaves"], "Outer cabbage leaves, core pieces and other plain trimmings. Chop thick pieces.", "green"),
    41: (["long bean ends", "green bean trimmings"], "Stem ends and plain trimmings from green beans or long beans.", "green"),
    42: (["cauliflower stems", "cauliflower leaves"], "Leaves and thick stem trimmings from cauliflower. Chop stalks first.", "green"),
    43: (["ginger skin", "halia peel"], "Plain ginger peel and small root offcuts. Cut large pieces into smaller ones.", "green"),
    44: (["chayote skin", "labu siam peel"], "Plain peel and trimmings from chayote. Remove any attached produce stickers.", "green"),
    45: (["fruit pits", "avocado pit", "mango stone"], "Large hard fruit stones. Set these aside because they break down too slowly for these recipes.", None),
    46: (["oily food", "sauced leftovers", "fried leftovers"], "Food leftovers visibly coated in oil or sauce. Keep out of SoilSync's supported household recipes.", None),
    47: (["tea bag", "coffee pod", "coffee capsule"], "Used tea bags and coffee capsules with uncertain packaging materials. Separate loose contents from the packaging.", None),
    48: (["used paper coffee filter", "uncoated coffee filter"], "A plain paper filter used for brewing coffee. Tear it up for hot or cold composting; leave reusable mesh and plastic filters out.", "brown"),
    49: (["untreated wood chip", "clean wood chips"], "Small chips from untreated wood. Mix a little into an outdoor pile for structure; they break down slowly.", "brown"),
    50: (["compostable takeaway box", "compostable cutlery", "compostable bag"], "Food packaging labelled compostable. SoilSync's household methods do not accept it; use a local service only if it accepts the specific product.", None),
    51: (["glossy paper", "laminated carton", "wax-coated cardboard"], "Glossy, waxed or laminated paper or board. Keep it out of the compost and check what your local collection accepts.", None),
    52: (["diseased leaves", "diseased garden trimmings"], "Garden trimmings with known disease or pest infestation. Keep them out of the pile and follow local green waste guidance.", None),
    53: (["seedy weeds", "weeds gone to seed"], "Weeds carrying seeds. Keep them out of SoilSync's household recipes because seeds may survive and spread.", None),
}

EXISTING_EXTRA_WASTE = {31: ("Whole Potato", "Vegetable Scrap", True)}

EXTRA_WASTE = {
    32: ("Papaya peels", "Fruit Scrap", True),
    33: ("Mango peels", "Fruit Scrap", True),
    34: ("Pineapple trimmings", "Fruit Scrap", True),
    35: ("Citrus peels", "Fruit Scrap", True),
    36: ("Dragon fruit peels", "Fruit Scrap", True),
    37: ("Rambutan peels", "Fruit Scrap", True),
    38: ("Avocado peels", "Fruit Scrap", True),
    39: ("Onion skins", "Vegetable Scrap", True),
    40: ("Cabbage trimmings", "Vegetable Scrap", True),
    41: ("Bean trimmings", "Vegetable Scrap", True),
    42: ("Cauliflower trimmings", "Vegetable Scrap", True),
    43: ("Ginger peels", "Vegetable Scrap", True),
    44: ("Chayote peels", "Vegetable Scrap", True),
    45: ("Large fruit stones", "Slow to Break Down", False),
    46: ("Greasy prepared leftovers", "Fats and Oils", False),
    47: ("Tea bags and coffee capsules", "Mixed Packaging", False),
    48: ("Plain paper coffee filters", "Dry Browns", True),
    49: ("Untreated wood chips", "Dry Browns", True),
    50: ("Compostable food packaging", "Special Collection", False),
    51: ("Coated paper and cartons", "Mixed Packaging", False),
    52: ("Diseased garden trimmings", "Plant Health", False),
    53: ("Weeds with seeds", "Plant Health", False),
}


def recipes_for(waste_id):
    if waste_id in (48, 49):
        return (4, 5)
    entry = EXTRA_WASTE.get(waste_id) or EXISTING_EXTRA_WASTE.get(waste_id)
    return (4, 5, 6) if entry and entry[2] else ()


def details_for(waste_id):
    aliases, description, ingredient_role = DETAILS[waste_id]
    return {
        "description": description,
        "aliases": aliases,
        "ingredient_role": ingredient_role,
        "reference_url": SOURCE,
    }
