from sqlalchemy import Column, Integer, String, Float, Text, DateTime, ForeignKey, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base

class Recipe(Base):
    __tablename__ = "recipes"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String, nullable=False)
    raw_text = Column(Text, nullable=False)
    ingredients = Column(JSON, nullable=False)
    instructions = Column(JSON, nullable=False)
    calories = Column(Float, nullable=True)
    health_rating = Column(Float, nullable=True)
    health_breakdown = Column(Text, nullable=True)
    taste_rating = Column(Float, nullable=True)
    cuisine_type = Column(String, nullable=True)
    dietary_tags = Column(JSON, nullable=True)
    prep_time_minutes = Column(Integer, nullable=True)
    cook_time_minutes = Column(Integer, nullable=True)
    servings = Column(Integer, nullable=True)
    nutrition_data = Column(JSON, nullable=True)
    image_url = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    user = relationship("User", backref="recipes")