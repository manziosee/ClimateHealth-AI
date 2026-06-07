from fastapi import APIRouter, Query
from app.services.geocoding import search_locations

router = APIRouter(prefix="/locations", tags=["locations"])


@router.get("/search")
async def location_search(q: str = Query(..., min_length=2)):
    return await search_locations(q)
