"""Print the approved recipe library as JSON for import into MongoDB Atlas."""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.recipe_formulation import approved_documents  # noqa: E402

print(json.dumps(approved_documents(), ensure_ascii=True, indent=2))
