from sqlalchemy import Column, String, Float
from app.db.session import Base

class Business(Base):
    __tablename__ = "businesses"

    id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False)
    iae_code = Column(String, nullable=False)
    rentability = Column(Float)
    proximity_to_urban_center_m = Column(Float)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)