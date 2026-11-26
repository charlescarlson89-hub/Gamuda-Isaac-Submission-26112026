import os

from dotenv import load_dotenv
from pymongo import MongoClient


if __name__ == "__main__":
    load_dotenv()
    uri = os.getenv("MONGODB_ATLAS_CLUSTER_URI")
    if not uri:
        raise SystemExit("Add MONGODB_ATLAS_CLUSTER_URI to your private .env.")

    expected = {
        "test_collection": "test-index-1",
        "test_collection_pdf": "test-index-pdf",
    }
    with MongoClient(uri, serverSelectionTimeoutMS=8000, timeoutMS=12000) as client:
        database = client["test_db"]
        all_ready = True
        for collection, name in expected.items():
            index = next(iter(database[collection].list_search_indexes(name)), None)
            status = index.get("status", "UNKNOWN") if index else "MISSING"
            queryable = bool(index and index.get("queryable"))
            print(f"{collection}/{name}: {status}, queryable={queryable}")
            all_ready = all_ready and status == "READY" and queryable
    if not all_ready:
        raise SystemExit(1)
