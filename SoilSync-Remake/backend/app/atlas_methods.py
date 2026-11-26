"""Read and rank the compost methods maintained in MongoDB Atlas."""

import logging
import re
from typing import Annotated, Literal

from pydantic import BaseModel, Field, ValidationError, field_validator, model_validator
from pymongo.errors import PyMongoError

from app import recipe_formulation
from app.config import get_settings
from app.waste_catalogue_v3 import ANIMAL_METHOD_IDS
from app.waste_catalogue_v3 import ANIMAL_WASTE_KINDS as STANDARD_ANIMAL_WASTE_KINDS
from app.waste_catalogue_v4 import CHICKEN_BONE_ID, FISH_PIN_BONE_ID

logger = logging.getLogger(__name__)
METHOD_IDS = {
    "hot_composting": 4,
    "cold_composting": 5,
    "bokashi_fermentation": 6,
    "blender_slurry_soil_factory": 7,
    "diy_rice_water_lab": 8,
}
METHOD_KEYS = dict(zip(METHOD_IDS, ("hot", "cold", "bokashi", "blender", "rice-water"), strict=True))
ADDITIONAL_METHODS = {
    7: ("Blender Slurry & Soil Factory", "A method for suitable plant-based scraps.", 21),
    8: ("DIY Rice Water Inoculant", "A fermentation method for selected plant-based scraps.", 28),
}
ILLUSTRATED_STAGES = {
    "blender_slurry_soil_factory": (
        ("Blend the plant scraps", 0, 2),
        ("Mix the slurry into soil", 2, 4),
        ("Cover and let it break down", 4, None),
    ),
    "diy_rice_water_lab": (
        ("Prepare the rice water", 0, 1),
        ("Separate and store the starter", 1, 3),
        ("Ferment the scraps and finish in soil", 3, None),
    ),
}
FEATURED_METHOD_IDS = (7, 8)
LINKED_METHOD_IDS = (*FEATURED_METHOD_IDS, 6)
ANIMAL_WASTE_KINDS = {**STANDARD_ANIMAL_WASTE_KINDS, FISH_PIN_BONE_ID: "bone", CHICKEN_BONE_ID: "bone"}
TIE_BREAK = {7: 0, 8: 1, 5: 2, 4: 3, 6: 4}
REJECTED_INGREDIENTS = re.compile(
    r"\b(meat|fish|seafood|chicken|beef|pork|bone\w*|dairy|milk|whey|cheese|oils?|grease|pet waste)\b",
    re.I,
)


class Ingredient(BaseModel):
    item: Annotated[str, Field(min_length=1, max_length=160)]
    percentage: Annotated[int, Field(strict=True, ge=1, le=100)]


class Recipe(BaseModel):
    recipe_name: Annotated[str, Field(min_length=1, max_length=120)]
    ingredients: Annotated[list[Ingredient], Field(min_length=1, max_length=20)]

    @model_validator(mode="after")
    def check_percentages(self):
        if sum(item.percentage for item in self.ingredients) != 100:
            raise ValueError("Recipe ingredient percentages must total 100")
        return self


# Adapted from the household and market mixes in sections 3 and 5 of the guide.
ANIMAL_MIXES = {
    6: Recipe(recipe_name="All-Rounder Kitchen Bokashi", ingredients=[
        Ingredient(item="Plain cooked rice or noodles", percentage=40),
        Ingredient(item="Vegetable and fruit scraps", percentage=40),
        Ingredient(item="Small plain meat or fish trimmings, or small bones if accepted by your kit", percentage=20),
    ]),
    8: Recipe(recipe_name="Zero-Waste Market", ingredients=[
        Ingredient(item="Vegetable trimmings", percentage=50),
        Ingredient(item="Fruit rinds", percentage=30),
        Ingredient(
            item="Small plain fish or meat trimmings, small fish bones or separate chicken bones if your sealed system accepts them",
            percentage=20,
        ),
    ]),
}
ANIMAL_INGREDIENT_WORDS = {
    "meat": {"meat", "chicken", "poultry", "beef", "pork"},
    "fish": {"fish", "seafood", "prawn", "shrimp"},
    "bone": {"bone", "bones"},
}


class CompostMethod(BaseModel):
    method_id: Literal[
        "hot_composting", "cold_composting", "bokashi_fermentation",
        "blender_slurry_soil_factory", "diy_rice_water_lab",
    ]
    recipe_id: Annotated[int, Field(strict=True, ge=4, le=8)] | None = None
    method_name: Annotated[str, Field(min_length=1, max_length=120)]
    timeline_days: Annotated[int, Field(strict=True, ge=7, le=730)]
    suitable_food_waste: Annotated[list[str], Field(min_length=1, max_length=40)]
    not_suitable_food_waste: Annotated[list[str], Field(max_length=40)]
    suitable_plants: Annotated[list[str], Field(min_length=1, max_length=40)]
    plants_to_avoid: Annotated[list[str], Field(max_length=40)]
    recipes: Annotated[list[Recipe], Field(min_length=1, max_length=25)]
    steps: Annotated[list[Annotated[str, Field(min_length=1, max_length=1500)]], Field(max_length=30)] = (
        Field(default_factory=list)
    )

    @field_validator("recipes", mode="before")
    @classmethod
    def validate_recipes(cls, recipes):
        if not isinstance(recipes, list):
            return recipes
        valid = []
        for recipe in recipes:
            try:
                valid.append(Recipe.model_validate(recipe))
            except ValidationError:
                logger.warning("Skipping an invalid Atlas recipe mix")
        return valid

    @model_validator(mode="after")
    def check_id(self):
        if self.recipe_id is not None and self.recipe_id != self.numeric_id:
            raise ValueError("Recipe ID does not match the method")
        return self

    @property
    def numeric_id(self):
        return METHOD_IDS[self.method_id]


def load_methods():
    """Accept the existing Atlas records during migration, preferring numeric copies."""
    settings = get_settings()
    uri = settings.mongodb_recipe_uri.get_secret_value()
    if not uri:
        return {}
    try:
        collection = recipe_formulation.mongo_client(uri)[settings.mongodb_recipe_database][
            recipe_formulation.COLLECTION
        ]
        rows = list(collection.find({
            "method_id": {"$in": list(METHOD_IDS)},
            "recipes": {"$exists": True},
        }))
    except (PyMongoError, ValueError) as error:
        logger.warning("Atlas method lookup failed (%s)", type(error).__name__)
        return {}

    methods = {}
    for row in rows:
        try:
            method = CompostMethod.model_validate(row)
        except ValidationError:
            logger.warning("Skipping an invalid Atlas compost method document")
            continue
        recipe_id = method.numeric_id
        if isinstance(row["_id"], int) and row["_id"] != recipe_id:
            logger.warning("Skipping a compost method with a conflicting numeric ID")
            continue
        if recipe_id not in methods or row["_id"] == recipe_id:
            methods[recipe_id] = method
    return methods


def guide_fields(method):
    plants = [
        {"id": f"{recommended}-{index}", "name": name, "type": "Garden plant",
         "recommended": recommended, "notes": "Apply only after the material has fully broken down."}
        for recommended, names in ((True, method.suitable_plants), (False, method.plants_to_avoid))
        for index, name in enumerate(names)
    ]
    guide = {
        "id": method.numeric_id,
        "method": METHOD_KEYS[method.method_id],
        "active": True,
        "name": method.method_name,
        "estimatedDays": method.timeline_days,
        "timeline": f"{method.timeline_days} days planned for weekly check-ins. Readiness varies.",
        "plants": plants,
        "suitableWaste": [
            label for label in method.suitable_food_waste
            if not REJECTED_INGREDIENTS.search(label)
        ],
        "excludedWaste": method.not_suitable_food_waste,
    }
    if method.numeric_id in ANIMAL_METHOD_IDS:
        guide["suitableWaste"].append("Small plain meat and boneless fish trimmings")
        if method.numeric_id == 6:
            guide["suitableWaste"].append("Small bones, if accepted by your sealed Bokashi kit")
            guide["excludedWaste"] = [*method.not_suitable_food_waste, "Large or thick bones"]
        else:
            guide["suitableWaste"].append(
                "Small, separate fish bones and individual chicken bones, "
                "if your sealed rice-water system accepts them"
            )
            guide["excludedWaste"] = [
                "Large meat or fish pieces"
                if "meat chunks" in label.lower() else label
                for label in method.not_suitable_food_waste
            ]
            guide["excludedWaste"].append(
                "Chicken carcasses, spines, fish skeletons, and large or thick fish bones"
            )
    stage_groups = ILLUSTRATED_STAGES.get(method.method_id)
    if stage_groups and method.steps:
        steps = [
            {"number": number, "instruction": instruction}
            for number, instruction in enumerate(method.steps, start=1)
        ]
        guide.update(
            steps=steps,
            stages=[
                {
                    "title": title,
                    "imageKey": f"{guide['method']}-{index}",
                    "steps": steps[start:end],
                }
                for index, (title, start, end) in enumerate(stage_groups, start=1)
                if steps[start:end]
            ],
            guideCredit="SoilSync recipe library",
        )
    return guide


def words(value):
    singular = {"vegetables": "vegetable", "fruits": "fruit", "beans": "bean"}
    return {singular.get(word, word) for word in re.findall(r"[a-z]+", value.lower())}


def waste_match(waste, label):
    label_words = words(label)
    kind = ANIMAL_WASTE_KINDS.get(waste.id)
    if kind:
        return 2 if ANIMAL_INGREDIENT_WORDS[kind] & label_words else 0
    names = [waste.name, *(waste.aliases or [])]
    for name in names:
        specific = words(name) - {
            "fresh", "crushed", "cooked", "whole", "spent", "ground", "scrap", "scraps",
            "peel", "peels", "skin", "skins", "rind", "rinds", "waste", "leftovers",
            "ends", "trimmings", "grounds", "cuttings", "dry", "dried", "plain", "shredded",
            "fruit", "vegetable", "leafy", "leaves", "leaf", "used", "loose",
        }
        if specific & label_words:
            return 2
    if waste.ingredient_role == "green" and (
        {"kitchen", "food"} & label_words and {"scraps", "waste"} & label_words
        and not {"fruit", "vegetable", "veggie", "veg", "peels", "trimmings"} & label_words
    ):
        return 1
    groups = {
        "fruit scrap": {"fruit", "peelings"},
        "vegetable scrap": {"vegetable", "veggie", "veggies", "veg", "greens"},
        "dry browns": {"browns"},
        "plain cooked scraps": {"leftovers"},
    }
    return int(bool(groups.get(waste.category.lower(), set()) & label_words))


def recommend(methods, waste_rows, recipe_links):
    food = [
        row for row in waste_rows
        if row.is_supported and row.ingredient_role in {"green", "mineral"}
        and (row.id in ANIMAL_WASTE_KINDS or not REJECTED_INGREDIENTS.search(row.name))
    ]
    has_animal_scraps = any(row.id in ANIMAL_WASTE_KINDS for row in food)
    candidates = []
    for method in methods.values():
        featured = method.numeric_id in FEATURED_METHOD_IDS
        linked = recipe_links.get(method.numeric_id, ())
        if (featured or has_animal_scraps) and any(row.id not in linked for row in food):
            continue
        if not food or any(
            max((waste_match(row, item) for item in method.not_suitable_food_waste), default=0)
            >= 2 for row in food if row.id not in ANIMAL_WASTE_KINDS
        ):
            continue
        matches = [max(waste_match(row, item) for item in method.suitable_food_waste) for row in food]
        mixes = []
        candidates_for_method = (
            [ANIMAL_MIXES[method.numeric_id]] if method.numeric_id in ANIMAL_MIXES else []
        ) if has_animal_scraps else method.recipes
        for recipe in candidates_for_method:
            if not has_animal_scraps and any(REJECTED_INGREDIENTS.search(part.item) for part in recipe.ingredients):
                continue
            recipe_matches = [max(waste_match(row, part.item) for part in recipe.ingredients) for row in food]
            if all(recipe_matches) and all(
                has_animal_scraps or suitable or (featured and ingredient >= 2)
                for suitable, ingredient in zip(matches, recipe_matches, strict=True)
            ):
                mixes.append((sum(recipe_matches), recipe))
        if mixes:
            score, recipe = max(mixes, key=lambda mix: mix[0])
            rank = (featured, sum(matches), score, -TIE_BREAK[method.numeric_id])
            candidates.append((rank, method, recipe))
    if not candidates:
        return None

    ordered = sorted(candidates, key=lambda result: result[0], reverse=True)
    _, method, recipe = ordered[0]
    return {
        **present_mix(method, recipe, food),
        "alternatives": [present_mix(alternate, mix, food) for _, alternate, mix in ordered[1:]],
    }


def present_mix(method, recipe, food):
    return {
        "recipeId": method.numeric_id,
        "recipeName": method.method_name,
        "templateName": recipe.recipe_name,
        "templateSource": "SoilSync Composting Guide" if recipe is ANIMAL_MIXES.get(method.numeric_id) else None,
        "matchedWaste": [row.name for row in food],
        "timelineDays": method.timeline_days,
        "suitablePlants": method.suitable_plants,
        "basis": "mix_by_volume",
        "ingredients": [
            {"id": index, "name": part.item, "percentage": part.percentage,
             "matched": any(waste_match(row, part.item) for row in food)}
            for index, part in enumerate(recipe.ingredients, 1)
        ],
    }
