from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any
from datetime import datetime

class RecipeBase(BaseModel):
    title: str
    raw_text: str
    cuisine_type: Optional[str] = None
    dietary_tags: Optional[List[str]] = None
    prep_time_minutes: Optional[int] = None
    cook_time_minutes: Optional[int] = None
    servings: Optional[int] = None

class RecipeCreate(RecipeBase):
    @validator('raw_text')
    def validate_raw_text(cls, v):
        if len(v.strip()) < 10:
            raise ValueError('Recipe text must be at least 10 characters')
        return v

class RecipeUpdate(BaseModel):
    taste_rating: Optional[float] = Field(None, ge=1, le=5)

class RecipeResponse(RecipeBase):
    id: int
    user_id: int
    ingredients: List[Dict[str, Any]]
    instructions: List[str]
    calories: Optional[float]
    health_rating: Optional[float]
    health_breakdown: Optional[str] = None
    taste_rating: Optional[float]
    nutrition_data: Optional[Dict[str, Any]]
    image_url: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True

class RecipeSearchQuery(BaseModel):
    query: Optional[str] = None
    ingredients: Optional[List[str]] = None
    cuisine_type: Optional[str] = None
    dietary_tags: Optional[List[str]] = None
    min_health_rating: Optional[float] = None
    min_taste_rating: Optional[float] = None
    max_calories: Optional[float] = None