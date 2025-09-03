export interface User {
  id: number;
  username: string;
  email: string;
  created_at: string;
}

export interface Recipe {
  id: number;
  user_id: number;
  title: string;
  raw_text: string;
  ingredients: Ingredient[];
  instructions: string[];
  calories?: number;
  health_rating?: number;
  health_breakdown?: string;
  taste_rating?: number;
  cuisine_type?: string;
  dietary_tags?: string[];
  prep_time_minutes?: number;
  cook_time_minutes?: number;
  servings?: number;
  nutrition_data?: NutritionData;
  created_at: string;
}

export interface Ingredient {
  name: string;
  quantity?: string;
  unit?: string;
}

export interface NutritionData {
  total: NutritionValues;
  per_serving: NutritionValues;
  servings: number;
  estimated?: boolean;
}

export interface NutritionValues {
  calories?: number;
  protein?: number;
  carbs?: number;
  fat?: number;
  fiber?: number;
  sugar?: number;
  sodium?: number;
}

export interface RecipeCreateRequest {
  title: string;
  raw_text: string;
  cuisine_type?: string;
  dietary_tags?: string[];
  prep_time_minutes?: number;
  cook_time_minutes?: number;
  servings?: number;
}

export interface RecipeSearchQuery {
  query?: string;
  ingredients?: string[];
  cuisine_type?: string;
  dietary_tags?: string[];
  min_health_rating?: number;
  min_taste_rating?: number;
  max_calories?: number;
}