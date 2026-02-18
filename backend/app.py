from fastapi import FastAPI, Query
from pymongo import MongoClient
import json

app = FastAPI()

client = MongoClient("mongodb://localhost:27017/")
db = client["pdf_text_db"]
collection = db["extracted_text"]

# Create text index on raw_text field for full-text search
try:
    collection.create_index([("raw_text", "text")])
    print("✓ Text index created on 'raw_text' field")
except Exception as e:
    print(f"Note: Text index creation: {e}")


@app.get("/search")
def search(q: str = Query(default="")):
    if not q.strip():
        return []

    results = []
    search_term = q.strip().lower()

    try:
        # Step 1: Find documents containing the search term in raw_text
        cursor = collection.find(
            {"$text": {"$search": search_term}},
            {"_id": 0, "structured_json": 1, "file_name": 1}
        )

        for doc in cursor:
            structured = doc.get("structured_json")
            file_name = doc.get("file_name", "Unknown")

            # Step 2: Parse JSON string to actual list
            if isinstance(structured, str):
                try:
                    cleaned = structured.strip()
                    if cleaned.startswith("```"):
                        cleaned = cleaned.split("```")[1]
                        if cleaned.startswith("json"):
                            cleaned = cleaned[4:]
                    
                    structured = json.loads(cleaned)
                except json.JSONDecodeError as e:
                    print(f"Failed to parse JSON for {file_name}: {e}")
                    continue

            # Step 3: Filter products - ONLY include if search term matches
            if isinstance(structured, list):
                for item in structured:
                    product_name = str(item.get("product_name", "")).lower()
                    description = str(item.get("description", "")).lower()
                    
                    # Strict filtering: search term must be in product name OR description
                    if search_term in product_name or search_term in description:
                        results.append(item)

    except Exception as e:
        print("ERROR:", e)
        return {"error": str(e)}

    # Return only matched products, empty array if none found
    return results