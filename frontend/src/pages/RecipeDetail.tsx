import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import Navbar from '../components/Navbar';
import { recipeService } from '../services/api';
import { Recipe } from '../types';

const RecipeDetail: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [recipe, setRecipe] = useState<Recipe | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [rating, setRating] = useState(0);
  const [updating, setUpdating] = useState(false);
  const [unitSystem, setUnitSystem] = useState<'US' | 'METRIC'>('US');
  const [servingMultiplier, setServingMultiplier] = useState(1);

  useEffect(() => {
    if (id) {
      fetchRecipe(parseInt(id));
    }
  }, [id]);

  const fetchRecipe = async (recipeId: number) => {
    try {
      const data = await recipeService.getById(recipeId);
      setRecipe(data);
      setRating(data.taste_rating || 0);
    } catch (err) {
      setError('Failed to load recipe');
    } finally {
      setLoading(false);
    }
  };

  const handleRatingUpdate = async (newRating: number) => {
    if (!recipe) return;
    
    setUpdating(true);
    try {
      const updated = await recipeService.updateRating(recipe.id, newRating);
      setRecipe(updated);
      setRating(newRating);
    } catch (err) {
      setError('Failed to update rating');
    } finally {
      setUpdating(false);
    }
  };

  const handleDelete = async () => {
    if (!recipe || !window.confirm('Are you sure you want to delete this recipe?')) return;
    
    try {
      await recipeService.delete(recipe.id);
      navigate('/');
    } catch (err) {
      setError('Failed to delete recipe');
    }
  };

  const getHealthColor = (rating?: number) => {
    if (!rating) return 'text-gray-500';
    if (rating >= 7) return 'text-green-600';
    if (rating >= 4) return 'text-yellow-600';
    return 'text-red-600';
  };

  const convertToMetric = (quantity: string | number | undefined, unit: string | undefined) => {
    if (!quantity || !unit) return { quantity, unit };
    
    const qty = typeof quantity === 'string' ? parseFloat(quantity) : quantity;
    if (isNaN(qty)) return { quantity, unit };

    const lowerUnit = unit.toLowerCase().trim();
    
    // Volume conversions
    if (lowerUnit === 'cup' || lowerUnit === 'cups') {
      return { quantity: (qty * 236.588).toFixed(0), unit: 'ml' };
    }
    if (lowerUnit === 'tablespoon' || lowerUnit === 'tablespoons' || lowerUnit === 'tbsp') {
      return { quantity: (qty * 14.787).toFixed(1), unit: 'ml' };
    }
    if (lowerUnit === 'teaspoon' || lowerUnit === 'teaspoons' || lowerUnit === 'tsp') {
      return { quantity: (qty * 4.929).toFixed(1), unit: 'ml' };
    }
    if (lowerUnit === 'fl oz' || lowerUnit === 'fluid ounce' || lowerUnit === 'fluid ounces') {
      return { quantity: (qty * 29.574).toFixed(0), unit: 'ml' };
    }
    if (lowerUnit === 'quart' || lowerUnit === 'quarts' || lowerUnit === 'qt') {
      return { quantity: (qty * 946.353).toFixed(0), unit: 'ml' };
    }
    if (lowerUnit === 'gallon' || lowerUnit === 'gallons' || lowerUnit === 'gal') {
      return { quantity: (qty * 3785.41).toFixed(0), unit: 'ml' };
    }
    
    // Weight conversions
    if (lowerUnit === 'oz' || lowerUnit === 'ounce' || lowerUnit === 'ounces') {
      return { quantity: (qty * 28.35).toFixed(0), unit: 'g' };
    }
    if (lowerUnit === 'lb' || lowerUnit === 'lbs' || lowerUnit === 'pound' || lowerUnit === 'pounds') {
      const grams = qty * 453.592;
      // If over 1000g, show in kg
      if (grams >= 1000) {
        return { quantity: (grams / 1000).toFixed(2).replace(/\.?0+$/, ''), unit: 'kg' };
      }
      return { quantity: grams.toFixed(0), unit: 'g' };
    }
    
    return { quantity, unit };
  };

  const scaleQuantity = (quantity: string | number | undefined, multiplier: number) => {
    if (!quantity) return quantity;
    
    const qty = typeof quantity === 'string' ? parseFloat(quantity) : quantity;
    if (isNaN(qty)) return quantity;
    
    const scaled = qty * multiplier;
    // Format nicely - whole numbers or up to 2 decimal places
    return scaled % 1 === 0 ? scaled.toString() : scaled.toFixed(2).replace(/\.?0+$/, '');
  };

  const renderHealthBreakdown = (breakdown: string) => {
    const sections = breakdown.split(/### /);
    
    return sections.map((section, index) => {
      if (!section.trim()) return null;
      
      const lines = section.split('\n');
      const title = index > 0 ? lines[0] : null;
      
      // Skip "Missing Components" section
      if (title && title.includes('Missing Components')) {
        return null;
      }
      
      const content = index > 0 ? lines.slice(1).join('\n') : section;
      
      return (
        <div key={index} className={index > 0 ? 'mt-4' : ''}>
          {title && (
            <h3 className="text-lg font-semibold mb-2">
              {title.trim()}
            </h3>
          )}
          <div>
            {content.split('\n').map((line, lineIndex) => {
              const trimmedLine = line.trim();
              if (!trimmedLine) return null;
              
              // Skip markdown table headers and separators
              if (trimmedLine.startsWith('|--') || trimmedLine === '| Ingredient | Health Consideration |') {
                return null;
              }
              
              // Handle markdown table rows (convert to bullet points)
              if (trimmedLine.startsWith('|') && trimmedLine.endsWith('|')) {
                const parts = trimmedLine.split('|').filter(p => p.trim());
                if (parts.length === 2) {
                  const ingredient = parts[0].trim();
                  const concern = parts[1].trim();
                  return (
                    <li key={lineIndex} className="ml-5 list-disc mb-2">
                      <strong>{ingredient}</strong>: {concern}
                    </li>
                  );
                }
              }
              
              // Handle bold text and remove emojis
              let processedLine = trimmedLine;
              
              // Remove emoji characters (most common emoji ranges)
              processedLine = processedLine.replace(/[\u{1F300}-\u{1F9FF}]|[\u{2600}-\u{26FF}]|[\u{2700}-\u{27BF}]|[\u{1F000}-\u{1F02F}]|[\u{1F680}-\u{1F6FF}]|[\u{1F900}-\u{1F9FF}]/gu, '').trim();
              
              // Skip empty lines after emoji removal
              if (!processedLine) return null;
              
              // Check if this line has bold text (likely a health aspect item title)
              const hasBoldText = processedLine.includes('**') && processedLine.startsWith('**');
              
              // For "What Makes It Healthy" section - combine title and next line
              if (hasBoldText && title?.includes('What Makes It Healthy')) {
                // Get the next line if it exists (description)
                const nextLineIndex = lineIndex + 1;
                const nextLine = content.split('\n')[nextLineIndex]?.trim();
                
                if (nextLine && !nextLine.startsWith('**') && !nextLine.startsWith('•')) {
                  // Combine title and description
                  const titleText = processedLine.replace(/\*\*(.*?)\*\*/g, '$1').trim();
                  return (
                    <li key={lineIndex} className="ml-5 list-disc mb-2">
                      <strong>{titleText}</strong>: {nextLine}
                    </li>
                  );
                } else {
                  // Just the title if no description follows
                  processedLine = processedLine.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
                  return (
                    <li key={lineIndex} className="ml-5 list-disc mb-2">
                      <span dangerouslySetInnerHTML={{ __html: processedLine }} />
                    </li>
                  );
                }
              }
              
              // Skip lines that were already processed as descriptions
              if (title?.includes('What Makes It Healthy')) {
                const prevLineIndex = lineIndex - 1;
                const prevLine = content.split('\n')[prevLineIndex]?.trim();
                if (prevLine && prevLine.includes('**') && !processedLine.includes('**')) {
                  return null; // Skip this line as it was already combined with the title
                }
              }
              
              // Replace bold text
              if (processedLine.includes('**')) {
                processedLine = processedLine.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
              }
              
              // Handle bullet points
              if (trimmedLine.startsWith('•') || processedLine.startsWith('•')) {
                const bulletContent = processedLine.startsWith('•') ? processedLine.substring(1).trim() : processedLine;
                return (
                  <li key={lineIndex} className="ml-5 list-disc mb-2">
                    <span dangerouslySetInnerHTML={{ __html: bulletContent }} />
                  </li>
                );
              }
              
              // For other sections with bold text at start (Watch Out For, Tips)
              if (hasBoldText && (title?.includes('Watch Out For') || title?.includes('Tips'))) {
                return (
                  <li key={lineIndex} className="ml-5 list-disc mb-2">
                    <span dangerouslySetInnerHTML={{ __html: processedLine }} />
                  </li>
                );
              }
              
              // Regular paragraph
              return (
                <p key={lineIndex} className="mb-2">
                  <span dangerouslySetInnerHTML={{ __html: processedLine }} />
                </p>
              );
            })}
          </div>
        </div>
      );
    });
  };

  if (loading) {
    return (
      <div>
        <Navbar />
        <div className="flex justify-center items-center h-64">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-green-600"></div>
        </div>
      </div>
    );
  }

  if (!recipe) {
    return (
      <div>
        <Navbar />
        <div className="max-w-4xl mx-auto px-4 py-8">
          <p className="text-red-600">Recipe not found</p>
        </div>
      </div>
    );
  }

  return (
    <div>
      <Navbar />
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {error && (
          <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
            {error}
          </div>
        )}

        <div className="bg-white rounded-lg shadow-md p-6">
          {/* Recipe Image */}
          {recipe.image_url && (
            <div className="mb-6 rounded-lg overflow-hidden">
              <img 
                src={recipe.image_url} 
                alt={recipe.title}
                className="w-full h-96 object-cover rounded-lg shadow-md"
                onError={(e) => {
                  // Hide image if it fails to load
                  (e.target as HTMLImageElement).style.display = 'none';
                }}
              />
            </div>
          )}

          {/* 1. Recipe Name */}
          <div className="flex justify-between items-start mb-6">
            <h1 className="text-3xl font-bold text-gray-900">{recipe.title}</h1>
            <button
              onClick={handleDelete}
              className="bg-red-500 hover:bg-red-600 text-white px-4 py-2 rounded-md text-sm"
            >
              Delete Recipe
            </button>
          </div>

          {/* 2. Calories and Basic Info */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
            <div className="bg-gray-50 p-4 rounded">
              <p className="text-sm text-gray-600">Calories per serving</p>
              <p className="text-2xl font-bold">{recipe.calories || 'N/A'}</p>
            </div>
            <div className="bg-gray-50 p-4 rounded">
              <p className="text-sm text-gray-600">Health Rating</p>
              <p className={`text-2xl font-bold ${getHealthColor(recipe.health_rating)}`}>
                {recipe.health_rating ? `${recipe.health_rating}/10` : 'N/A'}
              </p>
            </div>
            <div className="bg-gray-50 p-4 rounded">
              <p className="text-sm text-gray-600">Servings</p>
              <p className="text-2xl font-bold">{recipe.servings || 4}</p>
            </div>
          </div>

          {/* 3. Your Rating */}
          <div className="mb-6 border-t pt-6">
            <h2 className="text-xl font-semibold mb-2">Your Rating</h2>
            <div className="flex items-center space-x-2">
              {[1, 2, 3, 4, 5].map((star) => (
                <button
                  key={star}
                  onClick={() => handleRatingUpdate(star)}
                  disabled={updating}
                  className={`text-3xl ${
                    star <= rating ? 'text-yellow-500' : 'text-gray-300'
                  } hover:text-yellow-500 disabled:opacity-50`}
                >
                  ★
                </button>
              ))}
              <span className="text-gray-600 ml-2">
                {rating ? `${rating}/5` : 'Not rated'}
              </span>
            </div>
          </div>

          {/* 4. Ingredients */}
          <div className="mb-6 border-t pt-6">
            <div className="bg-gradient-to-br from-green-50 to-emerald-50 p-5 rounded-lg shadow-sm border border-green-100">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-xl font-bold text-green-800 uppercase tracking-wide flex items-center">
                  <span className="text-2xl mr-2">🥗</span> Ingredients
                  {servingMultiplier > 1 && (
                    <span className="ml-2 text-sm font-normal text-green-600">
                      (Scaled for {(recipe.servings || 4) * servingMultiplier} servings)
                    </span>
                  )}
                </h2>
                <div className="flex gap-1">
                  <button 
                    onClick={() => setUnitSystem('US')}
                    className={`px-3 py-1 text-xs rounded-full font-semibold transition-colors ${
                      unitSystem === 'US' 
                        ? 'bg-green-600 text-white hover:bg-green-700' 
                        : 'bg-green-100 text-green-700 hover:bg-green-200'
                    }`}
                  >
                    US
                  </button>
                  <button 
                    onClick={() => setUnitSystem('METRIC')}
                    className={`px-3 py-1 text-xs rounded-full transition-colors ${
                      unitSystem === 'METRIC' 
                        ? 'bg-green-600 text-white hover:bg-green-700' 
                        : 'bg-green-100 text-green-700 hover:bg-green-200'
                    }`}
                  >
                    METRIC
                  </button>
                  <span className="mx-2 text-green-300">|</span>
                  <button 
                    onClick={() => setServingMultiplier(1)}
                    className={`px-3 py-1 text-xs rounded-full font-semibold transition-colors ${
                      servingMultiplier === 1 
                        ? 'bg-green-600 text-white hover:bg-green-700' 
                        : 'bg-green-100 text-green-700 hover:bg-green-200'
                    }`}
                  >
                    1X
                  </button>
                  <button 
                    onClick={() => setServingMultiplier(2)}
                    className={`px-3 py-1 text-xs rounded-full transition-colors ${
                      servingMultiplier === 2 
                        ? 'bg-green-600 text-white hover:bg-green-700' 
                        : 'bg-green-100 text-green-700 hover:bg-green-200'
                    }`}
                  >
                    2X
                  </button>
                  <button 
                    onClick={() => setServingMultiplier(3)}
                    className={`px-3 py-1 text-xs rounded-full transition-colors ${
                      servingMultiplier === 3 
                        ? 'bg-green-600 text-white hover:bg-green-700' 
                        : 'bg-green-100 text-green-700 hover:bg-green-200'
                    }`}
                  >
                    3X
                  </button>
                </div>
              </div>
              <div className="space-y-2">
                {recipe.ingredients.map((ingredient, index) => {
                  let displayQuantity = scaleQuantity(ingredient.quantity, servingMultiplier);
                  let displayUnit = ingredient.unit;
                  
                  if (unitSystem === 'METRIC' && displayQuantity && displayUnit) {
                    const converted = convertToMetric(displayQuantity, displayUnit);
                    displayQuantity = converted.quantity;
                    displayUnit = converted.unit;
                  }
                  
                  return (
                    <label key={index} className="flex items-start cursor-pointer hover:bg-green-100/50 p-3 rounded-lg transition-all hover:shadow-sm">
                      <input 
                        type="checkbox" 
                        className="mt-1 mr-3 h-5 w-5 text-green-600 border-green-300 rounded focus:ring-green-500 focus:ring-2"
                      />
                      <div className="flex-1">
                        <span className="text-gray-700">
                          {displayQuantity && (
                            <span className="font-bold text-green-700">{displayQuantity} </span>
                          )}
                          {displayUnit && (
                            <span className="text-green-600 font-medium">{displayUnit} </span>
                          )}
                          <span className="text-gray-800 font-medium">{ingredient.name}</span>
                        </span>
                      </div>
                    </label>
                  );
                })}
              </div>
            </div>
          </div>

          {/* 5. Instructions */}
          <div className="mb-6 border-t pt-6">
            <div className="bg-gradient-to-br from-green-50 to-emerald-50 p-5 rounded-lg shadow-sm border border-green-100">
              <h2 className="text-xl font-bold text-green-800 uppercase tracking-wide mb-5 flex items-center">
                <span className="text-2xl mr-2">👩‍🍳</span> Instructions
              </h2>
              <div className="space-y-4">
                {recipe.instructions.map((instruction, index) => (
                  <div key={index} className="flex group hover:bg-green-100/30 p-3 rounded-lg transition-all">
                    <div className="flex-shrink-0 w-10 h-10 bg-gradient-to-br from-green-500 to-emerald-500 text-white rounded-full flex items-center justify-center font-bold text-sm mr-4 shadow-md group-hover:shadow-lg transition-shadow">
                      {index + 1}
                    </div>
                    <p className="text-gray-700 leading-relaxed pt-2 font-medium">{instruction}</p>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Additional Info */}
          {recipe.cuisine_type && (
            <div className="mb-6 border-t pt-6">
              <p className="mb-2">
                <span className="font-semibold">Cuisine:</span> {recipe.cuisine_type}
              </p>
            </div>
          )}

          {recipe.dietary_tags && recipe.dietary_tags.length > 0 && (
            <div className="mb-6">
              <span className="font-semibold">Dietary Tags:</span>
              <div className="flex flex-wrap gap-2 mt-2">
                {recipe.dietary_tags.map((tag, index) => (
                  <span
                    key={index}
                    className="bg-green-100 text-green-800 px-3 py-1 rounded-full text-sm"
                  >
                    {tag}
                  </span>
                ))}
              </div>
            </div>
          )}

          {recipe.prep_time_minutes && recipe.cook_time_minutes && (
            <div className="flex space-x-6 text-sm text-gray-600 mb-6">
              <p>
                <span className="font-semibold">Prep Time:</span> {recipe.prep_time_minutes} minutes
              </p>
              <p>
                <span className="font-semibold">Cook Time:</span> {recipe.cook_time_minutes} minutes
              </p>
              <p>
                <span className="font-semibold">Total Time:</span>{' '}
                {recipe.prep_time_minutes + recipe.cook_time_minutes} minutes
              </p>
            </div>
          )}

          {/* 6. Nutrition Information */}
          {recipe.nutrition_data && (
            <div className="mb-6 border-t pt-6">
              <div className="bg-gradient-to-br from-green-50 to-emerald-50 p-5 rounded-lg shadow-sm border border-green-100">
                <h2 className="text-xl font-bold text-green-800 uppercase tracking-wide mb-4 flex items-center">
                  <span className="text-2xl mr-2">📊</span> Nutrition Information
                </h2>
                <p className="font-semibold text-green-700 mb-3">Per Serving:</p>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  {Object.entries(recipe.nutrition_data.per_serving).map(([key, value]) => (
                    <div key={key} className="bg-white/60 p-3 rounded-lg border border-green-100">
                      <p className="text-sm text-gray-600 capitalize">{key}</p>
                      <p className="font-bold text-green-700 text-lg">
                        {value}{key === 'calories' ? '' : key === 'sodium' ? 'mg' : 'g'}
                      </p>
                    </div>
                  ))}
                </div>
                {recipe.nutrition_data.estimated && (
                  <p className="text-sm text-gray-500 mt-3 italic">* Estimated values</p>
                )}
              </div>
            </div>
          )}

          {/* 7. Health Analysis - Last */}
          {recipe.health_breakdown && (
            <div className="border-t pt-6">
              <div className="bg-gradient-to-br from-green-50 to-emerald-50 p-5 rounded-lg shadow-sm border border-green-100">
                <h2 className="text-xl font-bold text-green-800 uppercase tracking-wide mb-4 flex items-center">
                  <span className="text-2xl mr-2">💚</span> Health Analysis
                </h2>
                <div className="text-gray-700">
                  {renderHealthBreakdown(recipe.health_breakdown)}
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default RecipeDetail;