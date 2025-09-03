import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import Navbar from '../components/Navbar';
import { recipeService } from '../services/api';
import { Recipe, RecipeSearchQuery } from '../types';

const Search: React.FC = () => {
  const [searchQuery, setSearchQuery] = useState<RecipeSearchQuery>({
    query: '',
    ingredients: [],
    cuisine_type: '',
    dietary_tags: [],
    min_health_rating: undefined,
    min_taste_rating: undefined,
    max_calories: undefined,
  });
  const [results, setResults] = useState<Recipe[]>([]);
  const [loading, setLoading] = useState(false);
  const [searched, setSearched] = useState(false);
  const [ingredientInput, setIngredientInput] = useState('');
  const [dietaryInput, setDietaryInput] = useState('');

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setSearched(true);

    const queryData: RecipeSearchQuery = {
      ...searchQuery,
      ingredients: ingredientInput ? ingredientInput.split(',').map(i => i.trim()).filter(Boolean) : [],
      dietary_tags: dietaryInput ? dietaryInput.split(',').map(d => d.trim()).filter(Boolean) : [],
    };

    try {
      const data = await recipeService.search(queryData);
      setResults(data);
    } catch (err) {
      console.error('Search failed:', err);
      setResults([]);
    } finally {
      setLoading(false);
    }
  };

  const getHealthColor = (rating?: number) => {
    if (!rating) return 'text-gray-500';
    if (rating >= 7) return 'text-green-600';
    if (rating >= 4) return 'text-yellow-600';
    return 'text-red-600';
  };

  const getRatingStars = (rating?: number) => {
    if (!rating) return '☆☆☆☆☆';
    const filled = '★'.repeat(Math.round(rating));
    const empty = '☆'.repeat(5 - Math.round(rating));
    return filled + empty;
  };

  return (
    <div>
      <Navbar />
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-8">Search Recipes</h1>

        <form onSubmit={handleSearch} className="bg-white p-6 rounded-lg shadow-md mb-8">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
            <div>
              <label htmlFor="query" className="block text-sm font-medium text-gray-700">
                Search Text
              </label>
              <input
                type="text"
                id="query"
                className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-green-500 focus:border-green-500"
                value={searchQuery.query}
                onChange={(e) => setSearchQuery({ ...searchQuery, query: e.target.value })}
                placeholder="Search recipes..."
              />
            </div>

            <div>
              <label htmlFor="ingredients" className="block text-sm font-medium text-gray-700">
                Ingredients
              </label>
              <input
                type="text"
                id="ingredients"
                className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-green-500 focus:border-green-500"
                value={ingredientInput}
                onChange={(e) => setIngredientInput(e.target.value)}
                placeholder="chicken, tomatoes, basil (comma-separated)"
              />
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
            <div>
              <label htmlFor="cuisine" className="block text-sm font-medium text-gray-700">
                Cuisine Type
              </label>
              <input
                type="text"
                id="cuisine"
                className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-green-500 focus:border-green-500"
                value={searchQuery.cuisine_type}
                onChange={(e) => setSearchQuery({ ...searchQuery, cuisine_type: e.target.value })}
                placeholder="Italian, Mexican, etc."
              />
            </div>

            <div>
              <label htmlFor="dietary" className="block text-sm font-medium text-gray-700">
                Dietary Tags
              </label>
              <input
                type="text"
                id="dietary"
                className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-green-500 focus:border-green-500"
                value={dietaryInput}
                onChange={(e) => setDietaryInput(e.target.value)}
                placeholder="vegetarian, gluten-free (comma-separated)"
              />
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
            <div>
              <label htmlFor="health" className="block text-sm font-medium text-gray-700">
                Min Health Rating
              </label>
              <input
                type="number"
                id="health"
                min="1"
                max="10"
                step="0.1"
                className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-green-500 focus:border-green-500"
                value={searchQuery.min_health_rating || ''}
                onChange={(e) => setSearchQuery({ 
                  ...searchQuery, 
                  min_health_rating: e.target.value ? parseFloat(e.target.value) : undefined 
                })}
                placeholder="1-10"
              />
            </div>

            <div>
              <label htmlFor="taste" className="block text-sm font-medium text-gray-700">
                Min Taste Rating
              </label>
              <input
                type="number"
                id="taste"
                min="1"
                max="5"
                step="0.5"
                className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-green-500 focus:border-green-500"
                value={searchQuery.min_taste_rating || ''}
                onChange={(e) => setSearchQuery({ 
                  ...searchQuery, 
                  min_taste_rating: e.target.value ? parseFloat(e.target.value) : undefined 
                })}
                placeholder="1-5"
              />
            </div>

            <div>
              <label htmlFor="calories" className="block text-sm font-medium text-gray-700">
                Max Calories
              </label>
              <input
                type="number"
                id="calories"
                min="0"
                className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-green-500 focus:border-green-500"
                value={searchQuery.max_calories || ''}
                onChange={(e) => setSearchQuery({ 
                  ...searchQuery, 
                  max_calories: e.target.value ? parseFloat(e.target.value) : undefined 
                })}
                placeholder="500"
              />
            </div>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full md:w-auto px-6 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 disabled:opacity-50"
          >
            {loading ? 'Searching...' : 'Search'}
          </button>
        </form>

        {loading && (
          <div className="text-center py-8">
            <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-green-600"></div>
          </div>
        )}

        {searched && !loading && results.length === 0 && (
          <div className="text-center py-8">
            <p className="text-gray-500">No recipes found matching your criteria</p>
          </div>
        )}

        {results.length > 0 && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {results.map((recipe) => (
              <Link
                key={recipe.id}
                to={`/recipes/${recipe.id}`}
                className="bg-white rounded-lg shadow-md hover:shadow-lg transition-shadow p-6"
              >
                <h3 className="text-xl font-semibold mb-2">{recipe.title}</h3>
                
                <div className="space-y-2 text-sm">
                  {recipe.cuisine_type && (
                    <p className="text-gray-600">Cuisine: {recipe.cuisine_type}</p>
                  )}
                  
                  <div className="flex justify-between">
                    <span className="text-gray-600">Calories:</span>
                    <span className="font-medium">{recipe.calories || 'N/A'}</span>
                  </div>
                  
                  <div className="flex justify-between">
                    <span className="text-gray-600">Health Rating:</span>
                    <span className={`font-medium ${getHealthColor(recipe.health_rating)}`}>
                      {recipe.health_rating ? `${recipe.health_rating}/10` : 'N/A'}
                    </span>
                  </div>
                  
                  <div className="flex justify-between">
                    <span className="text-gray-600">Taste:</span>
                    <span className="text-yellow-500">
                      {getRatingStars(recipe.taste_rating)}
                    </span>
                  </div>
                  
                  {recipe.dietary_tags && recipe.dietary_tags.length > 0 && (
                    <div className="flex flex-wrap gap-1 mt-2">
                      {recipe.dietary_tags.map((tag, index) => (
                        <span
                          key={index}
                          className="bg-gray-200 text-gray-700 px-2 py-1 rounded-md text-xs"
                        >
                          {tag}
                        </span>
                      ))}
                    </div>
                  )}
                </div>
              </Link>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default Search;