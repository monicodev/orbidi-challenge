from pydantic import BaseModel, Field

class IAECreate(BaseModel):
    iae_code: str = Field(..., example="E471.1")
    valor_tipologia: int = Field(..., ge=1, le=1000, example=850)

class IAEResponse(IAECreate):
    id: int

    class Config:
        from_attributes = True