import math
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List, Dict, Any

from app.models.iae import IAECategory
from app.models.business import Business
from app.services.calculator import calculator

def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate the great-circle distance between two points 
    on the Earth in meters.
    """
    R = 6371000  # Earth radius in meters
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)

    a = math.sin(dphi / 2)**2 + \
        math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2)**2
    
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

async def get_processed_businesses(
    db: AsyncSession, 
    lat: float, 
    lon: float, 
    radius: int
) -> List[Dict[str, Any]]:
    result_biz = await db.execute(select(Business))
    db_businesses = result_biz.scalars().all()
    
    nearby_businesses = []
    iae_codes = set()

    for b in db_businesses:
        dist = haversine_distance(lat, lon, b.latitude, b.longitude)
        if dist <= radius:
            biz_data = {
                "id": b.id,
                "name": b.name,
                "iae_code": b.iae_code,
                "rentability": b.rentability,
                "proximity_to_urban_center_m": b.proximity_to_urban_center_m,
                "distance_from_search_m": round(dist, 2),
                "coordinates": {
                    "lat": b.latitude,
                    "lon": b.longitude
                }
            }
            nearby_businesses.append(biz_data)
            iae_codes.add(b.iae_code)

    if not nearby_businesses:
        return []

    result_iae = await db.execute(
        select(IAECategory).where(IAECategory.iae_code.in_(iae_codes))
    )
    iae_map = {row.iae_code: row.valor_tipologia for row in result_iae.scalars().all()}

    for biz in nearby_businesses:
        t_val = iae_map.get(biz["iae_code"], 0)
        
        biz["metric"] = calculator.calculate_conversion_metric(
            rentability=biz["rentability"],
            typology_val=t_val,
            distance_m=biz["proximity_to_urban_center_m"]
        )

    return sorted(nearby_businesses, key=lambda x: x["metric"], reverse=True)

async def get_processed_businesses_by_id(
    db: AsyncSession, 
    business_id: str,
    lat: float, 
    lon: float, 
    radius: int
) -> List[Dict[str, Any]]:
    result_target = await db.execute(select(Business).where(Business.id == business_id))
    target_biz = result_target.scalar_one_or_none()

    if not target_biz:
        return None

    sector_prefix = target_biz.iae_code[:2]

    result_biz = await db.execute(
        select(Business).where(
            Business.iae_code.startswith(sector_prefix),
            Business.id != business_id
        )
    )
    db_candidates = result_biz.scalars().all()
    
    nearby_competitors = []
    iae_codes = set()

    for b in db_candidates:
        dist = haversine_distance(lat, lon, b.latitude, b.longitude)
        if dist <= radius:
            comp_data = {
                "id": b.id,
                "name": b.name,
                "iae_code": b.iae_code,
                "rentability": b.rentability,
                "proximity_to_urban_center_m": b.proximity_to_urban_center_m,
                "distance_from_search_m": round(dist, 2),
                "coordinates": {
                    "lat": b.latitude,
                    "lon": b.longitude
                }
            }
            nearby_competitors.append(comp_data)
            iae_codes.add(b.iae_code)

    if not nearby_competitors:
        return []

    result_iae = await db.execute(
        select(IAECategory).where(IAECategory.iae_code.in_(iae_codes))
    )
    iae_map = {row.iae_code: row.valor_tipologia for row in result_iae.scalars().all()}

    for comp in nearby_competitors:
        t_val = iae_map.get(comp["iae_code"], 0)
        
        comp["metric"] = calculator.calculate_conversion_metric(
            rentability=comp["rentability"],
            typology_val=t_val,
            distance_m=comp["proximity_to_urban_center_m"]
        )

    # Return sorted by metric (descending)
    return sorted(nearby_competitors, key=lambda x: x["metric"], reverse=True)
