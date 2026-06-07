from fastapi import APIRouter, Query
from app.models.schemas import LocationResult
from app.services.geocoding import search_locations

router = APIRouter(prefix="/locations", tags=["locations"])


@router.get("/search", response_model=list[LocationResult])
async def location_search(
    q: str = Query(..., min_length=2, description="City or region name"),
    count: int = Query(default=5, ge=1, le=20),
):
    return await search_locations(q, count)
