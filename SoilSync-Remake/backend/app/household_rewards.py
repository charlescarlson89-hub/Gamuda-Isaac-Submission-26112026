"""Catalogue entries for the household reward concepts."""

HOUSEHOLD_REWARDS = (
    (24, "vinda-tissue", "Vinda Facial Tissue", 60,
     "Made with 100% virgin wood pulp from renewable plant fibres."),
    (25, "vinda-kitchen-paper", "Vinda Kitchen Paper", 90,
     "Made with 100% virgin wood pulp from renewable plant fibres."),
    (26, "petpet-diapers", "PETPET Pants Diapers", 150,
     "The absorbent core uses wood pulp from renewable plant fibres."),
)


def household_reward_rows():
    return [
        {
            "id": reward_id,
            "slug": slug,
            "title": title,
            "points_cost": points,
            "category": "Household Essentials",
            "kind": slug,
            "description": description,
            "is_active": True,
            "prototype_only": True,
        }
        for reward_id, slug, title, points, description in HOUSEHOLD_REWARDS
    ]
