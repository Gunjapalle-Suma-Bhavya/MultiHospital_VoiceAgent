"""
FastAPI router providing endpoints to check MongoDB Atlas connectivity,
fetch live JSON documents, and sync clinical records into MongoDB.
"""
from fastapi import APIRouter, HTTPException, Query
from typing import Dict, Any, List, Optional
from app.database.mongodb import (
    check_mongodb_connection,
    get_mongodb_collections_stats,
    seed_mongodb_data,
    get_collection,
)

router = APIRouter(prefix="/api/v1/mongodb", tags=["MongoDB Integration"])


@router.get("/status")
def get_mongodb_status() -> Dict[str, Any]:
    """Check MongoDB Atlas cluster connection status and database statistics."""
    conn = check_mongodb_connection()
    stats = get_mongodb_collections_stats()
    return {
        "connected": conn.get("connected", False),
        "database": conn.get("database", "nexushealth_hospital_db"),
        "error": conn.get("error"),
        "collections": stats.get("collections", {}),
    }


@router.post("/seed")
def trigger_seed_mongodb() -> Dict[str, Any]:
    """Seed or update MongoDB Atlas with baseline clinical records in JSON format."""
    result = seed_mongodb_data()
    return result


@router.get("/documents/{collection_name}")
def get_collection_documents(
    collection_name: str,
    limit: int = Query(default=50, ge=1, le=100),
    search: Optional[str] = None,
) -> Dict[str, Any]:
    """Fetch raw JSON documents from a given MongoDB collection (doctors, patients, appointments, questionnaires, hospitals)."""
    coll = get_collection(collection_name)
    if coll is None:
        raise HTTPException(
            status_code=503,
            detail="MongoDB connection unavailable or collection not found",
        )

    query = {}
    if search:
        query = {"$text": {"$search": search}}

    docs = []
    try:
        cursor = coll.find(query).limit(limit)
        for doc in cursor:
            if "_id" in doc:
                doc["_id"] = str(doc["_id"])
            docs.append(doc)
    except Exception:
        cursor = coll.find({}).limit(limit)
        for doc in cursor:
            if "_id" in doc:
                doc["_id"] = str(doc["_id"])
            docs.append(doc)

    return {
        "collection": collection_name,
        "count": len(docs),
        "documents": docs,
    }


@router.post("/documents/{collection_name}")
def insert_document(
    collection_name: str,
    payload: Dict[str, Any],
) -> Dict[str, Any]:
    """Insert a new JSON document into a MongoDB collection."""
    coll = get_collection(collection_name)
    if coll is None:
        raise HTTPException(
            status_code=503,
            detail="MongoDB connection unavailable",
        )
    try:
        res = coll.insert_one(payload)
        return {
            "status": "inserted",
            "collection": collection_name,
            "inserted_id": str(res.inserted_id),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
