from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile, Form
from sqlalchemy.orm import Session
from typing import List, Optional
import json
import logging

logger = logging.getLogger(__name__)

from app.database import get_db, get_chroma_collection
from app.models.recipe import Recipe
from app.models.user import User
from app.schemas.recipe import RecipeCreate, RecipeResponse, RecipeUpdate
from app.core.security import get_current_user
from app.services.recipe_parser_ai import AIRecipeParser
from app.services.nutrition_ai import AINutritionCalculator
from app.services.health_analyzer_ai import AIHealthAnalyzer
from app.services.url_scraper import URLRecipeScraper
from app.services.ocr_service import OCRService

router = APIRouter()

@router.post("/", response_model=RecipeResponse)
async def create_recipe(
    recipe: RecipeCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Use AI for all analysis
    ai_parser = AIRecipeParser()
    ai_nutrition = AINutritionCalculator()
    ai_health_analyzer = AIHealthAnalyzer()
    
    # Check if input is a URL
    recipe_text = recipe.raw_text.strip()
    url_title = None
    image_url = None
    if recipe_text.startswith(('http://', 'https://', 'www.')):
        # It's a URL, scrape it first
        url_scraper = URLRecipeScraper()
        try:
            scraped_data = url_scraper.scrape_recipe(recipe_text)
            recipe_text = scraped_data['text']
            # Extract title from scraped data if available
            if scraped_data.get('structured_data') and scraped_data['structured_data'].get('title'):
                url_title = scraped_data['structured_data']['title']
            # Extract image URL if available
            image_url = scraped_data.get('image_url')
            logger.info(f"Successfully scraped recipe from URL. Title: {url_title}, Image: {image_url}")
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to fetch recipe from URL: {str(e)}"
            )
    
    try:
        logger.debug(f"Create recipe: preserve_original={recipe.preserve_original}, type={'URL' if recipe_text.startswith(('http://', 'https://')) else 'Text'}")
        
        # Parse recipe with AI (either from URL or direct text)
        parsed = ai_parser.parse_recipe_text(
            recipe_text,
            preserve_original=recipe.preserve_original
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    
    # Calculate nutrition with AI
    nutrition_data = ai_nutrition.calculate_nutrition(
        parsed.ingredients, 
        parsed.servings
    )
    
    calories = nutrition_data['per_serving'].get('calories', 0)
    
    recipe_data = {
        'ingredients': parsed.ingredients,
        'instructions': parsed.instructions,
        'nutrition_data': nutrition_data,
        'servings': parsed.servings
    }
    
    # Get AI health analysis
    ai_health = ai_health_analyzer.analyze_health(recipe_data)
    health_rating = ai_health.get('score', 7)
    health_breakdown = ai_health.get('breakdown', '')
    
    # Use AI-detected tags if user didn't provide them
    final_cuisine = recipe.cuisine_type or parsed.cuisine_type
    final_dietary_tags = recipe.dietary_tags if recipe.dietary_tags else parsed.dietary_tags
    
    # Prioritize URL title, then user-provided title, then AI-parsed title
    final_title = url_title or recipe.title or parsed.title
    
    db_recipe = Recipe(
        user_id=current_user.id,
        title=final_title,
        raw_text=recipe.raw_text,
        ingredients=parsed.ingredients,
        instructions=parsed.instructions,
        calories=calories,
        health_rating=round(health_rating, 1),
        health_breakdown=health_breakdown,
        cuisine_type=final_cuisine,
        dietary_tags=final_dietary_tags,
        prep_time_minutes=recipe.prep_time_minutes,
        cook_time_minutes=recipe.cook_time_minutes,
        servings=parsed.servings,
        nutrition_data=nutrition_data,
        image_url=image_url
    )
    
    db.add(db_recipe)
    db.commit()
    db.refresh(db_recipe)
    
    collection = get_chroma_collection()
    
    metadata = {
        "recipe_id": db_recipe.id,
        "user_id": current_user.id,
        "calories": calories,
        "health_rating": health_rating,
        "cuisine_type": recipe.cuisine_type or "",
        "dietary_tags": json.dumps(recipe.dietary_tags or [])
    }
    
    ingredients_text = " ".join([ing['name'] for ing in parsed.ingredients])
    instructions_text = " ".join(parsed.instructions)
    document = f"{db_recipe.title} {ingredients_text} {instructions_text}"
    
    collection.add(
        documents=[document],
        metadatas=[metadata],
        ids=[f"recipe_{db_recipe.id}"]
    )
    
    return db_recipe

@router.post("/upload-image", response_model=RecipeResponse)
async def create_recipe_from_image(
    file: UploadFile = File(...),
    preserve_original: Optional[str] = Form("false"),
    title: Optional[str] = Form(None),
    cuisine_type: Optional[str] = Form(None),
    dietary_tags: Optional[List[str]] = Form(None),
    prep_time_minutes: Optional[int] = Form(None),
    cook_time_minutes: Optional[int] = Form(None),
    servings: Optional[int] = Form(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a recipe by uploading an image of handwritten recipe or recipe book page
    """
    # Validate file type
    if not file.content_type.startswith('image/'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be an image (JPEG, PNG, etc.)"
        )
    
    # Read image data
    image_data = await file.read()
    
    # Validate image
    ocr_service = OCRService()
    is_valid, message = ocr_service.validate_image(image_data)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message
        )
    
    # Convert string to boolean for preserve_original FIRST
    preserve_original_bool = preserve_original.lower() == "true"
    
    try:
        # Extract text from image using OCR (with preserve_original flag)
        extracted_text = ocr_service.extract_text_from_image(image_data, preserve_original=preserve_original_bool)
        
        if not extracted_text.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Could not extract any text from the image. Please ensure the image contains readable text."
            )
        
        logger.info(f"Extracted {len(extracted_text)} characters from image")
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to process image: {str(e)}"
        )
    
    # Use AI services to parse the extracted text
    ai_parser = AIRecipeParser()
    ai_nutrition = AINutritionCalculator()
    ai_health_analyzer = AIHealthAnalyzer()
    
    logger.debug(f"Upload image: preserve_original={preserve_original_bool}, extracted text length={len(extracted_text)}")
    
    try:
        # Parse recipe with AI (with enhanced prompt for OCR text)
        parsed = ai_parser.parse_recipe_text(
            extracted_text,
            is_ocr_text=True,  # This flag helps the AI know it's dealing with OCR output
            preserve_original=preserve_original_bool
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to parse recipe from image: {str(e)}"
        )
    
    # Calculate nutrition with AI
    nutrition_data = ai_nutrition.calculate_nutrition(
        parsed.ingredients, 
        parsed.servings
    )
    
    calories = nutrition_data['per_serving'].get('calories', 0)
    
    recipe_data = {
        'ingredients': parsed.ingredients,
        'instructions': parsed.instructions,
        'nutrition_data': nutrition_data,
        'servings': parsed.servings
    }
    
    # Get AI health analysis
    ai_health = ai_health_analyzer.analyze_health(recipe_data)
    health_rating = ai_health.get('score', 7)
    health_breakdown = ai_health.get('breakdown', '')
    
    # Use provided metadata or AI-detected values
    final_title = title or parsed.title
    final_cuisine = cuisine_type or parsed.cuisine_type
    final_dietary_tags = dietary_tags if dietary_tags else parsed.dietary_tags
    
    # Create recipe in database
    db_recipe = Recipe(
        user_id=current_user.id,
        title=final_title,
        raw_text=f"[Extracted from image]\n\n{extracted_text}",
        ingredients=parsed.ingredients,
        instructions=parsed.instructions,
        calories=calories,
        health_rating=round(health_rating, 1),
        health_breakdown=health_breakdown,
        cuisine_type=final_cuisine,
        dietary_tags=final_dietary_tags,
        prep_time_minutes=prep_time_minutes,
        cook_time_minutes=cook_time_minutes,
        servings=parsed.servings or servings,
        nutrition_data=nutrition_data
    )
    
    db.add(db_recipe)
    db.commit()
    db.refresh(db_recipe)
    
    # Add to vector database for search
    collection = get_chroma_collection()
    
    metadata = {
        "recipe_id": db_recipe.id,
        "user_id": current_user.id,
        "calories": calories,
        "health_rating": health_rating,
        "cuisine_type": final_cuisine or "",
        "dietary_tags": json.dumps(final_dietary_tags or []),
        "source": "image_upload"
    }
    
    ingredients_text = " ".join([ing['name'] for ing in parsed.ingredients])
    instructions_text = " ".join(parsed.instructions)
    document = f"{db_recipe.title} {ingredients_text} {instructions_text}"
    
    collection.add(
        documents=[document],
        metadatas=[metadata],
        ids=[f"recipe_{db_recipe.id}"]
    )
    
    return db_recipe

@router.get("/{recipe_id}", response_model=RecipeResponse)
async def get_recipe(
    recipe_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    recipe = db.query(Recipe).filter(
        Recipe.id == recipe_id,
        Recipe.user_id == current_user.id
    ).first()
    
    if not recipe:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recipe not found"
        )
    
    return recipe

@router.get("/", response_model=List[RecipeResponse])
async def list_recipes(
    skip: int = 0,
    limit: int = 20,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    recipes = db.query(Recipe).filter(
        Recipe.user_id == current_user.id
    ).offset(skip).limit(limit).all()
    
    return recipes

@router.patch("/{recipe_id}/rating", response_model=RecipeResponse)
async def update_recipe_rating(
    recipe_id: int,
    update: RecipeUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    recipe = db.query(Recipe).filter(
        Recipe.id == recipe_id,
        Recipe.user_id == current_user.id
    ).first()
    
    if not recipe:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recipe not found"
        )
    
    if update.taste_rating is not None:
        recipe.taste_rating = update.taste_rating
    
    db.commit()
    db.refresh(recipe)
    
    collection = get_chroma_collection()
    collection.update(
        ids=[f"recipe_{recipe_id}"],
        metadatas=[{
            "recipe_id": recipe_id,
            "user_id": current_user.id,
            "calories": recipe.calories,
            "health_rating": recipe.health_rating,
            "taste_rating": recipe.taste_rating,
            "cuisine_type": recipe.cuisine_type or "",
            "dietary_tags": json.dumps(recipe.dietary_tags or [])
        }]
    )
    
    return recipe

@router.delete("/{recipe_id}")
async def delete_recipe(
    recipe_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    recipe = db.query(Recipe).filter(
        Recipe.id == recipe_id,
        Recipe.user_id == current_user.id
    ).first()
    
    if not recipe:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recipe not found"
        )
    
    collection = get_chroma_collection()
    collection.delete(ids=[f"recipe_{recipe_id}"])
    
    db.delete(recipe)
    db.commit()
    
    return {"message": "Recipe deleted successfully"}