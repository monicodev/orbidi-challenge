from sqlalchemy import Column, Integer, String
from app.db.session import Base

class IAECategory(Base):
    __tablename__ = "iae_categories"

    id = Column(Integer, primary_key=True, index=True)
    iae_code = Column(String(20), unique=True, index=True, nullable=False)
    valor_tipologia = Column(Integer, nullable=False) # Value between 1 and 1000