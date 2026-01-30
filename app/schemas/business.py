from pydantic import BaseModel
from typing import List, Optional

class Coordinates(BaseModel):
    lat: float
    lon: float

class BusinessBase(BaseModel):
    id: str
    name: str
    iae_code: str
    rentability: int
    proximity_to_urban_center_m: float
    coordinates: Coordinates

class BusinessResponse(BusinessBase):
    metric: float # Calculated sigmoidal value

class BusinessList(BaseModel):
    count: int
    businesses: List[BusinessResponse]

class CompetitorList(BaseModel):
    count: int
    competitors: List[BusinessResponse]