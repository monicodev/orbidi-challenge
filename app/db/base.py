# Import all models here
from app.models.iae import IAECategory
from app.models.business import Business
from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    pass