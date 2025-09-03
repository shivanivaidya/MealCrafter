from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Optional
import json

from app.database import get_db, get_chroma_collection
from app.models.recipe import Recipe
from app.models.user import User
from app.schemas.recipe import RecipeResponse, RecipeSearchQuery
from app.core.security import get_current_user

router = APIRouter()

@router.post("/", response_model=List[RecipeResponse])
async def search_recipes(
    search_query: RecipeSearchQuery,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    collection = get_chroma_collection()
    
    where_conditions = {"user_id": current_user.id}
    
    if search_query.min_health_rating:
        where_conditions["health_rating"] = {"$gte": search_query.min_health_rating}
    
    if search_query.min_taste_rating:
        where_conditions["taste_rating"] = {"$gte": search_query.min_taste_rating}
    
    if search_query.max_calories:
        where_conditions["calories"] = {"$lte": search_query.max_calories}
    
    if search_query.cuisine_type:
        where_conditions["cuisine_type"] = search_query.cuisine_type
    
    query_text = ""
    if search_query.query:
        query_text = search_query.query
    
    if search_query.ingredients:
        query_text += " " + " ".join(search_query.ingredients)
    
    if search_query.dietary_tags:
        query_text += " " + " ".join(search_query.dietary_tags)
    
    recipe_ids = []
    
    if query_text.strip():
        results = collection.query(
            query_texts=[query_text],
            where=where_conditions,
            n_results=50
        )
        
        if results and results['metadatas'] and results['metadatas'][0]:
            recipe_ids = [
                metadata['recipe_id'] 
                for metadata in results['metadatas'][0]
            ]
    else:
        results = collection.get(
            where=where_conditions
        )
        
        if results and results['metadatas']:
            recipe_ids = [
                metadata['recipe_id'] 
                for metadata in results['metadatas']
            ]
    
    if not recipe_ids:
        return []
    
    recipes = db.query(Recipe).filter(
        Recipe.id.in_(recipe_ids),
        Recipe.user_id == current_user.id
    ).all()
    
    recipes_dict = {recipe.id: recipe for recipe in recipes}
    ordered_recipes = [recipes_dict[rid] for rid in recipe_ids if rid in recipes_dict]
    
    return ordered_recipes

@router.get("/ingredients", response_model=List[str])
async def search_by_ingredients(
    ingredients: str = Query(..., description="Comma-separated list of ingredients"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    ingredient_list = [ing.strip() for ing in ingredients.split(",")]
    
    collection = get_chroma_collection()
    
    query_text = " ".join(ingredient_list)
    results = collection.query(
        query_texts=[query_text],
        where={"user_id": current_user.id},
        n_results=20
    )
    
    recipe_ids = []
    if results and results['metadatas'] and results['metadatas'][0]:
        recipe_ids = [
            metadata['recipe_id'] 
            for metadata in results['metadatas'][0]
        ]
    
    if not recipe_ids:
        return []
    
    recipes = db.query(Recipe).filter(
        Recipe.id.in_(recipe_ids),
        Recipe.user_id == current_user.id
    ).all()
    
    return [recipe.title for recipe in recipes]