import json
from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

# Core and Security
from app.core.config import settings
from app.core.security import get_current_user, create_access_token
from app.core.redis import redis_client

# DB and Services
from app.db.session import get_db, SessionLocal, engine, Base
from app.services.business_logic import get_processed_businesses, get_processed_businesses_by_id

# Models and Schemas
from app.models.iae import IAECategory
from app.models.business import Business
from app.schemas.business import BusinessList, CompetitorList
from app.schemas.iae import IAECreate, IAEResponse

async def seed_database():
    """Forced synchronization and seeding."""
    print("LOG: Starting seed_database process...")
    async with SessionLocal() as db:
        try:
            # 1. Check IAE Categories
            try:
                iae_stmt = await db.execute(select(IAECategory))
                existing_iae = iae_stmt.scalars().first()
                if not existing_iae:
                    print("LOG: Seeding IAE Categories...")
                    db.add_all([
                        IAECategory(iae_code="E471.1", valor_tipologia=800),
                        IAECategory(iae_code="G651.2", valor_tipologia=450),
                        IAECategory(iae_code="G651.3", valor_tipologia=470),
                        IAECategory(iae_code="G651.4", valor_tipologia=490)
                    ])
                    await db.commit()
                    print("LOG: IAE Categories inserted.")
            except Exception as e:
                print(f"LOG: IAE table check failed (maybe doesn't exist?): {e}")

            # 2. Check Businesses
            try:
                biz_stmt = await db.execute(select(Business))
                if not biz_stmt.scalars().first():
                    print("LOG: Seeding Businesses...")
                    db.add_all([
                        Business(
                            id="biz_001", name="Madrid Central Grill", 
                            iae_code="E471.1", rentability=85.0, 
                            proximity_to_urban_center_m=100.0,
                            latitude=40.4167, longitude=-3.7037
                        ),
                        Business(
                            id="biz_002", name="Retiro Coffee", 
                            iae_code="G651.2", rentability=65.0, 
                            proximity_to_urban_center_m=200.0,
                            latitude=40.4150, longitude=-3.6850
                        ),
                        Business(
                            id="biz_003", name="Madrid Central Coffee", 
                            iae_code="G651.3", rentability=68.0, 
                            proximity_to_urban_center_m=190.0,
                            latitude=40.4130, longitude=-3.6810
                        ),
                        Business(
                            id="biz_004", name="Sol Coffee", 
                            iae_code="G651.4", rentability=62.0, 
                            proximity_to_urban_center_m=90.0,
                            latitude=40.4230, longitude=-3.6110
                        )
                    ])
                    await db.commit()
                    print("LOG: Businesses inserted.")
            except Exception as e:
                print(f"LOG: Business table check failed: {e}")

        except Exception as global_e:
            await db.rollback()
            print(f"CRITICAL: Global seeding error -> {global_e}")

@asynccontextmanager
async def lifespan(app: FastAPI):
    print(f"DEBUG: Registered tables: {list(Base.metadata.tables.keys())}")
    
    async with engine.begin() as conn:
        try:
            await conn.run_sync(Base.metadata.create_all)
        except Exception as e:
            print(f"LOG: Table creation skipped or already handled: {e}")
    
    try:
        await seed_database()
    except Exception as e:
        print(f"LOG: Seeding skipped (likely already done): {e}")

    redis_client.init()
    yield
    await redis_client.close()


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    lifespan=lifespan
)

# --- AUTHENTICATION ---

@app.post("/api/v1/auth/token", tags=["Auth"])
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()]
):
    """Obtain a JWT token. Password is 'admin'."""
    if form_data.password != "admin":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = create_access_token(data={"sub": form_data.username})
    return {"access_token": token, "token_type": "bearer"}

# --- BUSINESS ENDPOINTS ---

@app.get(
    "/api/v1/businesses/search", 
    response_model=BusinessList,
    tags=["Commercials"]
)
async def search_nearby_businesses(
    lat: float, 
    lon: float, 
    radius: int,
    db: AsyncSession = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    """
    Returns businesses filtered by radius and ranked by success probability.
    Results are cached in Redis for 5 minutes.
    """
    cache_key = f"search:{lat}:{lon}:{radius}"
    
    cached_result = await redis_client.get_cache(cache_key)
    if cached_result:
        return cached_result

    # Process businesses using DB data
    processed_list = await get_processed_businesses(db, lat, lon, radius)
    
    response = {
        "count": len(processed_list),
        "businesses": processed_list
    }

    await redis_client.set_cache(cache_key, response, expire=300)
    return response

@app.get(
    "/api/v1/businesses/{business_id}/competitors", 
    response_model=CompetitorList,
    tags=["Commercials"]
)
async def get_business_competitors(
    business_id: str,
    lat: float,
    lon: float,
    radius: int,
    db: AsyncSession = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    cache_key = f"search:{business_id}:{lat}:{lon}:{radius}"
    
    cached_result = await redis_client.get_cache(cache_key)
    if cached_result:
        return cached_result

    # Process businesses by id using DB data
    processed_list = await get_processed_businesses_by_id(db, business_id, lat, lon, radius)
    
    response = {
        "count": len(processed_list),
        "competitors": processed_list
    }

    await redis_client.set_cache(cache_key, response, expire=300)
    return response

@app.post(
    "/api/v1/iae", 
    response_model=IAEResponse, 
    status_code=status.HTTP_201_CREATED,
    tags=["Admin"]
)
async def upsert_iae_category(
    iae_data: IAECreate, 
    db: AsyncSession = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    """Adds or updates IAE typology values for the scoring metric."""
    query = select(IAECategory).where(IAECategory.iae_code == iae_data.iae_code)
    result = await db.execute(query)
    db_entry = result.scalar_one_or_none()

    if db_entry:
        db_entry.valor_tipologia = iae_data.valor_tipologia
    else:
        db_entry = IAECategory(**iae_data.model_dump())
        db.add(db_entry)

    await db.commit()
    await db.refresh(db_entry)
    return db_entry